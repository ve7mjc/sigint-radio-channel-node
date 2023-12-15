# project libs
from .utils import from_dict
from .literals import DEFAULT_CONFIG_FILE

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
    overrides: list[str] = field(default=list)


@dataclass
class MumbleChannelConfig:
    enabled: bool = field(default=True)
    channel: Optional[str] = None


@dataclass
class RadioVoiceChannelConfig:
    id: str
    freq: float
    mumble: MumbleChannelConfig
    mode: Optional[str] = "nfm"
    label: Optional[str] = None
    ctcss: Optional[float] = None
    udp_port: Optional[int] = None
    overrides: list[str] = field(default_factory=list)


@dataclass
class MumbleConfig:
    remote_host: str
    remote_port: int


@dataclass
class AppConfig:
    data_store: str
    mumble: MumbleConfig
    config_out_filename: Optional[str] = None
    global_tau: Optional[int] = None
    global_overrides: list[str] = field(default_factory=list)
    devices: list[SdrDeviceConfig] = field(default_factory=list)
    channels: list[RadioVoiceChannelConfig] = field(default_factory=list)


# global config instance
_config: Optional[AppConfig] = None


def load_yaml_config(filename: str = DEFAULT_CONFIG_FILE) -> AppConfig:

    with open(filename, "r") as f:
        d = yaml.safe_load(f)

    config: AppConfig = from_dict(AppConfig, d)
    return config


def get_config(filename: str):
    global _config
    if _config:
        return _config

    _config = load_yaml_config(filename)

    return _config