from .schema import RadioSystem
from app.common.utils import find_files, from_dict

import yaml
import os

# load up the systems


def load_radio_system_data(yaml_file: str) -> RadioSystem:

    with open(yaml_file, "r") as f:
        d = yaml.safe_load(f)

    # pull out 'system' if nested -- future concept
    if "system" in d:
        d = d['system']

    system = from_dict(RadioSystem, d)

    return system