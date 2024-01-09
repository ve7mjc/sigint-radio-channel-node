from app.radio.schema import RadioChannelRecord

from dataclasses import dataclass, field
from typing import Optional

#
## Radio System Data
#

@dataclass
class RadioSystemChannel:
    id: str
    freq: str

    label: Optional[str] = None
    comment: Optional[str] = None
    description: Optional[str] = None
    designator: Optional[str] = None

@dataclass
class RadioSystem:
    id: str
    name: str

    description: Optional[str] = None

    default_designator: Optional[str] = None

    channels: list[RadioSystemChannel] = field(default_factory=list)

