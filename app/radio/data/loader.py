from . import find_files, load_radio_system_data
from app.radio.data.systems import RadioSystems, process_system
from app.common.utils import from_dict

import os
import logging


logger = logging.getLogger(__name__)


def load_all() -> RadioSystems:

    logger.debug("load_all() ..")

    this_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(this_path)

    files = find_files(data_path, ".yaml")

    systems = RadioSystems()

    for result in files:

        file, dir, name = result
        file_path = os.path.join(data_path, file)

        logger.debug(f"loading {file_path} ({result}) ..")

        system = load_radio_system_data(file_path)

        system = process_system(system)

        systems.add(system)

        # systems.add()

    return systems