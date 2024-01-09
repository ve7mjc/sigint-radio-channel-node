# project libs
from app.common.utils import from_dict
from .literals import (
    DEFAULT_CONFIG_FILE, DEFAULT_UDP_LISTEN_ADDR,
    DEFAULT_DATA_STORE_PATH, DEFAULT_UDP_PORT_BASE
)

# system libs
from typing import Optional, Union
from dataclasses import dataclass, field
import os

# third-party/ext libs
import yaml


class ConfigurationException(Exception):
    pass


@dataclass
class SdrDeviceConfig:
    type: str
    device_string: Optional[str] = None
    serial: Optional[str] = None
    gain: Optional[float] = None
    correction: Optional[float] = None
    center_freq: Optional[float] = None
    rtlsdr_airband_overrides: list[str] = field(default=list)
    sample_rate: Optional[int] = None
    mode: Optional[str] = "multichannel"


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
class SensorConfig:
    geolocation: Optional[list[float]] = None


@dataclass
class AppConfig:
    config_file: str
    mumble: Optional[MumbleConfig] = None
    config_out_filename: Optional[str] = None
    rtlsdr_airband_global_overrides: list[str] = field(default_factory=list)

    listen_address: str = DEFAULT_UDP_LISTEN_ADDR
    listen_port_base: int = DEFAULT_UDP_PORT_BASE

    data_path: Optional[str] = DEFAULT_DATA_STORE_PATH
    cache_path: Optional[str] = None
    devices: list[SdrDeviceConfig] = field(default_factory=list)
    channels: list[RadioChannelConfig] = field(default_factory=list)

    sensor: Optional[SensorConfig] = None


class ConfigManager:

    config_dict: dict
    config: Union[AppConfig, None]

    def __init__(self):
        self.config_dict = {}
        self.config = None

    def add_yaml(self, filename: str):

        with open(filename, "r") as f:
            d = yaml.safe_load(f)

        # insert config filename
        d['config_file'] = filename

        self.config_dict = {**self.config_dict, **d}

    def process_config(self) -> AppConfig:

        config: AppConfig = from_dict(AppConfig, self.config_dict)

        # build paths
        if not config.cache_path:
            config.cache_path = os.path.join(config.data_path, "cache/")

        self.config = config
        return config
