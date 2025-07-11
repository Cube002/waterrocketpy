# waterrocketpy/rocket/builder.py
"""
Rocket builder for creating and managing rocket configurations.
"""

import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.constants import (
    DEFAULT_DISCHARGE_COEFFICIENT, DEFAULT_DRAG_COEFFICIENT,
    DEFAULT_NOZZLE_DIAMETER, DEFAULT_ROCKET_DIAMETER,
    DEFAULT_BOTTLE_VOLUME, DEFAULT_WATER_FRACTION, DEFAULT_EMPTY_MASS,
    ATMOSPHERIC_PRESSURE
)
from ..core.validation import ParameterValidator


@dataclass
class RocketConfiguration:
    """Data class for rocket configuration."""
    # Bottle parameters
    bottle_volume: float = DEFAULT_BOTTLE_VOLUME  # m³
    bottle_diameter: float = DEFAULT_ROCKET_DIAMETER  # m
    bottle_length: float = 0.3  # m
    
    # Nozzle parameters
    nozzle_diameter: float = DEFAULT_NOZZLE_DIAMETER  # m
    nozzle_discharge_coefficient: float = DEFAULT_DISCHARGE_COEFFICIENT
    
    # Mass parameters
    empty_mass: float = DEFAULT_EMPTY_MASS  # kg
    water_fraction: float = DEFAULT_WATER_FRACTION
    
    # Aerodynamic parameters
    drag_coefficient: float = DEFAULT_DRAG_COEFFICIENT
    reference_area: float = None  # Will be calculated if None
    
    # Initial conditions
    initial_pressure: float = 10 * ATMOSPHERIC_PRESSURE  # Pa
    initial_temperature: float = 300  # K
    
    # Optional liquid gas parameters
    liquid_gas_mass: float = 0.0  # kg
    
    # Metadata
    name: str = "Default Rocket"
    description: str = "Standard water rocket configuration"
    
    def __post_init__(self):
        """Calculate derived parameters after initialization."""
        if self.reference_area is None:
            self.reference_area = np.pi * (self.bottle_diameter / 2) ** 2
    
    @property
    def nozzle_area(self) -> float:
        """Calculate nozzle cross-sectional area."""
        return np.pi * (self.nozzle_diameter / 2) ** 2
    
    @property
    def water_volume(self) -> float:
        """Calculate initial water volume."""
        return self.bottle_volume * self.water_fraction
    
    @property
    def water_mass(self) -> float:
        """Calculate initial water mass."""
        from ..core.constants import WATER_DENSITY
        return WATER_DENSITY * self.water_volume
    
    @property
    def total_mass(self) -> float:
        """Calculate total initial mass."""
        return self.empty_mass + self.water_mass + self.liquid_gas_mass


