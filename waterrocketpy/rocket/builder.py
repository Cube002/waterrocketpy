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
    DEFAULT_DISCHARGE_COEFFICIENT,
    DEFAULT_DRAG_COEFFICIENT,
    DEFAULT_NOZZLE_DIAMETER,
    DEFAULT_ROCKET_DIAMETER,
    DEFAULT_BOTTLE_VOLUME,
    DEFAULT_WATER_FRACTION,
    DEFAULT_EMPTY_MASS,
    ATMOSPHERIC_PRESSURE,
)
from ..core.validation import ParameterValidator

# handle the imports from geometry.py and materials.py
import waterrocketpy.rocket.geometry as geometry
import waterrocketpy.rocket.materials as materials


@dataclass
class MaterialProperties:
    """Container for material properties."""

    name: str
    density: float  # kg/m³
    yield_strength: float  # Pa
    ultimate_strength: float  # Pa
    elastic_modulus: float  # Pa
    poisson_ratio: float
    thermal_expansion: float  # 1/K
    thermal_conductivity: float  # W/(m·K)
    specific_heat: float  # J/(kg·K)
    max_temperature: float  # K
    cost_per_kg: float = 0.0  # Optional cost information


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
        self.material_db = materials.MaterialDatabase()

    def set_bottle(
        self, volume: float, diameter: float, length: float = None
    ) -> "RocketBuilder":
        """Set bottle parameters."""
        self.config.bottle_volume = volume
        self.config.bottle_diameter = diameter
        if length is not None:
            self.config.bottle_length = length
        return self

    def set_nozzle(
        self, diameter: float, discharge_coefficient: float = None
    ) -> "RocketBuilder":
        """Set nozzle parameters."""
        self.config.nozzle_diameter = diameter
        if discharge_coefficient is not None:
            self.config.nozzle_discharge_coefficient = discharge_coefficient
        return self

    def set_mass(
        self, empty_mass: float, water_fraction: float = None
    ) -> "RocketBuilder":
        """Set mass parameters."""
        self.config.empty_mass = empty_mass
        if water_fraction is not None:
            self.config.water_fraction = water_fraction
        return self

    def set_aerodynamics(
        self, drag_coefficient: float, reference_area: float = None
    ) -> "RocketBuilder":
        """Set aerodynamic parameters."""
        self.config.drag_coefficient = drag_coefficient
        if reference_area is not None:
            self.config.reference_area = reference_area
        return self

    def set_initial_conditions(
        self, pressure: float, temperature: float = None
    ) -> "RocketBuilder":
        """Set initial conditions."""
        self.config.initial_pressure = pressure
        if temperature is not None:
            self.config.initial_temperature = temperature
        return self

    def add_liquid_gas(self, mass: float) -> "RocketBuilder":
        """Add liquid gas propellant."""
        self.config.liquid_gas_mass = mass
        return self

    def set_metadata(
        self, name: str, description: str = None
    ) -> "RocketBuilder":
        """Set rocket metadata."""
        self.config.name = name
        if description is not None:
            self.config.description = description
        return self

    def build_from_dimensions(
        self,
        L_body: float,
        L_cone: float,
        d_body: float,
        p_max: float,
        nozzle_diameter: float,
        material_name: str = "PET",
        water_fraction: float = DEFAULT_WATER_FRACTION,
        nozzle_discharge_coefficient: float = DEFAULT_DISCHARGE_COEFFICIENT,
        liquid_gas_mass: float = 0.0,
        safety_factor: float = 2.0,
        cone_wall_thickness: float = 0.002,
    ) -> "RocketBuilder":
        """
        Build rocket configuration from dimensional parameters.

        Args:
            L_body: Body length (m)
            L_cone: Nose cone length (m)
            d_body: Body diameter (m)
            p_max: Maximum pressure (Pa)
            nozzle_diameter: Nozzle diameter (m)
            material_name: Material name (default: 'PET')
            water_fraction: Fraction of bottle volume filled with water
            nozzle_discharge_coefficient: Nozzle discharge coefficient
            liquid_gas_mass: Mass of liquid gas propellant (kg)
            safety_factor: Safety factor for wall thickness calculation
            cone_wall_thickness: Nose cone wall thickness (m)

        Returns:
            RocketBuilder instance
        """
        # Get material properties
        material = self.material_db.get_material(material_name)
        if not material:
            raise ValueError(f"Unknown material: {material_name}")

        # Calculate wall thickness for body
        wall_thickness_body = (
            materials.StructuralAnalysis.calculate_wall_thickness(
                internal_pressure=p_max,
                diameter=d_body,
                material=material,
                safety_factor=safety_factor,
            )
        )

        # Calculate bottle volume (cylindrical approximation)
        bottle_volume = np.pi * (d_body / 2) ** 2 * L_body

        # Calculate body mass
        m_body = materials.calculate_bottle_mass(
            diameter=d_body,
            length=L_body,
            wall_thickness=wall_thickness_body,
            material_name=material_name,
        )

        # Calculate nose cone surface area
        A_cone = geometry.RocketGeometry.cone_surface_area(
            diameter=d_body, height=L_cone
        )

        # Calculate cone mass
        cone_volume = A_cone * cone_wall_thickness
        m_cone = materials.StructuralAnalysis.calculate_mass(
            cone_volume, material
        )

        # Calculate total rocket dimensions
        L_rocket = L_body + L_cone

        # Calculate rocket surface area (wetted area)
        surface_area_rocket = (
            geometry.RocketGeometry.calculate_rocket_wetted_area(
                diameter=d_body,
                length=L_rocket,
                nose_cone_height=L_cone,
                fin_area=0.0,  # Set to 0 as requested
            )
        )

        # Calculate Reynolds number and drag coefficient
        # Using characteristic length = L_rocket
        Re = 40000 * L_rocket  # Simplified Reynolds number

        # Calculate friction coefficients
        C_f_laminar = 1.437 * Re ** (-0.5058)
        C_f_turbulent = 0.03725 * Re ** (-0.1557)
        C_f = (C_f_laminar + C_f_turbulent) / 2

        # Calculate areas
        S_bt = np.pi * (d_body / 2) ** 2  # Cross-sectional area
        S_w = surface_area_rocket  # Wetted surface area

        # Calculate drag coefficient
        C_drag = (
            1.02
            * C_f
            * (1 + 1.5 / ((L_rocket / d_body) ** (3 / 2)))
            * S_w
            / S_bt
        )

        # Calculate empty mass
        m_empty = m_cone + m_body

        # Set all calculated parameters
        self.config.bottle_volume = bottle_volume
        self.config.bottle_diameter = d_body
        self.config.bottle_length = L_body
        self.config.nozzle_diameter = nozzle_diameter
        self.config.nozzle_discharge_coefficient = nozzle_discharge_coefficient
        self.config.empty_mass = m_empty
        self.config.water_fraction = water_fraction
        self.config.drag_coefficient = C_drag
        self.config.reference_area = S_bt
        self.config.initial_pressure = p_max
        self.config.liquid_gas_mass = liquid_gas_mass

        # Store additional calculated values as metadata
        self.config.description = (
            f"Rocket built from dimensions: L_body={L_body:.3f}m, "
            f"L_cone={L_cone:.3f}m, d_body={d_body:.3f}m, "
            f"p_max={p_max/1000:.0f}kPa, material={material_name}, "
            f"wall_thickness={wall_thickness_body:.4f}m, "
            f"empty_mass={m_empty:.3f}kg, C_drag={C_drag:.3f}"
        )

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
            "P0": self.config.initial_pressure,
            "A_nozzle": self.config.nozzle_area,
            "V_bottle": self.config.bottle_volume,
            "water_fraction": self.config.water_fraction,
            "C_d": self.config.nozzle_discharge_coefficient,
            "m_empty": self.config.empty_mass,
            "C_drag": self.config.drag_coefficient,
            "A_rocket": self.config.reference_area,
            "liquid_gas_mass": self.config.liquid_gas_mass,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RocketBuilder":
        """Create builder from dictionary."""
        builder = cls()
        builder.config = RocketConfiguration(**data)
        return builder

    @classmethod
    def from_json(cls, file_path: str) -> "RocketBuilder":
        """Create builder from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Rocket configuration file not found: {file_path}"
            )

        with open(path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    def to_json(self, file_path: str) -> None:
        """Save rocket configuration to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(asdict(self.config), f, indent=2)

    def reset(self) -> "RocketBuilder":
        """Reset builder to default configuration."""
        self.config = RocketConfiguration()
        return self


