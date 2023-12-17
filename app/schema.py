from .config import RadioChannelConfig
from .rtlsdr_airband.schema import RtlSdrAirbandChannel

from typing import Optional
from dataclasses import dataclass
from enum import Enum

# class ModulationType(Enum):
#     frequency = "fm"
#     amplitude = "am"


# @dataclass
# class RadioChannelMode:
#     name: str
#     modulation: ModulationType
#     bandwidth: Optional[int] = None


# @dataclass
# class RadioChannel:
#     freq: float
#     mode: RadioChannelMode

#     ctcss: Optional[float] = None
#     config: Optional[RadioChannelConfig] = None


    # rsab_channel: Optional[RtlSdrAirbandChannel] = None
    # udp_port: Optional[int] = None
