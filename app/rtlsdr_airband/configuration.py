from .schema import (
    RtlSdrAirbandChannel, RtlSdrAirbandConfig,
    RtlSdrAirbandDevice
)
from .literals import RTLSDR_MAX_BANDWIDTH

import os
from statistics import median

# third-party libs
from jinja2 import Environment, FileSystemLoader


RTLSDR_AIRBAND_CONF_TEMPLATE: str = "rtlsdr_airband_config.tpl"
template_dir = os.path.dirname(os.path.abspath(__file__))
config_template_file = os.path.join(template_dir, RTLSDR_AIRBAND_CONF_TEMPLATE)


class ConfigGenerator:

    devices: list[RtlSdrAirbandDevice]

    def __init__(self):
        self.devices = []

    def add_device(self, device: RtlSdrAirbandDevice):
        self.devices.append(device)

    def add_channel(self, channel: RtlSdrAirbandDevice):
        self.devices[0].channels.append(channel)

    def generate(self, filename: str) -> str:

        airband_config = RtlSdrAirbandConfig(
            devices=self.devices
        )

        # calculate center frequency
        freqs: list[float] = []
        for ch in self.devices[0].channels:
            freqs.append(ch.freq)

        freq_min = min(freqs)
        freq_max = max(freqs)
        if (freq_max - freq_min) > RTLSDR_MAX_BANDWIDTH:
            raise Exception("Channel frequencies span > bandwidth!")

        airband_config.devices[0].centerfreq = median(freqs)

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


