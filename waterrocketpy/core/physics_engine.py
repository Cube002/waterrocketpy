# waterrocketpy/core/physics_engine.py
"""
Physics calculations for water rocket simulation.
"""

import numpy as np
from .constants import (
    GRAVITY, WATER_DENSITY, AIR_DENSITY_SL, ATMOSPHERIC_PRESSURE,
    ADIABATIC_INDEX_AIR, INITIAL_TEMPERATURE
)


class PhysicsEngine:
    """Handles all physics calculations for water rocket simulation."""
    
    def __init__(self, gravity=GRAVITY, air_density=AIR_DENSITY_SL):
        self.gravity = gravity
        self.air_density = air_density
    
    def calculate_thrust(self, pressure, nozzle_area, discharge_coefficient):
        """
        Calculate thrust force from water expulsion.
        
        Args:
            pressure (float): Internal pressure (Pa)
            nozzle_area (float): Nozzle cross-sectional area (m²)
            discharge_coefficient (float): Discharge coefficient
            
        Returns:
            tuple: (thrust_force, exit_velocity, mass_flow_rate)
        """
        pressure_diff = max(pressure - ATMOSPHERIC_PRESSURE, 0)
        
        # Exit velocity using Torricelli's equation
        exit_velocity = discharge_coefficient * np.sqrt(2 * pressure_diff / WATER_DENSITY)
        
        # Mass flow rate
        mass_flow_rate = WATER_DENSITY * nozzle_area * exit_velocity
        
        # Thrust force
        thrust_force = mass_flow_rate * exit_velocity
        
        return thrust_force, exit_velocity, mass_flow_rate
    
    def calculate_drag(self, velocity, drag_coefficient, cross_sectional_area):
        """
        Calculate drag force on the rocket.
        
        Args:
            velocity (float): Rocket velocity (m/s)
            drag_coefficient (float): Drag coefficient
            cross_sectional_area (float): Cross-sectional area (m²)
            
        Returns:
            float: Drag force (N)
        """
        return 0.5 * self.air_density * velocity**2 * drag_coefficient * cross_sectional_area * np.sign(velocity)
    
    def calculate_pressure_adiabatic(self, initial_pressure, initial_volume, current_volume):
        """
        Calculate pressure during adiabatic expansion.
        
        Args:
            initial_pressure (float): Initial pressure (Pa)
            initial_volume (float): Initial air volume (m³)
            current_volume (float): Current air volume (m³)
            
        Returns:
            float: Current pressure (Pa)
        """
        if current_volume <= 0:
            return initial_pressure
        
        return initial_pressure * (initial_volume / current_volume) ** ADIABATIC_INDEX_AIR
    
    def calculate_temperature_adiabatic(self, initial_temperature, initial_pressure, current_pressure):
        """
        Calculate temperature during adiabatic expansion.
        
        Args:
            initial_temperature (float): Initial temperature (K)
            initial_pressure (float): Initial pressure (Pa)
            current_pressure (float): Current pressure (Pa)
            
        Returns:
            float: Current temperature (K)
        """
        return initial_temperature * (current_pressure / initial_pressure) ** ((ADIABATIC_INDEX_AIR - 1) / ADIABATIC_INDEX_AIR)
    
    def calculate_air_volume(self, bottle_volume, water_mass):
        """
        Calculate current air volume in the bottle.
        
        Args:
            bottle_volume (float): Total bottle volume (m³)
            water_mass (float): Current water mass (kg)
            
        Returns:
            float: Air volume (m³)
        """
        water_volume = water_mass / WATER_DENSITY
        air_volume = bottle_volume - water_volume
        return max(air_volume, 1e-10)  # Prevent division by zero
    
    def calculate_net_force(self, thrust, drag, mass):
        """
        Calculate net force and acceleration.
        
        Args:
            thrust (float): Thrust force (N)
            drag (float): Drag force (N)
            mass (float): Total rocket mass (kg)
            
        Returns:
            tuple: (net_force, acceleration)
        """
        net_force = thrust - drag
        acceleration = net_force / mass - self.gravity
        return net_force, acceleration