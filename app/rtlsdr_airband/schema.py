from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RtlSdrAirbandChannelOutputBase:
    type: str


@dataclass
class RtlSdrAirbandChannel:
    id: str
    name: str
    freq: float
    modulation: str
    outputs: list[dict] = field(default_factory=list)
    ctcss: Optional[float] = None

    def add_output_udp_stream(self, dest_address: str, dest_port: int):
        output = { "type": "\"udp_stream\"" }
        output['dest_address'] = f"\"{dest_address}\""
        output['dest_port'] = dest_port
        output['continuous'] = "false"
        self.outputs.append(output)


@dataclass
class RtlSdrAirbandDevice:
    type: str
    index: int = 0
    gain: Optional[float] = None
    correction: Optional[float] = None
    centerfreq: Optional[float] = None
    channels: list[RtlSdrAirbandChannel] = field(default_factory=list)


@dataclass
class RtlSdrAirbandConfig:
    devices: list[RtlSdrAirbandDevice] = field(default_factory=list)
