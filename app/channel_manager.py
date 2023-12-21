from .rtlsdr_airband.config_generator import (
    ConfigGenerator,
    RtlSdrAirbandConfig,
    RtlSdrAirbandDevice,
    RtlAirbandConfigurationException
)
from .literals import DEFAULT_UDP_PORT_BASE
from .config import AppConfig
from .channel import RadioChannelProcessor
from .rtlsdr_airband.rtl_airband import (
    RtlSdrAirbandInstance,
    ProcessEvent,
    ProcessEventType
)
from .utils import filename_from_path
from .config import ConfigurationException

import asyncio
import logging
import sys
import traceback


logger = logging.getLogger(__name__)


class RadioChannelManager:

    config: AppConfig
    tasks: list
    rtlsdr_airband_configs: list[RtlSdrAirbandConfig]
    rtlsdr_airband_instances: list[RtlSdrAirbandInstance]

    listen_addr: str

    channels: list[RadioChannelProcessor]

    def __init__(self, config: AppConfig):

        self.config = config

        self.tasks = []
        self.rtlsdr_airband_instances = []
        self.rtlsdr_airband_configs = []
        self.channels = []

    def configure_channels(self):

        for config in self.config.channels:

            config.generate_id()

            listen_port = config.udp_port or self._get_next_listen_port()

            channel = RadioChannelProcessor(
                config,
                self.config.listen_address,
                listen_port,
                data_output_path=self.config.data_store_path
            )

            # Mumble config
            if self.config.mumble:
                join_channel = self.config.mumble.default_channel
                if channel.config.mumble and channel.config.mumble.channel:
                    join_channel = channel.config.mumble.channel
                if join_channel is None:
                    logger.warning("mumble channel not specified, cannot join!")
                else:
                    channel.add_mumble_output(
                        self.config.mumble.remote_host,
                        self.config.mumble.remote_port,
                        channel=join_channel
                    )

            self.channels.append(channel)

    def _get_next_listen_port(self) -> int:
        port: int = self.config.listen_port_base
        ports_in_use: list[int] = []
        for channel in self.channels:
            if channel.listen_port:
                ports_in_use.append(channel.listen_port)
        # increment port until no collision
        while port in ports_in_use:
            port += 1
        return port

    def configure_rtlsdr_airband(self):

        rtlsdr_airband_generator = ConfigGenerator(
            global_overrides=self.config.rtlsdr_airband_global_overrides
        )

        for device_cfg in self.config.devices:

            # support rtlsdr_airband.* devices -- passing the subtype
            # on as the type=xxxx for rtl_airband
            if device_cfg.type.startswith("rtlsdr_airband"):
                device_type = device_cfg.type.replace("rtlsdr_airband.","")
                device = RtlSdrAirbandDevice(
                    type=device_type,
                    serial=device_cfg.serial,
                    device_string=device_cfg.device_string,
                    gain=device_cfg.gain,
                    sample_rate=device_cfg.sample_rate,
                    correction=device_cfg.correction,
                    overrides=device_cfg.rtlsdr_airband_overrides,
                    centerfreq=device_cfg.center_freq
                )
                rtlsdr_airband_generator.add_device(device)

        if len(rtlsdr_airband_generator.config.devices) == 0:
            raise RtlAirbandConfigurationException("no RTLSDR-Airband devices configured!")

        for channel in self.channels:

            # RTLSDR-Airband Channels
            rtl_airband_channel = rtlsdr_airband_generator.add_channel(
                channel.channel, channel.config.rtlsdr_airband_overrides
            )

            rtl_airband_channel.add_output_udp_stream(
                self.config.listen_address,
                channel.listen_port
            )

        # Generate rtl_airband config
        config_output_filename = \
            f"rtl_airband_{filename_from_path(self.config.config_file)}.conf"
        if self.config.config_out_filename:
            config_output_filename = self.config.config_out_filename

        try:
            config = rtlsdr_airband_generator.generate(config_output_filename)
            logger.info(f"generated rtl_airband config: {config_output_filename}")
        except Exception as e:
            logger.error(f"rtl_airband config error: {e}")
            raise e

        self.rtlsdr_airband_instances.append(
            RtlSdrAirbandInstance(config_output_filename, config.id)
        )

    def configure(self):
        try:
            self.configure_channels()
        except RtlAirbandConfigurationException as e:
            logger.error(f"error configuring RTLSDR-Airband: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"error configuring channels: {type(e)}={e}; {traceback.format_exc()}")

        try:
            self.configure_rtlsdr_airband()
        except RtlAirbandConfigurationException as e:
            logger.error(f"error configuring RTLSDR-Airband: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"error configuring RTLSDR-Airband: {type(e)}={e}; {traceback.format_exc()}")
            sys.exit(1)

        # Configuration Summary
        print(self.configuration_summary())

    async def start(self):

        process_tasks = {}

        for rtlsdr_airband in self.rtlsdr_airband_instances:

            task = asyncio.create_task(rtlsdr_airband.run())
            process_tasks[rtlsdr_airband.id] = task

            event = await rtlsdr_airband.process.events.get()
            if event.type == ProcessEventType.READY:
                logger.info("rtl_airband ready -- proceeding")
                continue
            else:
                logger.error(f"rtl_airband error: {event.type.name}")
                # an rtl_airband instance has failed -- we will not proceed
                return

        self.tasks.extend([listener.start_listener() for listener in self.channels])

        await asyncio.gather(*self.tasks)


    def configuration_summary(self) -> str:

        out = "\r\nConfiguration Summary:\r\n"


        out += "\r\nChannels:\r\n"
        for channel in self.channels:
            out += f" {channel.channel.frequency} {channel.label}\r\n"

        return out
