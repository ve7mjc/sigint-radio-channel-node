
from .config import get_config
from .rtlsdr_airband.configuration import (
    ConfigGenerator,
    RtlSdrAirbandDevice,
    RtlSdrAirbandChannel
)
from .rtlsdr_airband.literals import DEFAULT_SAMPLE_RATE
from .literals import (
    DEFAULT_UDP_PORT_BASE,
    DEFAULT_UDP_LISTEN_ADDR,
    DEFAULT_CONFIG_FILE
)
from .schema import VoiceChannel
from .udp_adapter import UdpStreamProcessor
from .rtlsdr_airband.rtl_airband import RtlSdrAirbandInstance
from .utils import filename_from_path

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import argparse
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

    tasks = []

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Configuration file', required=False)
    args = parser.parse_args()

    udp_listen_address = DEFAULT_UDP_LISTEN_ADDR

    config_file = DEFAULT_CONFIG_FILE

    if args.config:
        config_file = args.config

    try:
        config = get_config(config_file)
    except FileNotFoundError:
        logger.error(f"config file '{config_file}' not found!")
        sys.exit(1)

    generator = ConfigGenerator()

    voice_channels: list[VoiceChannel] = []

    last_listen_port: int = DEFAULT_UDP_PORT_BASE

    for device_cfg in config.devices:
        device = RtlSdrAirbandDevice(
            type=device_cfg.type,
            serial=device_cfg.serial,
            device_string=device_cfg.device_string,
            gain=device_cfg.gain,
            correction=device_cfg.correction
        )
        generator.add_device(device)

    for channel_config in config.channels:
        rsab_channel = RtlSdrAirbandChannel(
            freq=channel_config.freq,
            modulation=channel_config.mode,
            id=channel_config.id,
            name=channel_config.label,
            ctcss=channel_config.ctcss,
            overrides=channel_config.overrides
        )

        if not channel_config.udp_port:
            last_listen_port += 1
            udp_port = last_listen_port
        else:
            udp_port = channel_config.udp_port

        rsab_channel.add_output_udp_stream(udp_listen_address, udp_port)
        channel = VoiceChannel(channel_config, rsab_channel, udp_port)
        voice_channels.append(channel)
        generator.add_channel(rsab_channel)

    # Generate rtl_airband config
    config_output_filename = f"rtl_airband_{filename_from_path(config_file)}.conf"
    if config.config_out_filename:
        config_output_filename = config.config_out_filename

    if config.global_tau:
        generator.set_global_tau(config.global_tau)

    if config.global_overrides:
        generator.add_global_overrides(config.global_overrides)

    try:
        generator.generate(config_output_filename)
        logger.info(f"generated rtl_airband config: {config_output_filename}")
    except Exception as e:
        logger.error(f"rtl_airband config error: {e}")
        sys.exit(1)

    rtl_airband = RtlSdrAirbandInstance(config_output_filename)

    tasks.append(asyncio.create_task(rtl_airband.run()))

    await rtl_airband.ready_event.wait()

    #
    # We have passed the configuration of RTLSDR-Airband
    #

    listeners: list[UdpStreamProcessor] = []

    channel: VoiceChannel
    for channel in voice_channels:

        stream_processor = UdpStreamProcessor(channel.config.id,
                                              udp_listen_address,
                                              channel.udp_port)
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

    tasks.extend([listener.start_listener() for listener in listeners])
    await asyncio.gather(*tasks)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped manually")
