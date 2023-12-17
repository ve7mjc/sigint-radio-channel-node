from .designators import Designator, decode_emissions_designator

from typing import Optional

class RadioChannel:

    frequency: float

    ctcss: Optional[float]

    designator: Optional[Designator]

    def __init__(self, frequency: float):
        self.frequency = frequency
        self.ctcss = None
        self.designator = None

    def set_ctcss(self, value: float):
        self.ctcss = value

    def set_emissions_designator(self, code: str):
        self.designator = decode_emissions_designator(code)
