from .schema import RadioSystem, RadioSystemChannel

import logging


logger = logging.getLogger(__name__)


class RadioSystems:

    _systems: dict[str, RadioSystem]

    def __init__(self):
        self._systems = {}


    def add(self, system: RadioSystem):
        logger.debug(f"adding system: {system}")
        self._systems[system.id] = system

    def get_by_id(self, id: str) -> RadioSystem:
        return self._systems.get(id)

    @property
    def ids(self) -> list[str]:
        return self._systems.keys()

    @property
    def names(self) -> list[str]:
        names: list[str] = []
        for system in self._systems:
            names.append(self._systems[system].name)
        return names


# Post-loading processing of RadioSystem and Channels
def process_system(system: RadioSystem) -> RadioSystem:

    for channel in system.channels:

        full_id = f"{system.id}.{channel.id}"

        # apply a default designator if not specified
        if channel.designator is None:
            if system.default_designator is None:
                raise Exception(f"channel {full_id} has no designator; and no default designator set")
            channel.designator = system.default_designator
            logger.debug(f"{full_id} applying default designator -> {system.default_designator}")

    return system