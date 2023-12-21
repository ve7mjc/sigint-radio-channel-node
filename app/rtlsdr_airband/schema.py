from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RtlSdrAirbandChannelOutputBase:
    type: str


# class attributes should match language of rtl_airband config
# file where possible
@dataclass
class RtlSdrAirbandChannel:

    freq: float
    modulation: str
    outputs: list[dict] = field(default_factory=list)
    ctcss: Optional[float] = None

    # special
    overrides: list[str] = field(default_factory=list)

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
    device_string: Optional[str] = None
    serial: Optional[str] = None
    gain: Optional[float] = None
    correction: Optional[float] = None
    centerfreq: Optional[float] = None
    channels: list[RtlSdrAirbandChannel] = field(default_factory=list)
    sample_rate: Optional[float] = None

    # special
    overrides: list[str] = field(default_factory=list)


@dataclass
class RtlSdrAirbandConfig:

    id: Optional[str] = None
    devices: list[RtlSdrAirbandDevice] = field(default_factory=list)

    # special
    global_overrides: list[str] = field(default_factory=list)
