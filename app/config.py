# project libs
from .utils import from_dict
from .literals import (
    DEFAULT_CONFIG_FILE, DEFAULT_UDP_LISTEN_ADDR,
    DEFAULT_DATA_STORE_PATH, DEFAULT_UDP_PORT_BASE
)

# system libs
from typing import Optional
from dataclasses import dataclass, field

# third-party/ext libs
import yaml


@dataclass
class SdrDeviceConfig:
    type: str
    device_string: Optional[str] = None
    serial: Optional[str] = None
    gain: Optional[float] = None
    correction: Optional[float] = None
    center_freq: Optional[float] = None
    rtlsdr_airband_overrides: list[str] = field(default=list)


@dataclass
class MumbleChannelConfig:
    enabled: bool = field(default=True)
    channel: Optional[str] = None


@dataclass
class RadioChannelConfig:
    freq: float

    id: Optional[str] = None
    mode: Optional[str] = None
    designator: Optional[str] = None

    label: Optional[str] = None
    ctcss: Optional[float] = None

    udp_port: Optional[int] = None

    mumble: Optional[MumbleChannelConfig] = None

    rtlsdr_airband_overrides: list[str] = field(default_factory=list)

    def generate_id(self, force: bool = False):
        if self.id and not force:
            return
        self.id = f"{self.mode}_{self.freq:.3f}".replace(".","")


@dataclass
class MumbleConfig:
    remote_host: str
    remote_port: int
    default_channel: Optional[str] = None


@dataclass
class AppConfig:
    config_file: str
    mumble: Optional[MumbleConfig] = None
    config_out_filename: Optional[str] = None
    rtlsdr_airband_global_overrides: list[str] = field(default_factory=list)

    listen_address: str = DEFAULT_UDP_LISTEN_ADDR
    listen_port_base: int = DEFAULT_UDP_PORT_BASE

    data_store_path: Optional[str] = DEFAULT_DATA_STORE_PATH
    devices: list[SdrDeviceConfig] = field(default_factory=list)
    channels: list[RadioChannelConfig] = field(default_factory=list)


# global config instance
_config: Optional[AppConfig] = None


def load_yaml_config(filename: str = DEFAULT_CONFIG_FILE) -> AppConfig:

    with open(filename, "r") as f:
        d = yaml.safe_load(f)

    # insert config filename
    d['config_file'] = filename

    config: AppConfig = from_dict(AppConfig, d)
    return config


def get_config(filename: str):
    global _config
    if _config:
        return _config

    _config = load_yaml_config(filename)

    return _config