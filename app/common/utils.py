from dataclasses import is_dataclass, fields, MISSING, asdict
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


def dataclass_to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, (list, tuple)):
        return [dataclass_to_dict(item) for item in obj]
    else:
        return obj


def find_files(path: str, extension: str):
    """
    This function searches recursively for all .{extension} files in the given path.
    It returns a list of tuples where each tuple contains:
    - The relative path to the found file
    - The relative path to the folder in dot-notated format
    - The filename
    """
    yaml_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                relative_path = os.path.relpath(os.path.join(root, file), path)
                folder_path_dot_notated = root.replace(os.sep, '.')
                yaml_files.append((relative_path, folder_path_dot_notated, file))

    return yaml_files