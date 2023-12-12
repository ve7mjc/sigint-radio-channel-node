from .config import RadioVoiceChannelConfig
from .rtlsdr_airband.schema import RtlSdrAirbandChannel

from typing import Optional
from dataclasses import dataclass


@dataclass
class VoiceChannel:
    config: RadioVoiceChannelConfig
    rsab_channel: RtlSdrAirbandChannel
    udp_port: Optional[int] = None
