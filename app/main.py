
from .config import get_config
from .rtlsdr_airband.configuration import (
    ConfigGenerator,
    RtlSdrAirbandDevice,
    RtlSdrAirbandChannel
)
from .rtlsdr_airband.literals import DEFAULT_SAMPLE_RATE
from .literals import DEFAULT_UDP_PORT_BASE, DEFAULT_UDP_LISTEN_ADDR
from .schema import VoiceChannel
from .udp_adapter import UdpStreamProcessor

import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from pprint import pprint

#
# Configure Logging
#

logger = logging.getLogger()

logs_path = os.environ.get("LOGS_PATH", "./logs")
if not os.path.exists(logs_path):
    os.mkdir(logs_path)

log_file = os.path.join(logs_path, 'main.log')

# 5 MB per file, keep 5 old copies
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=1024 * 1024 * 5,
    backupCount=5
)

console_handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# set levels
logger.setLevel(logging.DEBUG)
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

# squelch library loggers
logging.getLogger('asyncio').setLevel(logging.WARNING)


# build RTLSDR-Airband configuration from intent

## default to applying all of the channels to one device right now


async def main():

    udp_listen_address = DEFAULT_UDP_LISTEN_ADDR

    config = get_config()

    generator = ConfigGenerator()

    voice_channels: list[VoiceChannel] = []

    last_listen_port: int = DEFAULT_UDP_PORT_BASE

    for device in config.devices:
        generator.add_device(
            RtlSdrAirbandDevice(
                type=device.type,
                gain=device.gain
            )
        )

    for channel_config in config.channels:
        rsab_channel = RtlSdrAirbandChannel(
            freq=channel_config.freq,
            modulation="nfm",
            id=channel_config.id,
            name=channel_config.label,
            ctcss=channel_config.ctcss
        )
        last_listen_port += 1
        udp_port = last_listen_port

        rsab_channel.add_output_udp_stream(udp_listen_address, udp_port)
        channel = VoiceChannel(channel_config, rsab_channel, udp_port)
        voice_channels.append(channel)
        generator.add_channel(rsab_channel)


    generator.generate("test_output.conf")

    #
    # We have passed the configuration of RTLSDR-Airband
    #

    listeners: list[UdpStreamProcessor] = []

    channel: VoiceChannel
    for channel in voice_channels:

        stream_processor = UdpStreamProcessor(channel.config.id, udp_listen_address, channel.udp_port)
        stream_processor.set_data_path(config.data_store)
        if channel.config.ctcss:
            stream_processor.set_ctcss(channel.config.ctcss)
        if channel.config.label:
            stream_processor.set_label(channel.config.label)
        listeners.append(stream_processor)

        # Mumble config
        if config.mumble and channel.config.mumble.enabled:
            stream_processor.add_mumble_output(config.mumble.remote_host,
                                               config.mumble.remote_port,
                                               channel=channel.config.mumble.channel)

    tasks = [listener.start_listener() for listener in listeners]
    await asyncio.gather(*tasks)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped manually")