class RocketBuilder:
    """Builder class for creating rocket configurations."""
    
    def __init__(self):
        self.config = RocketConfiguration()
        self.validator = ParameterValidator()
    
    def set_bottle(self, volume: float, diameter: float, length: float = None) -> 'RocketBuilder':
        """Set bottle parameters."""
        self.config.bottle_volume = volume
        self.config.bottle_diameter = diameter
        if length is not None:
            self.config.bottle_length = length
        return self
    
    def set_nozzle(self, diameter: float, discharge_coefficient: float = None) -> 'RocketBuilder':
        """Set nozzle parameters."""
        self.config.nozzle_diameter = diameter
        if discharge_coefficient is not None:
            self.config.nozzle_discharge_coefficient = discharge_coefficient
        return self
    
    def set_mass(self, empty_mass: float, water_fraction: float = None) -> 'RocketBuilder':
        """Set mass parameters."""
        self.config.empty_mass = empty_mass
        if water_fraction is not None:
            self.config.water_fraction = water_fraction
        return self
    
    def set_aerodynamics(self, drag_coefficient: float, reference_area: float = None) -> 'RocketBuilder':
        """Set aerodynamic parameters."""
        self.config.drag_coefficient = drag_coefficient
        if reference_area is not None:
            self.config.reference_area = reference_area
        return self
    
    def set_initial_conditions(self, pressure: float, temperature: float = None) -> 'RocketBuilder':
        """Set initial conditions."""
        self.config.initial_pressure = pressure
        if temperature is not None:
            self.config.initial_temperature = temperature
        return self
    
    def add_liquid_gas(self, mass: float) -> 'RocketBuilder':
        """Add liquid gas propellant."""
        self.config.liquid_gas_mass = mass
        return self
    
    def set_metadata(self, name: str, description: str = None) -> 'RocketBuilder':
        """Set rocket metadata."""
        self.config.name = name
        if description is not None:
            self.config.description = description
        return self
    
    def build(self) -> RocketConfiguration:
        """Build and validate the rocket configuration."""
        # Update calculated parameters
        self.config.__post_init__()
        
        # Convert to parameter dictionary for validation
        params = self.to_simulation_params()
        
        # Validate parameters
        warnings = self.validator.validate_rocket_parameters(params)
        if warnings:
            print(f"Rocket '{self.config.name}' validation warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        return self.config
    
    def to_simulation_params(self) -> Dict[str, Any]:
        """Convert rocket configuration to simulation parameters."""
        return {
            'P0': self.config.initial_pressure,
            'A_nozzle': self.config.nozzle_area,
            'V_bottle': self.config.bottle_volume,
            'water_fraction': self.config.water_fraction,
            'C_d': self.config.nozzle_discharge_coefficient,
            'm_empty': self.config.empty_mass,
            'C_drag': self.config.drag_coefficient,
            'A_rocket': self.config.reference_area,
            'liquid_gas_mass': self.config.liquid_gas_mass
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RocketBuilder':
        """Create builder from dictionary."""
        builder = cls()
        builder.config = RocketConfiguration(**data)
        return builder
    
    @classmethod
    def from_json(cls, file_path: str) -> 'RocketBuilder':
        """Create builder from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Rocket configuration file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def to_json(self, file_path: str) -> None:
        """Save rocket configuration to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def reset(self) -> 'RocketBuilder':
        """Reset builder to default configuration."""
        self.config = RocketConfiguration()
        return self


def create_standard_rocket() -> RocketConfiguration:
    """Create a standard water rocket configuration."""
    return (RocketBuilder()
            .set_bottle(volume=0.002, diameter=0.1)  # 2L bottle
            .set_nozzle(diameter=0.015)
            .set_mass(empty_mass=0.25, water_fraction=0.33)
            .set_initial_conditions(pressure=8 * ATMOSPHERIC_PRESSURE)
            .set_metadata("Standard 2L Rocket", "Standard configuration for 2L bottle")
            .build())


def create_competition_rocket() -> RocketConfiguration:
    """Create a competition-grade water rocket configuration."""
    return (RocketBuilder()
            .set_bottle(volume=0.0015, diameter=0.08)  # 1.5L bottle
            .set_nozzle(diameter=0.012, discharge_coefficient=0.98)
            .set_mass(empty_mass=0.15, water_fraction=0.4)
            .set_aerodynamics(drag_coefficient=0.3)  # Improved aerodynamics
            .set_initial_conditions(pressure=12 * ATMOSPHERIC_PRESSURE)
            .set_metadata("Competition Rocket", "Optimized for maximum altitude")
            .build())


def create_high_pressure_rocket() -> RocketConfiguration:
    """Create a high-pressure water rocket with liquid gas boost."""
    return (RocketBuilder()
            .set_bottle(volume=0.001, diameter=0.1)  # 1L bottle
            .set_nozzle(diameter=0.020)
            .set_mass(empty_mass=0.3, water_fraction=0.25)
            .add_liquid_gas(mass=0.05)  # 50g liquid CO2
            .set_initial_conditions(pressure=15 * ATMOSPHERIC_PRESSURE)
            .set_metadata("High Pressure Rocket", "Rocket with liquid gas boost")
            .build())