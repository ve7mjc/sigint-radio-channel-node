from .rtlsdr_airband.literals import DEFAULT_STREAM_TIMEOUT_SECS
from .dsp.filters import iir_notch, iir_highpass
from .dsp.radio_filters import remove_ctcss
from .literals import DEFAULT_MINIMUM_VOICE_ACTIVE_SECS
from .mumble.channel import MumbleChannel

import os
import asyncio
import socket
import logging
from typing import Callable, Union, Optional
from datetime import datetime


import numpy as np
from numpy import ndarray
import resampy
from scipy.io import wavfile


logger = logging.getLogger(__name__)

# squelch resampy logging
logging.getLogger('numba.core.ssa').setLevel(logging.CRITICAL)
logging.getLogger('numba.core.interpreter').setLevel(logging.CRITICAL)
logging.getLogger('numba.core.byteflow').setLevel(logging.CRITICAL)


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

class UdpStreamProcessor:

    id: str
    listen_addr: str
    listen_port: int
    sample_rate_in: float
    stream_active: bool
    time_stream_started: Union[datetime, None]
    ctcss_freq: Optional[float]

    data_output_path: str

    receive_buffer: bytearray

    mumble_outputs: list[MumbleChannel]
    mumble_tasks: list

    def __init__(self, id: str, listen_addr: str, listen_port: int, sample_rate_in: float = 16000):
        self.id = id
        self.label = id
        self.listen_addr = listen_addr
        self.listen_port = listen_port
        self.sample_rate_in = sample_rate_in
        self.stream_active = False
        self.time_stream_started = None

        self.data_output_path = os.getcwd()
        self.ctcss_freq = None

        self.receive_buffer = bytearray()

        self.mumble_outputs = []
        self.mumble_tasks = []

        logger.debug(f"{self.__class__.__name__}({listen_addr}, {listen_port}, {sample_rate_in})")

    def add_mumble_output(self, remote_host: str, remote_port: int, **kwargs):
        passed_args = {}
        if "channel" in kwargs:
            passed_args['channel'] = kwargs.get('channel')
        mumble_channel = MumbleChannel(remote_host, remote_port, self.label, **passed_args)
        self.mumble_outputs.append(mumble_channel)

    def set_label(self, value: str):
        self.label = value

    def set_data_path(self, data_path: str):
        self.data_output_path = data_path

    def set_ctcss(self, freq: float):
        logger.debug(f"channel '{self.id}' enabling ctcss = {freq} Hz")
        self.ctcss_freq = freq

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
        logger.debug(f"voice ptt duration: {round(duration_voice, 2)}")
        if duration_voice < min_voice_secs:
            logger.info(f"ignoring ptt event of {round(duration_voice*1000,1)} msec")

        else:
            samples = np.frombuffer(self.receive_buffer.copy(), dtype=np.float32)

            # Write to WAV file
            self._write_samples(samples, self.sample_rate_in)

            # remove ctcss if specified
            if self.ctcss_freq:
                samples = remove_ctcss(samples, self.sample_rate_in, self.ctcss_freq)
                self._write_samples(samples, self.sample_rate_in, "ctcss_removed")

            # apply 300 Hz high-pass
            samples = iir_highpass(samples, self.sample_rate_in, 300)
            self._write_samples(samples, self.sample_rate_in, "highpass")

            # add to mumble if enabled
            for mumble_output in self.mumble_outputs:
                logger.debug("writing data to mumble channel!")
                resampled_array = resampy.resample(samples, 16000, 48000)
                pcm_data = np.int16(resampled_array * 32767 * 2).tobytes()  # also multiply by 5.0/2.5 KHz
                mumble_output.add_samples(pcm_data)

        # Clear the buffer and reset the start time
        self.receive_buffer.clear()
        self.stream_active = False
        self.start_time = None


    def _on_data(self, data, addr):
        if not self.stream_active:
            logger.debug(f"channel id={self.id} PTT stream udp/{self.listen_port} started")
            self._start_stream()

        self.receive_buffer.extend(data)

    def _on_done(self):
        logger.debug(f"channel id={self.id} PTT stream udp/{self.listen_port} stopped")
        self._stop_stream()


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
