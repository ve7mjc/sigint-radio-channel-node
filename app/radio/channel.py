from .designators import Designator, decode_emissions_designator
from app.common.utils import from_dict
from .schema import RadioChannelRecord

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
import asyncio
from asyncio import Queue
import os
import logging
import copy

import numpy as np
from numpy import ndarray
from scipy.io import wavfile
import yaml


logger = logging.getLogger(__name__)


class RadioChannel:

    frequency: float

    ctcss: Optional[float]

    designator: Optional[Designator]

    def __init__(self, frequency: float):
        self.frequency = frequency
        self.ctcss = None
        self.designator = None

    def set_ctcss(self, value: float):
        self.ctcss = value

    def set_emissions_designator(self, code: str):
        self.designator = decode_emissions_designator(code)


# we pass samples into this class and then flag it as ended
class RadioChannelSession:

    id: int
    timestamp_start: float

    _active: bool

    def __init__(self, id: int, time_start: Optional[float] = None):
        self.id = id
        self.timestamp_start = time_start or datetime.now()

        self._active = True

    @property
    def active(self) -> bool:
        return not self._active

    def set_finished(self):
        self._active = False


class SessionFrame:

    session_id: int
    samples: ndarray
    sample_rate: int

    def __init__(self, session_id: int, fs: int, samples: ndarray):
        self.session_id = session_id
        self.sample_rate = fs
        self.samples = samples

    @property
    def num_samples(self) -> int:
        return len(self.samples)


def load_channels(yaml_file: str) -> list[RadioChannelRecord]:

    with open(yaml_file, "r") as file:
        d = yaml.safe_load(file)

    channels: list[RadioChannelRecord] = []
    for chd in d['channels']:
        print(chd)
        c = from_dict(RadioChannelRecord, chd)
        channels.append(c)

    return channels


# Produce disk-copies of a channel at a particular point in processing/filtering
# to perform post-mortem, etc.
class StreamLogger:

    write_path: str
    sample_rate: int
    frames: Queue[SessionFrame]
    num_samples: int
    num_frames: int
    name: str
    variant: str
    timestamp: datetime

    def __init__(self, sample_rate: int, write_path: str, name: str, variant: str = ""):
        self.sample_rate = sample_rate
        self.write_path = write_path
        self.name = name
        self.variant = variant

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

    def write(self):

        # Copy samples before sending off to async task
        index = 0
        samples = np.zeros(self.num_samples, np.float32)
        while not self.frames.empty():
            frame = self.frames.get_nowait()
            next_index = index + frame.samples.size
            samples[index:next_index] = frame.samples
            index = next_index

        # Build Filename
        variant = self.variant
        if variant:
            variant = f"_{self.variant}"
        timestring = self.timestamp.strftime('%Y%m%dT%H%M%S')
        filename = f"{self.name}_{timestring}{variant}.wav"

        # reflect our clearing
        self.num_samples = 0
        self.num_frames = 0

        asyncio.create_task(self.write_wav(filename, samples))

    async def write_wav(self, filename: str, samples: ndarray):

        # convert to PCM S16 LE (s16l)
        pcm_data = np.int16(samples * 32767.)

        out_path = os.path.join(self.write_path, filename)
        wavfile.write(out_path, self.sample_rate, pcm_data)

        logger.debug(f"wrote stream [{self.variant}]: {filename}")
