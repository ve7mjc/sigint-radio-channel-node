from dataclasses import dataclass


@dataclass
class Certificate:
    common_name: str
    certfile: str
    keyfile: str
