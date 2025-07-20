import json
import numpy as np
from dataclasses import asdict
from typing import Union
from pathlib import Path

from ..core.simulation import FlightData  # Adjust import path as needed


def save_flight_data(
    data: FlightData,
    path: Union[str, Path],
    include_metadata: bool = True
) -> None:
    """
    Save FlightData to JSON and NPZ formats.

    Args:
        data: The FlightData object to save.
        path: Base path (without extension) for saving files.
        include_metadata: If True, includes simulation parameters in the JSON file.
    """
    path = Path(path)

    # Convert arrays to lists for JSON serialization
    json_data = {
        key: val.tolist() if isinstance(val, np.ndarray) else val
        for key, val in asdict(data).items()
    }

    # Add simulation parameters if available and requested
    if include_metadata and hasattr(data, 'to_simulation_params'):
        try:
            json_data['simulation_params'] = data.to_simulation_params()
        except Exception as e:
            print(f"Warning: Could not extract simulation parameters: {e}")

    # Save as JSON
    json_file = path.with_suffix('.json')
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)

    # Save as compressed NPZ
    npz_file = path.with_suffix('.npz')
    np.savez_compressed(npz_file, **{
        key: val for key, val in asdict(data).items()
        if isinstance(val, np.ndarray)
    })

    print(f"Saved FlightData to {json_file} and {npz_file}")


def load_flight_data(path: Union[str, Path]) -> FlightData:
    """
    Load FlightData from a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Reconstructed FlightData object.
    """
    path = Path(path).with_suffix('.json')
    with open(path, 'r') as f:
        json_data = json.load(f)

    # Extract only FlightData fields (ignore metadata)
    fd_fields = FlightData.__dataclass_fields__.keys()
    init_args = {
        key: np.array(val) if isinstance(FlightData.__dataclass_fields__[key].type, type(np.ndarray))
        else val
        for key, val in json_data.items()
        if key in fd_fields
    }

    return FlightData(**init_args)
