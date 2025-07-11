# waterrocketpy/rocket/geometry.py
"""
Geometric calculations for water rocket components.
"""

import numpy as np
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class GeometricProperties:
    """Container for geometric properties of rocket components."""
    volume: float
    surface_area: float
    center_of_mass: Tuple[float, float, float]
    center_of_pressure: Tuple[float, float, float]
    moment_of_inertia: Tuple[float, float, float]  # Ixx, Iyy, Izz


class RocketGeometry:
    """Geometric calculations for water rocket components."""
    
    @staticmethod
    def cylinder_volume(diameter: float, length: float) -> float:
        """Calculate volume of a cylinder."""
        radius = diameter / 2
        return np.pi * radius**2 * length
    
    @staticmethod
    def cylinder_surface_area(diameter: float, length: float, include_ends: bool = True) -> float:
        """Calculate surface area of a cylinder."""
        radius = diameter / 2
        lateral_area = 2 * np.pi * radius * length
        if include_ends:
            end_area = 2 * np.pi * radius**2
            return lateral_area + end_area
        return lateral_area
    
    @staticmethod
    def sphere_volume(diameter: float) -> float:
        """Calculate volume of a sphere."""
        radius = diameter / 2
        return (4/3) * np.pi * radius**3
    
    @staticmethod
    def sphere_surface_area(diameter: float) -> float:
        """Calculate surface area of a sphere."""
        radius = diameter / 2
        return 4 * np.pi * radius**2
    
    @staticmethod
    def cone_volume(diameter: float, height: float) -> float:
        """Calculate volume of a cone."""
        radius = diameter / 2
        return (1/3) * np.pi * radius**2 * height
    
    @staticmethod
    def cone_surface_area(diameter: float, height: float) -> float:
        """Calculate surface area of a cone."""
        radius = diameter / 2
        slant_height = np.sqrt(radius**2 + height**2)
        return np.pi * radius * slant_height + np.pi * radius**2
    
    @staticmethod
    def ellipsoid_volume(a: float, b: float, c: float) -> float:
        """Calculate volume of an ellipsoid."""
        return (4/3) * np.pi * a * b * c
    
    @staticmethod
    def bottle_volume(diameter: float, length: float, 
                     nose_cone_height: float = 0.0,
                     bottom_cone_height: float = 0.0) -> float:
        """
        Calculate total volume of a rocket bottle.
        
        Args:
            diameter: Bottle diameter
            length: Cylindrical section length
            nose_cone_height: Height of nose cone
            bottom_cone_height: Height of bottom cone
            
        Returns:
            Total volume
        """
        # Cylindrical section
        cylinder_vol = RocketGeometry.cylinder_volume(diameter, length)
        
        # Nose cone (if present)
        nose_vol = 0
        if nose_cone_height > 0:
            nose_vol = RocketGeometry.cone_volume(diameter, nose_cone_height)
        
        # Bottom cone (if present)
        bottom_vol = 0
        if bottom_cone_height > 0:
            bottom_vol = RocketGeometry.cone_volume(diameter, bottom_cone_height)
        
        return cylinder_vol + nose_vol + bottom_vol
    
    @staticmethod
    def calculate_center_of_mass(components: List[Dict[str, Any]]) -> Tuple[float, float, float]:
        """
        Calculate center of mass for multiple components.
        
        Args:
            components: List of component dictionaries with 'mass', 'position' keys
            
        Returns:
            Center of mass coordinates (x, y, z)
        """
        total_mass = 0
        weighted_position = np.array([0.0, 0.0, 0.0])
        
        for component in components:
            mass = component['mass']
            position = np.array(component['position'])
            
            total_mass += mass
            weighted_position += mass * position
        
        if total_mass == 0:
            return (0.0, 0.0, 0.0)
        
        center_of_mass = weighted_position / total_mass
        return tuple(center_of_mass)
    
    @staticmethod
    def calculate_center_of_pressure(fins: List[Dict[str, Any]], 
                                   body_cp: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Calculate center of pressure for rocket with fins.
        
        Args:
            fins: List of fin dictionaries with area and position
            body_cp: Center of pressure of the body
            
        Returns:
            Overall center of pressure
        """
        # Body contribution
        body_area = 1.0  # Normalized
        body_moment = np.array(body_cp) * body_area
        
        total_area = body_area
        total_moment = body_moment
        
        # Fin contributions
        for fin in fins:
            fin_area = fin['area']
            fin_position = np.array(fin['position'])
            
            total_area += fin_area
            total_moment += fin_area * fin_position
        
        if total_area == 0:
            return body_cp
        
        cp = total_moment / total_area
        return tuple(cp)
    
    @staticmethod
    def calculate_moment_of_inertia_cylinder(mass: float, radius: float, 
                                           length: float) -> Tuple[float, float, float]:
        """
        Calculate moment of inertia for a cylinder.
        
        Args:
            mass: Mass of cylinder
            radius: Radius of cylinder
            length: Length of cylinder
            
        Returns:
            Moments of inertia (Ixx, Iyy, Izz)
        """
        # For a cylinder with axis along z:
        # Ixx = Iyy = (1/12) * m * (3*r^2 + h^2)
        # Izz = (1/2) * m * r^2
        
        Ixx = Iyy = (1/12) * mass * (3 * radius**2 + length**2)
        Izz = 0.5 * mass * radius**2
        
        return (Ixx, Iyy, Izz)
    
    @staticmethod
    def calculate_stability_margin(center_of_mass: Tuple[float, float, float],
                                 center_of_pressure: Tuple[float, float, float],
                                 reference_length: float) -> float:
        """
        Calculate static stability margin.
        
        Args:
            center_of_mass: Center of mass position
            center_of_pressure: Center of pressure position
            reference_length: Reference length (typically rocket diameter)
            
        Returns:
            Stability margin (positive = stable)
        """
        # Calculate distance between CP and CG along rocket axis (typically x-axis)
        cp_x = center_of_pressure[0]
        cg_x = center_of_mass[0]
        
        # Stability margin in calibers (rocket diameters)
        stability_margin = (cp_x - cg_x) / reference_length
        
        return stability_margin
    
    @staticmethod
    def calculate_fin_properties(span: float, root_chord: float, 
                               tip_chord: float, sweep_angle: float = 0.0) -> Dict[str, float]:
        """
        Calculate properties of a trapezoidal fin.
        
        Args:
            span: Fin span (height)
            root_chord: Root chord length
            tip_chord: Tip chord length
            sweep_angle: Sweep angle in radians
            
        Returns:
            Dictionary with fin properties
        """
        # Area
        area = 0.5 * (root_chord + tip_chord) * span
        
        # Aspect ratio
        aspect_ratio = span**2 / area
        
        # Taper ratio
        taper_ratio = tip_chord / root_chord if root_chord > 0 else 0
        
        # Mean aerodynamic chord
        mac = (2/3) * root_chord * (1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)
        
        # Centroid position (from root leading edge)
        x_centroid = (root_chord + 2 * tip_chord) / (3 * (root_chord + tip_chord)) * root_chord
        y_centroid = span / 3 * (root_chord + 2 * tip_chord) / (root_chord + tip_chord)
        
        return {
            'area': area,
            'aspect_ratio': aspect_ratio,
            'taper_ratio': taper_ratio,
            'mac': mac,
            'centroid_x': x_centroid,
            'centroid_y': y_centroid
        }
    
    @staticmethod
    def calculate_rocket_wetted_area(diameter: float, length: float,
                                   nose_cone_height: float = 0.0,
                                   fin_area: float = 0.0) -> float:
        """
        Calculate total wetted area of rocket.
        
        Args:
            diameter: Rocket diameter
            length: Body length
            nose_cone_height: Nose cone height
            fin_area: Total fin area
            
        Returns:
            Total wetted area
        """
        # Body area
        body_area = RocketGeometry.cylinder_surface_area(diameter, length, include_ends=False)
        
        # Nose cone area
        nose_area = 0
        if nose_cone_height > 0:
            nose_area = RocketGeometry.cone_surface_area(diameter, nose_cone_height)
        
        # Base area
        base_area = np.pi * (diameter / 2)**2
        
        # Total wetted area (both sides of fins)
        total_area = body_area + nose_area + base_area + 2 * fin_area
        
        return total_area