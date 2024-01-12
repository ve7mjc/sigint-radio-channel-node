from .rtlsdr_airband.literals import DEFAULT_STREAM_TIMEOUT_SECS
# from .dsp.filters import iir_notch, iir_highpass
from .dsp.filters import StreamingFilter, FilterType


from .literals import (
    DEFAULT_MINIMUM_VOICE_ACTIVE_SECS,
    SAMPLE_SECS_PER_FRAME
)
from .mumble.channel import MumbleChannel
from app.config import RadioChannelConfig
# from app.radio.channel import RadioChannel, RadioChannelSession, Frame, StreamLogger

from app.radio.schema import RadioChannel, RadioChannelSession
from app.dsp.disk_writer import StreamDiskWriter, ChannelDiskWriter
from app.dsp.frame import Frame
from app.dsp.schema import DiskWriterConfig

# experiment to test if we are getting jitter from the 8,000 byte frames..
# 8k/4 = 2k samples
BUFFER_FRAMES_NUM: int = 15

import os
import asyncio
import logging
from typing import Callable, Union, Optional
from queue import Queue
import struct

import numpy as np


logger = logging.getLogger(__name__)


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


class RadioChannelProcessor:

    config: RadioChannelConfig

    channel: RadioChannel

    id: str
    listen_addr: str
    listen_port: int

    sample_rate: int

    # Channel specific
    data_store: Optional[str]

    # receive_buffer: bytearray
    frames: Queue[Frame]

    # Filters
    filters_notch: list[StreamingFilter]
    filter_highpass: StreamingFilter
    filter_lowpass: StreamingFilter

    # Move this all to the Mumble channel class
    mumble_outputs: list[MumbleChannel]
    mumble_tasks: list
    mumble_buffering: bool

    # Session
    last_session_id: int
    sessions: list[RadioChannelSession]
    active_session: Union[RadioChannelSession, None]

    # DataLoggers
    disk_writer: Optional[ChannelDiskWriter] = None
    # stream_logger_raw: StreamDiskWriter
    # stream_logger: StreamDiskWriter

    output_gain: float

    def __init__(
            self,
            config: RadioChannelConfig,
            listen_addr: str,
            listen_port: int,
            sample_rate: int = 16000,
            disk_writer_config: Optional[DiskWriterConfig] = None
        ):

        self.config = config

        # set from config
        self.id = config.id

        # determine radio channel mode
        self.channel = RadioChannel(
            config.freq,
            ctcss=config.ctcss,
            designator=config.designator
        )

        if config.designator:
            self.channel.set_emissions_designator(config.designator)

        self.frames = Queue()

        self.last_session_id = 0
        self.sessions = []
        self.active_session = None
        self.disk_writer = None

        # Data Storage `common_data_store/id`
        # self.data_store = disk_writer_config.base_path or os.getcwd()
        # self.data_store = os.path.join(self.data_store, self.id)
        # if not os.path.exists(self.data_store):
        #     os.makedirs(self.data_store, exist_ok=True)

        if config.label:
            self.set_label(config.label)
        self.label = config.label

        self.listen_addr = listen_addr
        self.listen_port = listen_port

        self.sample_rate = sample_rate

        self.time_stream_started = None

        # Filters
        self.filters_notch = []
        self.filter_highpass = StreamingFilter(FilterType.HIGHPASS,
                                               sampling_freq=self.sample_rate,
                                               order=40, freq=275)

        self.filter_lowpass = StreamingFilter(FilterType.LOWPASS,
                                              sampling_freq=self.sample_rate,
                                              order=40, freq=3500)

        self.mumble_outputs = []
        self.mumble_tasks = []
        self.mumble_buffering = False

        if disk_writer_config:
            self.disk_writer = ChannelDiskWriter(
                channel_id=self.id,
                data_store=disk_writer_config.base_path,
                sample_rate=self.sample_rate,
                minimum_record_secs=disk_writer_config.minimum_length_secs
            )

        # default of unity gain on output
        self.output_gain = 1.

        if self.channel.designator.modulation_type == 'F':
            if self.channel.designator.bandwidth == 16000:
                self.output_gain = 1.5
            elif self.channel.designator.bandwidth >= 11000 and self.channel.designator.bandwidth < 12000:
                self.output_gain = 2

    def add_disk_writer(self, config: DiskWriterConfig, id: Optional[str] = None) -> None:
        if self.disk_writer is None:
            raise Exception("disk writer is not configured!")

        # we have initialized a ChannelDataLogger with
        # default data_store, and sample_rate already
        self.disk_writer.add_stream_writer(id)
        # self.stream_logger_raw = self.datalogger.add_stream("raw")

    def add_mumble_output(self, remote_host: str, remote_port: int,
                          certs_store: Optional[str] = None, **kwargs):
        if self.id is None:
            logger.error("channel does not have a valid id!")

        passed_args = {}
        passed_args['cert_cn'] = self.id
        if "channel" in kwargs:
            passed_args['channel'] = kwargs.get('channel')
        mumble_channel = MumbleChannel(remote_host, remote_port, self.label,
                                       certs_store=certs_store, **passed_args)
        self.mumble_outputs.append(mumble_channel)

    def set_label(self, value: str):
        self.label = value

    def _start_stream(self):

        self.last_session_id += 1
        session = RadioChannelSession(self.last_session_id)
        self.active_session = session
        self.sessions.append(session)

        logger.debug(f"channel id={self.id} PTT stream udp/{self.listen_port}"
                     f" started; session_id = {self.active_session.id}")

        self.disk_writer.start_event(session.start_time)

    def _stop_stream(self):

        if self.active_session is None:
            logger.warning("trying to stop a stream where no stream exists!")

        if self.active_session:
            self.active_session.set_finished()
            self.active_session = None

        # null_tail = count_trailing_zeros(self.receive_buffer)
        # print(f"null_tail = {null_tail:,}/{len(self.receive_buffer):,} ({round((null_tail/len(self.receive_buffer))*100,1)})")

        # check if we meet our minimums
        # min_voice_secs = DEFAULT_MINIMUM_VOICE_ACTIVE_SECS
        # duration_voice = len(self.receive_buffer) / 4. / self.sample_rate

        # if duration_voice < min_voice_secs:
        #     logger.info(f"ignoring ptt event of {round(duration_voice*1000,1)} msec")

        # else:
        #     logger.debug(f"{self.label} - PTT ended; [{round(duration_voice, 2)} sec]")
        #     samples = np.frombuffer(self.receive_buffer.copy(), dtype=np.float32)

        self.disk_writer.finish_event()

        # Clear the buffer and reset the start time
        # self.receive_buffer.clear()
        self.start_time = None

    def _on_data(self, data, addr):
        """
        assuming incoming data type is 32-bit floats
        this method is being called by the datagram receiver so do not block
        """

        if not self.active_session:
            self._start_stream()

        # only if we are expecting an 8k block from RTLSDR-Airband UDP_OUTPUT
        if len(data) != 8000:
            logger.warning(f"received datagarm of size {len(data):,} bytes")

        # self.receive_buffer.extend(data)

        # There is no turning back with this Exception!
        if len(data) % 4 != 0:
            raise ValueError("The length of byte_array is not a multiple of 4")

        # Build, populate, and enqueue a frame
        unpacked_data = struct.unpack(f'<{len(data) // 4}f', data)
        frame = Frame(self.active_session.id, self.sample_rate,
                             np.array(unpacked_data, dtype=np.float32))
        self.frames.put_nowait(frame)

        self._process_samples()


    def _reset_filters(self):

        for filter_notch in self.filters_notch:
            filter_notch.reset()

        if self.filter_highpass:
            self.filter_highpass.reset()

        if self.filter_lowpass:
            self.filter_lowpass.reset()


    def _process_samples(self):
        """
        Attempt processing on arrival of new data
        """
        samples_per_frame = int(SAMPLE_SECS_PER_FRAME * 16000)  # match incoming sample rate to outgoing

        # # if we are buffering
        # if self.mumble_buffering and self.samples.qsize() < (BUFFER_FRAMES_NUM * samples_per_frame):
        #     return

        # # disable buffering
        # self.mumble_buffering = False

        # what happens if we have incorrect amount of data in a larger frame?
        # 8000k / 4 = 2000 samples (32-bit float @ 16kHz)
        # if we decide to work in a different frame size (eg. 160, what happens)
        # 12.5 frames per master frame -- eg. we will need to "put some back"
        # we have not addressed frame padding yet!


        while self.frames.qsize() > 0:

            frame = self.frames.get()

            # disabling raw logger for now
            # self.stream_logger_raw.add_frame(frame)

            # apply filter stages
            frame.samples = self.filter_highpass.filter(frame.samples)
            frame.samples = self.filter_lowpass.filter(frame.samples)

            if self.disk_writer is not None:
                self.disk_writer.add_frame(frame)

            # level normalization / fixed gain
            frame.samples = frame.samples * self.output_gain

            # forward samples to respective mumble outputs
            for mumble_output in self.mumble_outputs:
                mumble_output.add_frame(frame)

    def _on_done(self):
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
                for mumble_task in self.mumble_tasks:
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
