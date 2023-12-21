from dataclasses import dataclass
from typing import Optional


@dataclass
class RadioChannelRecord:
    freq: float
    label: str

    id: Optional[str] = None
    designator: [str] = None
    ctcss: Optional[float] = None
