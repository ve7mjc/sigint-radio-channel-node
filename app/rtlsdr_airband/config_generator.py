from .schema import (
    RtlSdrAirbandChannel, RtlSdrAirbandConfig,
    RtlSdrAirbandDevice
)
from app.radio.channel import RadioChannel
from .literals import RTLSDR_MAX_BANDWIDTH
from app.utils import channel_closest_center, bandwidth_required

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

    config: RtlSdrAirbandConfig

    def __init__(self, global_overrides: list[str] = []):
        self.config = RtlSdrAirbandConfig(overrides=global_overrides)

    def set_id(self, value: str):
        self.config.id = value

    def add_device(self, device: RtlSdrAirbandDevice):
        self.config.devices.append(device)

    def add_channel(self, channel: RadioChannel,
                    overrides: list[str] = []) -> RtlSdrAirbandChannel:

        if channel.designator is None:
            raise ValueError("unable to configure RTLSDR-Airband channel without designator!")

        # todo: set additional based on designator modulation:
        # - bandwidth
        # - audio gain
        # - agc?
        # - filters?
        rtlsdr_modulation: Optional[str] = None
        if channel.designator.modulation_type == "A":
            rtlsdr_modulation = 'am'
        elif channel.designator.modulation_type == "F":
            rtlsdr_modulation = 'fm'

        ch = RtlSdrAirbandChannel(
            freq=channel.frequency,
            modulation=rtlsdr_modulation,
            ctcss=channel.ctcss,
            overrides=overrides
        )

        logger.debug(f"adding channel to config: {ch}")
        self.config.devices[0].channels.append(ch)

        return ch

    def generate(self, filename: str) -> RtlSdrAirbandConfig:

        if len(self.config.devices[0].channels) == 0:
            raise Exception("no channels configured!")

        freqs: list[float] = []
        for ch in self.config.devices[0].channels:
            freqs.append(ch.freq)


        logger.debug(f"freqs = {freqs}")

        #
        # Determine appropriate center frequency
        if self.config.devices[0].centerfreq:
            center_channel = self.config.devices[0].centerfreq
            logger.info(f"using center freq of {center_channel} from config")
        else:
            center_channel = channel_closest_center(freqs)
            self.config.devices[0].centerfreq = center_channel
            logger.info(f"using center freq of {center_channel} from {freqs}")

        #
        # Required bandwidth

        bandwidth = bandwidth_required(freqs, 16000)
        bandwidth_mhz = round(bandwidth / 1e6, 3)
        logger.info(f"required bandwidth: {bandwidth_mhz:,} MHz")

        if bandwidth > RTLSDR_MAX_BANDWIDTH:
            raise Exception(f"Channel span bandwidth exceeded! {bandwidth_mhz:,} MHz")

        config_data = self.config.__dict__

        if not os.path.exists(config_template_file):
            raise FileNotFoundError("cannot find template '%s'",
                                    RTLSDR_AIRBAND_CONF_TEMPLATE)

        env = Environment(loader=FileSystemLoader(template_dir),
                        trim_blocks=True, lstrip_blocks=True)
        template = env.get_template(RTLSDR_AIRBAND_CONF_TEMPLATE)

        output = template.render(config_data)

        with open(filename, 'w') as f:
            f.write(output)

        return self.config

