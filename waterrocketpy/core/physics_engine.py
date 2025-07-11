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
        self.air_gas_constant = 287.0  # J/(kg·K) for air
    
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
    
    def calculate_air_thrust(self, pressure, temperature, nozzle_area, discharge_coefficient):
        """
        Calculate thrust force from air expulsion through converging nozzle.
        
        Args:
            pressure (float): Internal pressure (Pa)
            temperature (float): Internal temperature (K)
            nozzle_area (float): Nozzle cross-sectional area (m²)
            discharge_coefficient (float): Discharge coefficient
            
        Returns:
            tuple: (thrust_force, exit_velocity, mass_flow_rate)
        """
        if pressure <= ATMOSPHERIC_PRESSURE:
            return 0.0, 0.0, 0.0
        
        gamma = ADIABATIC_INDEX_AIR
        R = self.air_gas_constant
        
        # Critical pressure ratio for choked flow
        pressure_ratio_critical = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
        pressure_ratio = pressure / ATMOSPHERIC_PRESSURE
        
        # Check if flow is choked
        if pressure_ratio > pressure_ratio_critical:
            # Choked flow - sonic at throat
            
            # Throat conditions (sonic)
            T_throat = temperature * (2 / (gamma + 1))
            P_throat = pressure * (2 / (gamma + 1)) ** (gamma / (gamma - 1))
            rho_throat = P_throat / (R * T_throat)
            
            # Sonic velocity at throat
            v_throat = np.sqrt(gamma * R * T_throat)
            
            # Mass flow rate (choked)
            mass_flow_rate = discharge_coefficient * rho_throat * nozzle_area * v_throat
            
            # For converging nozzle, exit conditions = throat conditions
            exit_velocity = v_throat
            exit_pressure = P_throat
            
        else:
            # Subsonic flow - exit pressure = ambient pressure
            exit_pressure = ATMOSPHERIC_PRESSURE
            
            # Isentropic relations for exit conditions
            pressure_ratio_exit = exit_pressure / pressure
            T_exit = temperature * (pressure_ratio_exit ** ((gamma - 1) / gamma))
            rho_exit = exit_pressure / (R * T_exit)
            
            # Exit velocity from isentropic relations
            exit_velocity = np.sqrt(2 * gamma * R * temperature / (gamma - 1) *  #TODO woher kommt das /(gamma-1) her - überprüfe die gleichungen
                                  (1 - pressure_ratio_exit ** ((gamma - 1) / gamma)))
            
            # Mass flow rate
            mass_flow_rate = discharge_coefficient * rho_exit * nozzle_area * exit_velocity
        
        # Thrust force (momentum + pressure thrust)
        momentum_thrust = mass_flow_rate * exit_velocity
        pressure_thrust = nozzle_area * (exit_pressure - ATMOSPHERIC_PRESSURE)
        thrust_force = momentum_thrust + pressure_thrust
        
        return thrust_force, exit_velocity, mass_flow_rate
    
    def calculate_air_mass_flow_rate(self, pressure, temperature, air_volume, nozzle_area, discharge_coefficient):
        """
        Calculate air mass flow rate and resulting pressure change.
        
        Args:
            pressure (float): Current pressure (Pa)
            temperature (float): Current temperature (K)
            air_volume (float): Current air volume (m³)
            nozzle_area (float): Nozzle area (m²)
            discharge_coefficient (float): Discharge coefficient
            
        Returns:
            float: Mass flow rate (kg/s)
        """
        if pressure <= ATMOSPHERIC_PRESSURE:
            return 0.0
        
        # Get mass flow rate from air thrust calculation
        _, _, mass_flow_rate = self.calculate_air_thrust(
            pressure, temperature, nozzle_area, discharge_coefficient
        )
        
        return mass_flow_rate
    
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
    
    def calculate_air_mass_from_conditions(self, pressure, temperature, volume):
        """
        Calculate air mass from thermodynamic conditions.
        
        Args:
            pressure (float): Pressure (Pa)
            temperature (float): Temperature (K)
            volume (float): Volume (m³)
            
        Returns:
            float: Air mass (kg)
        """
        # Using ideal gas law: PV = mRT/M, so m = PV*M/(RT)
        # For air, M/R = 1/R_specific where R_specific = 287 J/(kg·K)
        return pressure * volume / (self.air_gas_constant * temperature)
    
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