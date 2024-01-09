from .loader import load_all
from .systems import RadioSystems

import logging

if __name__ == "__main__":

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    systems = load_all()

    print(systems.names)
