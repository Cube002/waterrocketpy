# waterrocketpy/core/validation.py
"""
Validation functions for water rocket simulation parameters.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from .constants import (
    ATMOSPHERIC_PRESSURE, DEFAULT_BOTTLE_VOLUME, DEFAULT_WATER_FRACTION,
    DEFAULT_EMPTY_MASS, DEFAULT_DISCHARGE_COEFFICIENT, DEFAULT_DRAG_COEFFICIENT
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ParameterValidator:
    """Validates simulation and rocket parameters."""
    
    @staticmethod
    def validate_positive(value: float, name: str, min_value: float = 0) -> None:
        """Validate that a value is positive."""
        if value <= min_value:
            raise ValidationError(f"{name} must be greater than {min_value}, got {value}")
    
    @staticmethod
    def validate_range(value: float, name: str, min_val: float, max_val: float) -> None:
        """Validate that a value is within a specified range."""
        if not (min_val <= value <= max_val):
            raise ValidationError(f"{name} must be between {min_val} and {max_val}, got {value}")
    
    @staticmethod
    def validate_fraction(value: float, name: str) -> None:
        """Validate that a value is a valid fraction (0-1)."""
        ParameterValidator.validate_range(value, name, 0.0, 1.0)
    
    @staticmethod
    def validate_rocket_parameters(params: Dict[str, Any]) -> List[str]:
        """
        Validate rocket parameters and return list of warnings.
        
        Args:
            params: Dictionary of rocket parameters
            
        Returns:
            List of warning messages
            
        Raises:
            ValidationError: If critical parameters are invalid
        """
        warnings = []
        
        # Required parameters
        required_params = [
            'P0', 'A_nozzle', 'V_bottle', 'water_fraction', 
            'C_d', 'm_empty', 'C_drag', 'A_rocket'
        ]
        
        for param in required_params:
            if param not in params:
                raise ValidationError(f"Missing required parameter: {param}")
        
        # Validate pressure
        ParameterValidator.validate_positive(params['P0'], 'Initial pressure (P0)')
        if params['P0'] < ATMOSPHERIC_PRESSURE:
            warnings.append("Initial pressure is below atmospheric pressure")
        if params['P0'] > 50 * ATMOSPHERIC_PRESSURE:
            warnings.append("Initial pressure is very high (>50 bar) - safety concern")
        
        # Validate areas
        ParameterValidator.validate_positive(params['A_nozzle'], 'Nozzle area (A_nozzle)')
        ParameterValidator.validate_positive(params['A_rocket'], 'Rocket cross-sectional area (A_rocket)')
        
        # Validate volume
        ParameterValidator.validate_positive(params['V_bottle'], 'Bottle volume (V_bottle)')
        
        # Validate water fraction
        ParameterValidator.validate_fraction(params['water_fraction'], 'Water fraction')
        if params['water_fraction'] < 0.1:
            warnings.append("Water fraction is very low (<10%) - may result in poor performance")
        if params['water_fraction'] > 0.8:
            warnings.append("Water fraction is very high (>80%) - may result in poor performance")
        
        # Validate coefficients
        ParameterValidator.validate_range(params['C_d'], 'Discharge coefficient (C_d)', 0.1, 1.0)
        ParameterValidator.validate_range(params['C_drag'], 'Drag coefficient (C_drag)', 0.1, 2.0)
        
        # Validate mass
        ParameterValidator.validate_positive(params['m_empty'], 'Empty mass (m_empty)')
        
        # Check for reasonable values
        if params['C_d'] < 0.6:
            warnings.append("Discharge coefficient is low (<0.6) - check nozzle design")
        if params['C_drag'] > 1.5:
            warnings.append("Drag coefficient is high (>1.5) - check rocket aerodynamics")
        
        return warnings
    
    @staticmethod
    def validate_simulation_parameters(params: Dict[str, Any]) -> List[str]:
        """
        Validate simulation parameters.
        
        Args:
            params: Dictionary of simulation parameters
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if 'max_time' in params:
            ParameterValidator.validate_positive(params['max_time'], 'Maximum simulation time')
            if params['max_time'] > 60:
                warnings.append("Maximum simulation time is very long (>60s)")
        
        if 'time_step' in params:
            ParameterValidator.validate_positive(params['time_step'], 'Time step')
            if params['time_step'] > 0.1:
                warnings.append("Time step is large (>0.1s) - may affect accuracy")
            if params['time_step'] < 0.001:
                warnings.append("Time step is very small (<0.001s) - may be computationally expensive")
        
        return warnings
    
    @staticmethod
    def validate_flight_data(time: np.ndarray, altitude: np.ndarray, 
                           velocity: np.ndarray, mass: np.ndarray) -> bool:
        """
        Validate flight data for physical consistency.
        
        Args:
            time: Time array
            altitude: Altitude array
            velocity: Velocity array
            mass: Mass array
            
        Returns:
            bool: True if data is valid
        """
        # Check array lengths
        if not (len(time) == len(altitude) == len(velocity) == len(mass)):
            raise ValidationError("All flight data arrays must have the same length")
        
        # Check for NaN or infinite values
        for arr, name in [(time, 'time'), (altitude, 'altitude'), 
                         (velocity, 'velocity'), (mass, 'mass')]:
            if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                raise ValidationError(f"{name} array contains NaN or infinite values")
        
        # Check physical constraints
        if np.any(mass < 0):
            raise ValidationError("Mass cannot be negative")
        
        if np.any(altitude < 0):
            raise ValidationError("Altitude cannot be negative")
        
        # Check time monotonicity
        if not np.all(np.diff(time) > 0):
            raise ValidationError("Time array must be monotonically increasing")
        
        return True