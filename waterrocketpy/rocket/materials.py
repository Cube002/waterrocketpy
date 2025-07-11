# waterrocketpy/rocket/materials.py
"""
Material properties and calculations for water rocket components.
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


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


class MaterialDatabase:
    """Database of material properties for rocket components."""
    
    def __init__(self):
        self._materials = self._load_default_materials()
    
    def _load_default_materials(self) -> Dict[str, MaterialProperties]:
        """Load default material properties."""
        materials = {}
        
        # PET (Polyethylene Terephthalate) - Common bottle material
        materials['PET'] = MaterialProperties(
            name='PET',
            density=1380,  # kg/m³
            yield_strength=55e6,  # Pa
            ultimate_strength=75e6,  # Pa
            elastic_modulus=2.8e9,  # Pa
            poisson_ratio=0.37,
            thermal_expansion=70e-6,  # 1/K
            thermal_conductivity=0.24,  # W/(m·K)
            specific_heat=1200,  # J/(kg·K)
            max_temperature=343,  # K (70°C)
            cost_per_kg=1.5
        )
        
        # HDPE (High-Density Polyethylene)
        materials['HDPE'] = MaterialProperties(
            name='HDPE',
            density=960,  # kg/m³
            yield_strength=30e6,  # Pa
            ultimate_strength=40e6,  # Pa
            elastic_modulus=1.1e9,  # Pa
            poisson_ratio=0.42,
            thermal_expansion=120e-6,  # 1/K
            thermal_conductivity=0.48,  # W/(m·K)
            specific_heat=1900,  # J/(kg·K)
            max_temperature=393,  # K (120°C)
            cost_per_kg=1.2
        )
        
        # Aluminum (for nozzles, fins)
        materials['Aluminum'] = MaterialProperties(
            name='Aluminum',
            density=2700,  # kg/m³
            yield_strength=276e6,  # Pa
            ultimate_strength=310e6,  # Pa
            elastic_modulus=69e9,  # Pa
            poisson_ratio=0.33,
            thermal_expansion=23e-6,  # 1/K
            thermal_conductivity=237,  # W/(m·K)
            specific_heat=900,  # J/(kg·K)
            max_temperature=933,  # K (660°C)
            cost_per_kg=2.5
        )
        
        # Carbon Fiber (for advanced rockets)
        materials['Carbon_Fiber'] = MaterialProperties(
            name='Carbon Fiber',
            density=1600,  # kg/m³
            yield_strength=3500e6,  # Pa
            ultimate_strength=4000e6,  # Pa
            elastic_modulus=230e9,  # Pa
            poisson_ratio=0.22,
            thermal_expansion=-0.5e-6,  # 1/K
            thermal_conductivity=100,  # W/(m·K)
            specific_heat=700,  # J/(kg·K)
            max_temperature=673,  # K (400°C)
            cost_per_kg=50.0
        )
        
        # Fiberglass
        materials['Fiberglass'] = MaterialProperties(
            name='Fiberglass',
            density=1800,  # kg/m³
            yield_strength=400e6,  # Pa
            ultimate_strength=500e6,  # Pa
            elastic_modulus=35e9,  # Pa
            poisson_ratio=0.25,
            thermal_expansion=8e-6,  # 1/K
            thermal_conductivity=0.35,  # W/(m·K)
            specific_heat=800,  # J/(kg·K)
            max_temperature=573,  # K (300°C)
            cost_per_kg=8.0
        )
        
        # Stainless Steel (for high-pressure applications)
        materials['Stainless_Steel'] = MaterialProperties(
            name='Stainless Steel',
            density=8000,  # kg/m³
            yield_strength=520e6,  # Pa
            ultimate_strength=720e6,  # Pa
            elastic_modulus=200e9,  # Pa
            poisson_ratio=0.29,
            thermal_expansion=17e-6,  # 1/K
            thermal_conductivity=16,  # W/(m·K)
            specific_heat=500,  # J/(kg·K)
            max_temperature=1673,  # K (1400°C)
            cost_per_kg=5.0
        )
        
        return materials
    
    def get_material(self, name: str) -> Optional[MaterialProperties]:
        """Get material properties by name."""
        return self._materials.get(name)
    
    def add_material(self, material: MaterialProperties) -> None:
        """Add a new material to the database."""
        self._materials[material.name] = material
    
    def list_materials(self) -> list:
        """List all available materials."""
        return list(self._materials.keys())
    
    def load_from_json(self, file_path: str) -> None:
        """Load materials from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Material database file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        for name, props in data.items():
            material = MaterialProperties(name=name, **props)
            self.add_material(material)
    
    def save_to_json(self, file_path: str) -> None:
        """Save materials to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for name, material in self._materials.items():
            data[name] = {
                'density': material.density,
                'yield_strength': material.yield_strength,
                'ultimate_strength': material.ultimate_strength,
                'elastic_modulus': material.elastic_modulus,
                'poisson_ratio': material.poisson_ratio,
                'thermal_expansion': material.thermal_expansion,
                'thermal_conductivity': material.thermal_conductivity,
                'specific_heat': material.specific_heat,
                'max_temperature': material.max_temperature,
                'cost_per_kg': material.cost_per_kg
            }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


class StructuralAnalysis:
    """Structural analysis calculations for rocket components."""
    
    @staticmethod
    def calculate_wall_thickness(internal_pressure: float, diameter: float,
                               material: MaterialProperties, safety_factor: float = 2.0) -> float:
        """
        Calculate minimum wall thickness for pressure vessel.
        
        Args:
            internal_pressure: Internal pressure (Pa)
            diameter: Vessel diameter (m)
            material: Material properties
            safety_factor: Safety factor
            
        Returns:
            Minimum wall thickness (m)
        """
        # Using thin-wall pressure vessel formula: σ = p*d/(2*t)
        # Rearranging: t = p*d/(2*σ_allow)
        
        allowable_stress = material.yield_strength / safety_factor
        radius = diameter / 2
        
        # Hoop stress formula for thin-walled cylinder
        thickness = internal_pressure * radius / allowable_stress
        
        return thickness
    
    @staticmethod
    def calculate_burst_pressure(diameter: float, wall_thickness: float,
                               material: MaterialProperties) -> float:
        """
        Calculate burst pressure for a cylindrical vessel.
        
        Args:
            diameter: Vessel diameter (m)
            wall_thickness: Wall thickness (m)
            material: Material properties
            
        Returns:
            Burst pressure (Pa)
        """
        radius = diameter / 2
        
        # Using ultimate strength for burst calculation
        burst_pressure = 2 * material.ultimate_strength * wall_thickness / radius
        
        return burst_pressure
    
    @staticmethod
    def calculate_mass(volume: float, material: MaterialProperties) -> float:
        """
        Calculate mass of component.
        
        Args:
            volume: Component volume (m³)
            material: Material properties
            
        Returns:
            Mass (kg)
        """
        return volume * material.density
    
    @staticmethod
    def check_temperature_limits(operating_temperature: float,
                               material: MaterialProperties) -> bool:
        """
        Check if operating temperature is within material limits.
        
        Args:
            operating_temperature: Operating temperature (K)
            material: Material properties
            
        Returns:
            True if temperature is acceptable
        """
        return operating_temperature <= material.max_temperature
    
    @staticmethod
    def calculate_thermal_stress(temperature_change: float, length: float,
                               material: MaterialProperties) -> float:
        """
        Calculate thermal stress due to temperature change.
        
        Args:
            temperature_change: Temperature change (K)
            length: Component length (m)
            material: Material properties
            
        Returns:
            Thermal stress (Pa)
        """
        # Thermal strain = α * ΔT
        # Thermal stress = E * α * ΔT (if constrained)
        
        thermal_strain = material.thermal_expansion * temperature_change
        thermal_stress = material.elastic_modulus * thermal_strain
        
        return thermal_stress
    
    @staticmethod
    def calculate_cost(volume: float, material: MaterialProperties) -> float:
        """
        Calculate material cost.
        
        Args:
            volume: Component volume (m³)
            material: Material properties
            
        Returns:
            Cost (currency units)
        """
        mass = StructuralAnalysis.calculate_mass(volume, material)
        return mass * material.cost_per_kg


# Global material database instance
material_db = MaterialDatabase()


def get_material_properties(name: str) -> Optional[MaterialProperties]:
    """Convenience function to get material properties."""
    return material_db.get_material(name)


def calculate_bottle_mass(diameter: float, length: float, wall_thickness: float,
                         material_name: str = 'PET') -> float:
    """
    Calculate mass of a bottle.
    
    Args:
        diameter: Bottle diameter (m)
        length: Bottle length (m)
        wall_thickness: Wall thickness (m)
        material_name: Material name
        
    Returns:
        Bottle mass (kg)
    """
    material = get_material_properties(material_name)
    if not material:
        raise ValueError(f"Unknown material: {material_name}")
    
    # Calculate volume of material (approximation for thin walls)
    outer_radius = diameter / 2
    inner_radius = outer_radius - wall_thickness
    
    # Volume of cylindrical shell
    volume = np.pi * length * (outer_radius**2 - inner_radius**2)
    
    # Add volume for bottle ends (approximate as flat discs)
    end_volume = 2 * np.pi * wall_thickness * (outer_radius**2 - inner_radius**2)
    
    total_volume = volume + end_volume
    
    return StructuralAnalysis.calculate_mass(total_volume, material)