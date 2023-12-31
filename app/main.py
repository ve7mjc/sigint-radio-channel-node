from .config import ConfigManager, AppConfig
from .literals import DEFAULT_CONFIG_FILE
from .channel_manager import RadioChannelManager

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import argparse

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

# squelch noisy library loggers
logging.getLogger('asyncio').setLevel(logging.WARNING)


async def main():

    config_manager = ConfigManager()

    # commandline argument processing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Configuration file',
                        required=False)
    args = vars(parser.parse_args())

    config_file = args.get('config', None)

    if not config_file:
        logger.error("requires config file!")
        sys.exit(1)

    # Base Config
    config_base = "config.yaml"
    if os.path.exists(config_base):
        config_manager.add_yaml(config_base)

    try:
        config_manager.add_yaml(config_file)
        config = config_manager.process_config()
    except FileNotFoundError:
        logger.error(f"config file '{config_file}' not found!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"error parsing configuration: {e}")
        sys.exit(1)

    # data store path
    logger.info(f"using data store path: {config.data_path}")
    if not os.path.exists(config.data_path):
        try:
            os.makedirs(config.data_path, exist_ok = True)
        except PermissionError:
            logger.error(f"unable to create data path:")
            sys.exit(1)

    ch_mgr = RadioChannelManager(config=config)

    try:
        ch_mgr.configure()
    except Exception as e:
        logger.error(f"error configuring: {e}")
        sys.exit(1)

    try:
        await ch_mgr.start()
    except Exception as e:
        logger.error(e)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped manually")
