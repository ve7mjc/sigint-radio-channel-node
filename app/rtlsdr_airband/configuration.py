from .schema import (
    RtlSdrAirbandChannel, RtlSdrAirbandConfig,
    RtlSdrAirbandDevice
)
from .literals import RTLSDR_MAX_BANDWIDTH

import os
from statistics import median
from typing import Optional
import logging
from math import ceil

# third-party libs
from jinja2 import Environment, FileSystemLoader


RTLSDR_AIRBAND_CONF_TEMPLATE: str = "rtlsdr_airband_config.tpl"
template_dir = os.path.dirname(os.path.abspath(__file__))
config_template_file = os.path.join(template_dir, RTLSDR_AIRBAND_CONF_TEMPLATE)

logger = logging.getLogger(__name__)


class ConfigGenerator:

    devices: list[RtlSdrAirbandDevice]

    global_tau: Optional[int]
    global_overrides: list[str]

    def __init__(self):
        self.devices = []
        self.global_overrides = []
        self.global_tau = None

    def add_device(self, device: RtlSdrAirbandDevice):
        self.devices.append(device)

    def add_channel(self, channel: RtlSdrAirbandDevice):
        self.devices[0].channels.append(channel)

    def add_global_overrides(self, overrides: list[str]):
        self.global_overrides.extend(overrides)

    def set_global_tau(self, value: int):
        self.global_tau = value

    def generate(self, filename: str) -> str:

        airband_config = RtlSdrAirbandConfig(
            devices=self.devices,
            global_tau=self.global_tau,
            global_overrides=self.global_overrides
        )

        # calculate center frequency
        freqs: list[float] = []
        for ch in self.devices[0].channels:
            freqs.append(ch.freq)

        if len(freqs) <= 2:
            center_freq = freqs[0]
        else:
            center_freq = median(freqs)
        airband_config.devices[0].centerfreq = center_freq

        logger.info(
            f"using center freq of {airband_config.devices[0].centerfreq} "
            f"from freqs: {freqs}"
        )

        # determine required bandwidth
        # frequencies are float mhz
        freq_min = int(min(freqs) * 1e6)
        freq_max = int(max(freqs) * 1e6)
        span_string = (
            f"min: {min(freqs):.3f} MHz; max: {max(freqs):.3f} MHz; "
            f"span: {freq_max-freq_min:,} Hz"
        )
        channel_width = int(16e3)  # estimated for now
        bandwidth_required_hz = (freq_max - freq_min) + channel_width
        if bandwidth_required_hz > RTLSDR_MAX_BANDWIDTH:
            raise Exception(f"Channels span > bandwidth! {span_string}")

        logger.info(f"required bandwidth: {bandwidth_required_hz:,} Hz")

        # Global tau
        # if self.global_tau:
        #     airband_config.global_tau = self.global_tau

        config_data = airband_config.__dict__

        # print("\n\n")
        # print(config_data)

        if not os.path.exists(config_template_file):
            raise FileNotFoundError("cannot find template '%s'",
                                    RTLSDR_AIRBAND_CONF_TEMPLATE)

        env = Environment(loader=FileSystemLoader(template_dir),
                        trim_blocks=True, lstrip_blocks=True)
        template = env.get_template(RTLSDR_AIRBAND_CONF_TEMPLATE)

        output = template.render(config_data)

        with open(filename, 'w') as f:
            f.write(output)

        return output


