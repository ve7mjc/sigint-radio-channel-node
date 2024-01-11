from .designators import Designator, decode_emissions_designator

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import os
import sys

from numpy import ndarray


@dataclass
class GeoJSONPoint:
    type: str
    coordinates: list[float]  # longitude, latitude, [height]

    def __init__(self, longitude: float, latitude: float, height: float = None):
        self.type = "Point"
        self.coordinates = [longitude, latitude]
        if height is not None:
            self.coordinates.append(height)


@dataclass
class RadioChannelRecord:
    channel_id: str
    freq: float

    label: str

    designator: [str] = None
    ctcss: Optional[float] = None


@dataclass
class RadioSensor:
    geolocation: GeoJSONPoint
    antenna_agl: float
    # estimated losses from antenna to frontend?

# the overall radio event -- perhaps we also track the trigger? eg. what prompted us to consider it a start? a stop?
@dataclass
class RadioChannelEvent:

    # per SigMF, an ISO-8601 string indicating the timestamp of the sample index specified by sample_start.
    time_start: datetime

    channel: RadioChannelRecord

    datatype: str
    sample_rate: int

    sample_count: int

    # A short form human/machine-readable label for the annotation.
    # label: str
    # Human-readable name of the entity that created this annotation.
    # generator: str
    # A human-readable comment
    # comment: str


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
    start_time: float

    _active: bool

    def __init__(self, id: int, time_start: Optional[float] = None):
        self.id = id
        self.start_time = time_start or datetime.now()

        self._active = True

    @property
    def active(self) -> bool:
        return not self._active

    def set_finished(self):
        self._active = False