# examples:


# Example usage:
def create_dimensional_rocket_example():
    """Example of creating a rocket from dimensional parameters."""
    builder = RocketBuilder()

    # Build rocket from dimensions
    config = (
        builder.build_from_dimensions(
            L_body=0.25,  # 25 cm body length
            L_cone=0.08,  # 8 cm nose cone
            d_body=0.088,  # 88 mm diameter (standard 2L bottle)
            p_max=8 * ATMOSPHERIC_PRESSURE,  # 8 bar pressure
            nozzle_diameter=0.01,  # 10 mm nozzle
            material_name="PET",
            water_fraction=0.3,
        )
        .set_metadata(
            name="Dimensional Rocket",
            description="Built from dimensional parameters",
        )
        .build()
    )

    return config


def create_standard_rocket() -> RocketConfiguration:
    """Create a standard water rocket configuration."""
    return (RocketBuilder()
       .set_bottle(volume=0.002, diameter=0.1)  # 2L bottle
        .set_nozzle(diameter=0.015)
        .set_mass(empty_mass=0.25, water_fraction=0.33)
        .set_initial_conditions(pressure=8 * ATMOSPHERIC_PRESSURE)
       .set_metadata("Standard 2L Rocket", "Standard configuration for 2L bottle")
        .build()
    )

