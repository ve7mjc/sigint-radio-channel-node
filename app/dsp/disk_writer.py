"""
We will have a DataLogger class instance in each channel

There will be one or more different "streams" that must be written to disk

## 10 Jan 2024 -- adding:
  - folder path checks per write
  - date-based path

"""
from .frame import Frame

from typing import Optional, Union
from datetime import datetime
from asyncio import Queue
import asyncio
import copy
import os
import logging
from enum import Enum

import numpy as np
from numpy import ndarray

from scipy.io import wavfile


logger = logging.getLogger(__name__)


class StreamFormat(Enum):
    WAV_PCM_16LE = "wav.pcm_16le"


# Produce disk-copies of a channel at a particular point in processing/filtering
# to perform post-mortem, etc.
class StreamDiskWriter:

    write_path: str
    sampling_rate: int
    frames: Queue[Frame]
    num_samples: int
    num_frames: int
    _id: str
    timestamp: datetime
    format: StreamFormat

    def __init__(self, id: str, sample_rate: int, write_path: str,
                 format: StreamFormat = StreamFormat.WAV_PCM_16LE):

        self.sampling_rate = sample_rate
        self.write_path = write_path
        self._id = id
        self.format = format

        self.frames = Queue()
        self.num_samples = 0
        self.num_frames = 0

    def add_frame(self, frame: Frame):
        self.num_samples += frame.samples.size
        self.num_frames += 1
        # create deep copy of frame
        self.frames.put_nowait(copy.deepcopy(frame))
        # logger.debug(f"added {frame.samples.size} frames; total = {self.num_frames}")

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
        wavfile.write(out_path, self.sampling_rate, pcm_data)

    @property
    def stream_length_secs(self) -> float:
        return self.num_samples / self.sampling_rate

    @property
    def variant(self) -> str:
        if self._id:
            return f"_{self._id}"
        return ""

# multiple different streams and manifest
class ChannelDiskWriter:

    channel_id: str
    data_store: str
    sample_rate: float

    writers: dict[str, StreamDiskWriter]
    start_time: Union[datetime, None]

    minimum_record_secs: float

    # filename pattern: {channel.id}_{YYYYMMDDTHHMMSS.ZZZ}.wav

    def __init__(self, channel_id: str, data_store: str,
                 sample_rate: float, minimum_record_secs: float):
        self.channel_id = channel_id
        self.data_store = data_store
        self.sample_rate = sample_rate
        self.minimum_record_secs = minimum_record_secs

        self.writers = {}
        self.start_time = None

    def add_stream_writer(self, id: Optional[str] = None) -> StreamDiskWriter:

        stream = StreamDiskWriter(
            sample_rate=self.sample_rate,
            write_path=self.data_store,
            id=id
        )

        self.writers[id] = stream
        return stream

    def add_frame(self, frame:
        Frame, writer_id: Optional[str] = None):

        if not writer_id in self.writers:
            raise ValueError(f"disk_writer '{writer_id}' does not exist!")

        self.writers[writer_id].add_frame(frame)

    def start_event(self, start_time: datetime):
        self.start_time = start_time
        for writer in self.writers.values():
            writer.start(start_time)

    def finish_event(self):
        asyncio.create_task(self._do_writes(self.start_time))

    def build_manifest(self, start_time: datetime):
        pass


    # create required number of async tasks
    # pass start_time now as we cannot guarantee lifetime
    async def _do_writes(self, start_time: datetime):

        # write streams
        stream: StreamDiskWriter
        for stream in self.writers.values():

            # determine if length of samples meets minimum for writing
            if stream.stream_length_secs < self.minimum_record_secs:
                logger.info(f"stream of {round(stream.stream_length_secs, 1)} secs ignored")
                continue

            # Build filename
            timestring = start_time.strftime('%Y%m%dT%H%M%S')
            filename = f"{self.channel_id}_{timestring}{stream.variant}.wav"

            folder_path = os.path.join(
                self.data_store,
                str(start_time.year),
                str(start_time.month),
                str(start_time.day)
            )

            # check/create path
            try:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                logger.error(f"exception ({type(e)}): {e}")
                continue

            # folder path, eg. data_store/2024/03/10/
            await stream.write(folder_path, filename)

        # write manifest
        logger.info(f"done writes for {self.channel_id}")
