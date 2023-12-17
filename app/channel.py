from .rtlsdr_airband.literals import DEFAULT_STREAM_TIMEOUT_SECS
from .dsp.filters import iir_notch, iir_highpass
from .dsp.radio_filters import remove_ctcss
from .literals import DEFAULT_MINIMUM_VOICE_ACTIVE_SECS, SAMPLE_SECS_PER_FRAME
from .mumble.channel import MumbleChannel
from app.config import RadioChannelConfig
from app.radio.channel import RadioChannel

# experiment to test if we are getting jitter from the 8,000 byte frames..
# 8k/4 = 2k samples
BUFFER_FRAMES_NUM: int = 15

import os
import asyncio
# import socket
import logging
from typing import Callable, Union, Optional
from datetime import datetime
from queue import Queue
import struct
from dataclasses import dataclass

import numpy as np
from numpy import ndarray
import resampy
from scipy.io import wavfile
from scipy.signal import butter, lfilter, lfilter_zi, iirnotch
from scipy.signal.windows import hann

from samplerate import Resampler

logger = logging.getLogger(__name__)

# squelch resampy logging
logging.getLogger('numba.core.ssa').setLevel(logging.CRITICAL)
logging.getLogger('numba.core.interpreter').setLevel(logging.CRITICAL)
logging.getLogger('numba.core.byteflow').setLevel(logging.CRITICAL)


# RTLSDR-Airband samples -> 16,000/sec
# Mumble sample_rate -> 48,000/sec



class PttVoiceDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_data: Callable, on_done: Callable,
                 timeout: float = DEFAULT_STREAM_TIMEOUT_SECS):
        self.on_data = on_data
        self.on_done = on_done
        self.timeout = timeout

        self.transport = None
        self.timeout_handle = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.on_data(data, addr)

        # Reset the timeout timer
        if self.timeout_handle:
            self.timeout_handle.cancel()
        self.timeout_handle = asyncio.get_event_loop().call_later(
            self.timeout, self.timeout_reached)

    def timeout_reached(self):
        self.on_done()

    def error_received(self, exc):
        logger.error(f'Error received: {exc}')

    def connection_lost(self, exc):
        logger.error('Connection closed')


def count_trailing_zeros(byte_array):
    count = 0
    for byte in reversed(byte_array):
        if byte == 0x00:
            count += 1
        else:
            break
    return count


@dataclass
class FilterState:
    b: ndarray
    a: ndarray
    zi: Optional[ndarray] = None