def create_standard_IPT_rocket() -> RocketConfiguration:
    """Create a standard water rocket configuration."""
    return (
        RocketBuilder()
        .set_bottle(volume=0.001, diameter=0.1)  # 2L bottle
        .set_nozzle(diameter=0.021)
        .set_mass(empty_mass=0.1, water_fraction=0.33)
        .set_initial_conditions(pressure=13 * ATMOSPHERIC_PRESSURE)
        .set_metadata(
            "Standard IPT 1L Rocket",
            "Standard IPT Air configuration for 1L bottle",
        )
        .build()
    )



def create_IPT1_rocket() -> RocketConfiguration:
    """Create a standard water rocket configuration."""
    return (
        RocketBuilder()
        .set_bottle(volume=0.001, diameter=0.1)  # 2L bottle
        .set_nozzle(diameter=0.021)
        .set_mass(empty_mass=0.1, water_fraction=0.33)
        .set_initial_conditions(pressure=13 * ATMOSPHERIC_PRESSURE)
        .set_metadata(
            "Standard IPT 1L Rocket",
            "Standard IPT Air configuration for 1L bottle",
        )
        .build()
    )


def create_competition_rocket() -> RocketConfiguration:
    """Create a competition-grade water rocket configuration."""
    return (
        RocketBuilder()
        .set_bottle(volume=0.0015, diameter=0.08)  # 1.5L bottle
        .set_nozzle(diameter=0.012, discharge_coefficient=0.98)
        .set_mass(empty_mass=0.15, water_fraction=0.4)
        .set_aerodynamics(drag_coefficient=0.3)  # Improved aerodynamics
        .set_initial_conditions(pressure=12 * ATMOSPHERIC_PRESSURE)
        .set_metadata("Competition Rocket", "Optimized for maximum altitude")
        .build()
    )


def create_high_pressure_rocket() -> RocketConfiguration:
    """Create a high-pressure water rocket with liquid gas boost."""
    return (
        RocketBuilder()
        .set_bottle(volume=0.001, diameter=0.1)  # 1L bottle
        .set_nozzle(diameter=0.020)
        .set_mass(empty_mass=0.3, water_fraction=0.25)
        .add_liquid_gas(mass=0.05)  # 50g liquid CO2
        .set_initial_conditions(pressure=15 * ATMOSPHERIC_PRESSURE)
        .set_metadata("High Pressure Rocket", "Rocket with liquid gas boost")
        .build()
    )
