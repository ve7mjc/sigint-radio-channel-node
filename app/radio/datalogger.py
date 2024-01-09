"""
We will have a DataLogger class instance in each channel

There will be one or more different "streams" that must be written to disk

"""
from .schema import SessionFrame, RadioChannelEvent

from typing import Optional, Union
from datetime import datetime
from asyncio import Queue
import asyncio
import copy
import os
import logging

import numpy as np
from numpy import ndarray

from scipy.io import wavfile


logger = logging.getLogger(__name__)


# Produce disk-copies of a channel at a particular point in processing/filtering
# to perform post-mortem, etc.
class StreamLogger:

    write_path: str
    sample_rate: int
    frames: Queue[SessionFrame]
    num_samples: int
    num_frames: int
    name: str
    _variant: str
    timestamp: datetime

    def __init__(self, sample_rate: int, write_path: str, name: str, variant: str = ""):
        self.sample_rate = sample_rate
        self.write_path = write_path
        self.name = name
        self._variant = variant

        self.frames = Queue()
        self.num_samples = 0
        self.num_frames = 0

    def add_frame(self, frame: SessionFrame):
        self.num_samples += frame.samples.size
        self.num_frames += 1
        # create deep copy of frame
        self.frames.put_nowait(copy.deepcopy(frame))

    def start(self, timestamp: datetime):
        self.timestamp = timestamp

    async def write(self, path: str, filename: str):

        # Copy samples before sending off to async task
        index = 0
        samples = np.zeros(self.num_samples, np.float32)
        while not self.frames.empty():
            frame = self.frames.get_nowait()
            next_index = index + frame.samples.size
            samples[index:next_index] = frame.samples
            index = next_index

        # reflect our clearing
        self.num_samples = 0
        self.num_frames = 0

        try:
            self.write_wav(os.path.join(path,filename), samples)
            logger.debug(f"wrote stream [{self.variant}]: {filename}")
        except Exception as e:
            logger.error(f"error writing wav: {e}")


    def write_wav(self, filename: str, samples: ndarray):

        # convert to PCM S16 LE (s16l)
        pcm_data = np.int16(samples * 32767.)

        out_path = os.path.join(self.write_path, filename)
        wavfile.write(out_path, self.sample_rate, pcm_data)


    @property
    def variant(self) -> str:
        if self._variant:
            return f"_{self._variant}"
        return ""

# multiple different streams and manifest
class ChannelDataLogger:

    channel_id: str
    data_store: str
    sample_rate: float

    streams: list[StreamLogger]
    start_time: Union[datetime, None]

    # filename pattern: {channel.id}_{YYYYMMDDTHHMMSS.ZZZ}.wav

    def __init__(self, channel_id: str, data_store: str, sample_rate: float):
        self.channel_id = channel_id
        self.data_store = data_store
        self.sample_rate = sample_rate

        self.streams = []
        self.start_time = None

    def add_stream(self, variant: Optional[str] = None) -> StreamLogger:
        stream = StreamLogger(
            sample_rate=self.sample_rate,
            write_path=self.data_store,
            name=self.channel_id,
            variant=variant
        )
        self.streams.append(stream)
        return stream

    def start_event(self, start_time: datetime):
        self.start_time = start_time
        for stream in self.streams:
            stream.start(start_time)

    def finish_event(self):
        asyncio.create_task(self._do_writes(self.start_time))

    def build_manifest(self, start_time: datetime):
        pass
        # manifest = RadioChannelEvent(
        #     time_start=start_time.isoformat(),

        # )

    # create required number of async tasks
    # pass start_time now as we cannot guarantee lifetime
    async def _do_writes(self, start_time: datetime):

        # write streams
        for stream in self.streams:

            # Build Filename
            timestring = start_time.strftime('%Y%m%dT%H%M%S')
            filename = f"{self.channel_id}_{timestring}{stream.variant}.wav"

            await stream.write(self.data_store, filename)

        # write manifest
        logger.info(f"done writes for {self.channel_id}")