class RadioChannelProcessor:

    config: RadioChannelConfig

    channel: RadioChannel

    id: str
    listen_addr: str
    listen_port: int

    sample_rate_in: int

    stream_active: bool
    time_stream_started: Union[datetime, None]

    data_output_path: str

    receive_buffer: bytearray
    samples: Queue[float]

    mumble_outputs: list[MumbleChannel]
    mumble_tasks: list
    mumble_buffering: bool
    mumble_debug_samples: bool
    mumble_samples: Queue[int]

    filter_states: dict[FilterState]

    mumble_resampler: Resampler

    output_gain: float

    def __init__(self, config: RadioChannelConfig, listen_addr: str, listen_port: int,
                 sample_rate_in: int = 16000):

        self.config = config

        # set from config
        self.id = config.id

        # determine radio channel mode
        self.channel = RadioChannel(config.freq)
        if config.designator:
            self.channel.set_emissions_designator(config.designator)

        # if config.ctcss:
        #     self.set_ctcss(config.ctcss)
        if config.label:
            self.set_label(config.label)
        self.label = config.label

        self.listen_addr = listen_addr
        self.listen_port = listen_port

        self.sample_rate_in = sample_rate_in

        self.stream_active = False
        self.time_stream_started = None

        self.data_output_path = os.getcwd()

        self.receive_buffer = bytearray()

        self.mumble_outputs = []
        self.mumble_buffering = True
        self.mumble_tasks = []
        self.mumble_samples = Queue()
        converter = 'sinc_best'
        self.mumble_resampler = Resampler(converter, channels=1)

        # write samples to disk for analysis
        self.mumble_debug_samples = True

        self.samples = Queue()
        self.filter_states = {}

        # default of unity gain on output
        self.output_gain = 1.

        # logger.debug(f"{self.__class__.__name__}({listen_addr}, {listen_port}, {sample_rate_in})")


    def add_mumble_output(self, remote_host: str, remote_port: int, **kwargs):

        # configure filters for first output only
        if len(self.mumble_outputs) == 0:

            nyquist = 0.5 * self.sample_rate_in

            # Notch out CTCSS if present
            if self.channel.ctcss:
                logger.debug(f"adding notch filter for ctcss freq = {self.channel.ctcss}")
                bandwidth_hz = 20
                q = self.channel.ctcss / bandwidth_hz
                # self.ctcss_freq / (self.sample_rate_in / 2)
                b, a = iirnotch(self.channel.ctcss, q, self.sample_rate_in)
                self.filter_states['mumble_notch_ctcss'] = FilterState(b=b,a=a)

            # Highpass
            cutoff_frequency = 250
            order: int = 5
            # normal_cutoff = cutoff_frequency / nyquist
            b, a = butter(order, cutoff_frequency, btype='highpass', fs=self.sample_rate_in)
            self.filter_states['mumble_high_pass'] = FilterState(b=b, a=a)

            # Lowpass
            cutoff_frequency = 3500
            order: int = 5
            # normal_cutoff = cutoff_frequency / nyquist
            b, a = butter(order, cutoff_frequency, btype='lowpass', fs=self.sample_rate_in)
            self.filter_states['mumble_low_pass'] = FilterState(b=b, a=a)

            # Final Lowpass (Temp, following resample)
            cutoff_frequency = 3500
            order: int = 5
            # normal_cutoff = cutoff_frequency / nyquist
            b, a = butter(order, cutoff_frequency, btype='lowpass', fs=48000)
            self.filter_states['mumble_final_highpass'] = FilterState(b=b, a=a)


        passed_args = {}
        if "channel" in kwargs:
            passed_args['channel'] = kwargs.get('channel')
        mumble_channel = MumbleChannel(remote_host, remote_port, self.label, **passed_args)
        self.mumble_outputs.append(mumble_channel)

    def set_label(self, value: str):
        self.label = value

    def set_data_path(self, data_path: str):
        self.data_output_path = data_path

    # def set_ctcss(self, freq: float):
    #     logger.debug(f"channel '{self.id}' enabling ctcss = {freq} Hz")
    #     self.ctcss_freq = freq

    def _start_stream(self):

        self.time_stream_started = datetime.now()
        self.stream_active = True

    def _write_samples(self, samples: ndarray, sample_rate: float, variant: str = ""):
        if variant:
            variant = f"_{variant}"

        # convert to PCM S16 LE (s16l)
        # normalized_data = np.interp(filtered_data, (filtered_data.min(), filtered_data.max()), (-1, 1))
        pcm_data = np.int16(samples * 32767 * 2)  # also multiply by 5.0/2.5 KHz

        timestring = self.time_stream_started.strftime('%Y%m%dT%H%M%S')
        outf = f"{self.id}_{timestring}{variant}.wav"
        out_path = os.path.join(self.data_output_path, outf)
        wavfile.write(out_path, sample_rate, pcm_data)
        # logger.debug(f"wrote samples [{variant}]: {out_path}")

    def _stop_stream(self):

        null_tail = count_trailing_zeros(self.receive_buffer)
        # print(f"null_tail = {null_tail:,}/{len(self.receive_buffer):,} ({round((null_tail/len(self.receive_buffer))*100,1)})")

        # check if we meet our minimums
        min_voice_secs = DEFAULT_MINIMUM_VOICE_ACTIVE_SECS
        duration_voice = len(self.receive_buffer) / 4. / self.sample_rate_in

        if duration_voice < min_voice_secs:
            logger.info(f"ignoring ptt event of {round(duration_voice*1000,1)} msec")

        else:
            logger.debug(f"{self.label} - PTT ended; [{round(duration_voice, 2)} sec]")
            samples = np.frombuffer(self.receive_buffer.copy(), dtype=np.float32)

            # Write to WAV file
            self._write_samples(samples, self.sample_rate_in)

            # remove ctcss if specified
            if self.channel.ctcss:
                samples = remove_ctcss(samples, self.sample_rate_in, self.channel.ctcss)
                self._write_samples(samples, self.sample_rate_in, "ctcss_removed")

            # apply 300 Hz high-pass
            samples = iir_highpass(samples, self.sample_rate_in, 300)
            self._write_samples(samples, self.sample_rate_in, "highpass")


        # Clear the buffer and reset the start time
        self.receive_buffer.clear()
        self.stream_active = False
        self.start_time = None


    def _on_data(self, data, addr):
        if not self.stream_active:
            logger.debug(f"channel id={self.id} PTT stream udp/{self.listen_port} started")
            self._start_stream()

        self.receive_buffer.extend(data)

        ## direct to mumble
        if len(self.mumble_outputs):
            if len(data) % 4 != 0:
                raise ValueError("The length of byte_array is not a multiple of 4")

            format_string = f'<{len(data) // 4}f'  # e.g., '<10f' for 10 floats
            for sample in list(struct.unpack(format_string, data)):
                self.samples.put(sample)

            self._process_samples()

            # print(f"{self.samples.qsize()} in the queue..")

        # for mumble_output in self.mumble_outputs:
        #     resampled_array = resampy.resample(samples, 16000, 48000)
        #     pcm_data = np.int16(resampled_array * 32767 * 2).tobytes()  # also multiply by 5.0/2.5 KHz
        #     mumble_output.add_samples(pcm_data)


    def _process_samples(self):
        """
        Attempt processing on arrival of new data
        """
        samples_per_frame = int(SAMPLE_SECS_PER_FRAME * 16000)  # match incoming sample rate to outgoing

        # if we are buffering
        if self.mumble_buffering and self.samples.qsize() < (BUFFER_FRAMES_NUM * samples_per_frame):
            return

        # disable buffering
        self.mumble_buffering = False

        while self.samples.qsize() >= samples_per_frame:

            # build a frame
            elements = np.empty(samples_per_frame, dtype=np.float32)
            for i in range(samples_per_frame):
                elements[i] = self.samples.get()
            # elements = np.float32([self.samples.get() for _ in range(samples_per_frame)])

            # Notch CTCSS if present
            if self.channel.ctcss:
                fst: FilterState = self.filter_states['mumble_notch_ctcss']
                if fst.zi is None:
                    fst.zi = np.zeros(max(len(fst.a), len(fst.b)) - 1)
                elements, fst.zi = lfilter(fst.b, fst.a, elements, zi=fst.zi)

            # High-Pass Filter
            fst: FilterState = self.filter_states['mumble_high_pass']
            if fst.zi is None:
                fst.zi = np.zeros(max(len(fst.a), len(fst.b)) - 1)
            elements, fst.zi = lfilter(fst.b, fst.a, elements, zi=fst.zi)

            # Low-Pass Filter
            fst: FilterState = self.filter_states['mumble_low_pass']
            if fst.zi is None:
                fst.zi = np.zeros(max(len(fst.a), len(fst.b)) - 1)
            elements, fst.zi = lfilter(fst.b, fst.a, elements, zi=fst.zi)

            # resample from RTLSDR-Airband 16kHz to Mumble 48kHz
            ratio = 3
            resampled = self.mumble_resampler.process(elements, ratio)
            # resampled_array = resampy.resample(elements, 16000, 48000)

            # Final Low-Pass Filter
            # fst: FilterState = self.filter_states['mumble_final_highpass']
            # if fst.zi is None:
            #     fst.zi = np.zeros(max(len(fst.a), len(fst.b)) - 1)
            # resampled, fst.zi = lfilter(fst.b, fst.a, resampled, zi=fst.zi)

            pcm_data = np.int16(resampled * 32767 * self.output_gain)

            # store samples for DiskWriting
            if self.mumble_debug_samples:
                for sample in pcm_data:
                    self.mumble_samples.put(sample)

            # forward samples to respective mumble outputs
            for mumble_output in self.mumble_outputs:
                mumble_output.add_samples(pcm_data.tobytes())


    def _on_done(self):

        self._stop_stream()

        # reset Mumble filters
        self.mumble_resampler.reset()
        for fstate in self.filter_states.values():
            fstate.zi = None

        # reset mumble buffering
        self.mumble_buffering = True

        # write samples to disk if requested to do so for
        # mumble stream debugging
        if self.mumble_debug_samples:
            timestring = self.time_stream_started.strftime('%Y%m%dT%H%M%S')
            wav_filename = f"mumble_{self.id}_{timestring}.wav"
            wav_path = os.path.join(self.data_output_path, wav_filename)
            samples = np.empty(self.mumble_samples.qsize(), dtype=np.int16)
            for i in range(self.mumble_samples.qsize()):
                samples[i] = self.mumble_samples.get()
            wavfile.write(wav_path, 48000, samples)


    async def start_listener(self):

        loop = asyncio.get_running_loop()

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: PttVoiceDatagramProtocol(self._on_data, self._on_done),
            local_addr=(self.listen_addr, self.listen_port)
        )

        logger.info(f"{self.__class__.__name__} id={self.id}; listening on udp/{self.listen_port}")

        # Create and start the concurrent task
        for mumble_channel in self.mumble_outputs:
            mumble_task = asyncio.create_task(mumble_channel.start(), name="Mumble Task")
            self.mumble_tasks.append(mumble_task)

        try:
            # Wait indefinitely; replace with appropriate condition if needed
            await asyncio.Future()
        finally:
            for mumble_channel in self.mumble_outputs:
                mumble_channel.stop()
            try:
                # Wait for the task to be cancelled
                for mumble_TASK in self.mumble_tasks:
                    await mumble_task
            except asyncio.CancelledError:
                # Handle the cancellation (if any specific handling is required)
                pass




# Async function to handle incoming UDP data
# async def handle_udp(reader, writer):
    # data = await reader.read(BUFFER_SIZE)
    # floats = np.frombuffer(data, dtype=np.float32)

    # # Apply the notch filter
    # filtered_data = lfilter(b, a, floats)

    # # Write to WAV file
    # write("output.wav", SAMPLE_RATE, filtered_data.astype(np.float32))

    ## 16-bit signed PCM
    ## Assuming filtered_data is your data in float32 format
    # normalized_data = np.interp(filtered_data, (filtered_data.min(), filtered_data.max()), (-1, 1))
    # pcm_data = np.int16(normalized_data * 32767)
    # write("output.wav", SAMPLE_RATE, pcm_data)
