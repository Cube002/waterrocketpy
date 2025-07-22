import json
import numpy as np
from pathlib import Path
from typing import Union, Dict, Any

from waterrocketpy.core.simulation import FlightData  # Adjust path as needed


def load_flight_data(path: Union[str, Path]) -> FlightData:
    """
    Load FlightData from a .json or .npz file.

    Args:
        path: Path to the .json or .npz file (without extension allowed).

    Returns:
        FlightData instance reconstructed from saved data.
    """
    path = Path(path)
    if path.suffix == "":
        if (path.with_suffix(".json")).exists():
            path = path.with_suffix(".json")
        elif (path.with_suffix(".npz")).exists():
            path = path.with_suffix(".npz")
        else:
            raise FileNotFoundError(
                "Neither .json nor .npz file found for base path."
            )

    if path.suffix == ".json":
        with open(path, "r") as f:
            data = json.load(f)
        fd_fields = FlightData.__dataclass_fields__.keys()
        init_args = {
            key: (
                np.array(value)
                if isinstance(
                    FlightData.__dataclass_fields__[key].type, type(np.ndarray)
                )
                else value
            )
            for key, value in data.items()
            if key in fd_fields
        }
        return FlightData(**init_args)

    elif path.suffix == ".npz":
        loaded = np.load(path, allow_pickle=False)
        init_args = {
            key: loaded[key]
            for key in FlightData.__dataclass_fields__.keys()
            if key in loaded
        }
        return FlightData(**init_args)

    else:
        raise ValueError("Unsupported file extension. Use .json or .npz.")


def load_simulation_params(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load only the simulation parameters from a .json file.

    Args:
        path: Path to the .json file (can omit extension).

    Returns:
        Dictionary of simulation parameters.
    """
    path = Path(path)
    if path.suffix == "":
        path = path.with_suffix(".json")

    if not path.exists():
        raise FileNotFoundError(f"No JSON file found at {path}")

    with open(path, "r") as f:
        data = json.load(f)

    return data.get("simulation_params", {})
