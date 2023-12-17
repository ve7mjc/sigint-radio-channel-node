from dataclasses import is_dataclass, fields, MISSING
from typing import TypeVar, Type, Any, get_args, get_origin, Union
import os
import logging


DataclassType = TypeVar("DataclassType")

logger = logging.getLogger(__name__)


def from_dict(dataclass_type: Type[DataclassType], dictionary: dict[str, Any]) -> DataclassType:
    field_values = {}
    for field in fields(dataclass_type):
        name = field.name
        field_type = field.type

        # Check if field is in the dictionary
        if name in dictionary:
            value = dictionary[name]
        # Use default value if field is missing in the dictionary
        elif field.default is not MISSING:
            value = field.default
        # Use default factory if available
        elif field.default_factory is not MISSING:
            value = field.default_factory()
        else:
            # If no default is specified, skip setting the value
            continue

        # Handle Optional, dataclass, and list types
        if get_origin(field_type) is Union and type(None) in get_args(field_type):
            if value is not None:
                inner_type = next(t for t in get_args(field_type) if t is not type(None))
                if is_dataclass(inner_type):
                    value = from_dict(inner_type, value)
        elif is_dataclass(field_type):
            value = from_dict(field_type, value)
        elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
            element_type = field_type.__args__[0]
            if is_dataclass(element_type):
                value = [from_dict(element_type, v) for v in value]

        field_values[name] = value

    return dataclass_type(**field_values)


def filename_from_path(file_path: str) -> str:
    base_name = os.path.basename(file_path)
    filename, _ = os.path.splitext(base_name)
    return filename

def channel_closest_center(channels: list[Union[int,float]]) -> Union[int,float]:
    """
    supports both int and float; returns the same as input
    """
    if len(channels) == 0:
        return None
    elif len(channels) == 1 or len(channels) == 2:
        return channels[0]
    else:
        chan_max = max(channels)
        chan_min = min(channels)
        freq_center = chan_min + ((chan_max - chan_min) / 2)

        # find channel with least distance from center
        chan_least = None
        dist_least = None
        for channel in channels:
            dist = abs(channel - freq_center)

            if chan_least is None or dist < dist_least:
                chan_least = channel
                dist_least = dist

    return chan_least

def bandwidth_required(channel_frequencies: list[float],
                       channel_width: int) -> int:

        # frequencies are float mhz
        freq_min_hz = int(min(channel_frequencies) * 1e6)
        freq_max_hz = int(max(channel_frequencies) * 1e6)

        return (freq_max_hz - freq_min_hz) + channel_width

