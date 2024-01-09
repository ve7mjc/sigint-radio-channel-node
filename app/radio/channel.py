from .schema import RadioChannelRecord
from app.common.utils import from_dict

import os
import logging

import yaml


logger = logging.getLogger(__name__)


def load_channels(yaml_file: str) -> list[RadioChannelRecord]:

    with open(yaml_file, "r") as file:
        d = yaml.safe_load(file)

    channels: list[RadioChannelRecord] = []
    for chd in d['channels']:
        print(chd)
        c = from_dict(RadioChannelRecord, chd)
        channels.append(c)

    return channels
