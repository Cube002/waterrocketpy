# waterrocketpy/core/simulation.py
"""
Main simulation engine for water rocket flight.
"""

import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Any, Tuple, NamedTuple
from dataclasses import dataclass

from .physics_engine import PhysicsEngine
from .validation import ParameterValidator
from .constants import (
    WATER_DENSITY, DEFAULT_TIME_STEP, DEFAULT_MAX_TIME, 
    DEFAULT_SOLVER, INITIAL_TEMPERATURE, ATMOSPHERIC_PRESSURE
)


@dataclass
class FlightData:
    """Container for flight simulation results."""
    time: np.ndarray
    altitude: np.ndarray
    velocity: np.ndarray
    acceleration: np.ndarray
    water_mass: np.ndarray
    liquid_gas_mass: np.ndarray
    pressure: np.ndarray
    temperature: np.ndarray
    thrust: np.ndarray
    drag: np.ndarray
    max_altitude: float
    max_velocity: float
    flight_time: float
    water_depletion_time: float


class WaterRocketSimulator:
    """Main simulation class for water rocket flight."""
    
    def __init__(self, physics_engine: PhysicsEngine = None):
        self.physics_engine = physics_engine or PhysicsEngine()
        self.validator = ParameterValidator()
    
    def _rocket_ode(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """
        ODE system for rocket dynamics.
        
        Args:
            t: Current time
            state: [altitude, velocity, water_mass, liquid_gas_mass]
            params: Rocket parameters
            
        Returns:
            Derivatives [velocity, acceleration, dm_water/dt, dm_gas/dt]
        """
        altitude, velocity, water_mass, liquid_gas_mass = state
        
        # Calculate current air volume
        air_volume = self.physics_engine.calculate_air_volume(params['V_bottle'], water_mass)
        
        # Calculate pressure
        if water_mass > 0 and liquid_gas_mass > 0:
            # Pressure from vaporizing liquid gas (constant while liquid remains)
            pressure = 10e5  # 10 bar in Pa
            dm_dt_liquid_gas = 0  # Simplified: no vaporization rate calculation
        else:
            dm_dt_liquid_gas = 0
            if water_mass > 0:
                # Adiabatic expansion
                initial_air_volume = params['V_bottle'] * (1 - params['water_fraction'])
                pressure = self.physics_engine.calculate_pressure_adiabatic(
                    params['P0'], initial_air_volume, air_volume
                )
            else:
                pressure = ATMOSPHERIC_PRESSURE
        
        # Calculate thrust and mass flow rate
        if water_mass > 0:
            thrust, exit_velocity, mass_flow_rate = self.physics_engine.calculate_thrust(
                pressure, params['A_nozzle'], params['C_d']
            )
            dm_dt_water = -mass_flow_rate
        else:
            thrust = 0
            dm_dt_water = 0
        
        # Calculate drag
        drag = self.physics_engine.calculate_drag(
            velocity, params['C_drag'], params['A_rocket']
        )
        
        # Calculate acceleration
        total_mass = params['m_empty'] + water_mass
        _, acceleration = self.physics_engine.calculate_net_force(thrust, drag, total_mass)
        
        return np.array([velocity, acceleration, dm_dt_water, dm_dt_liquid_gas])
    
    def _water_depletion_event(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> float:
        """Event function to detect water depletion."""
        return state[2]  # water_mass
    
    def _setup_events(self, params: Dict[str, Any]):
        """Setup event functions for simulation."""
        def water_depletion(t, state, *args):       #added a third argument 10.07.2025
            return self._water_depletion_event(t, state, params)
                
        water_depletion.terminal = True
        water_depletion.direction = -1
        
        return [water_depletion]
    
    def simulate(self, rocket_params: Dict[str, Any], 
                sim_params: Dict[str, Any] = None) -> FlightData:
        """
        Run complete water rocket simulation.
        
        Args:
            rocket_params: Rocket configuration parameters
            sim_params: Simulation parameters (optional)
            
        Returns:
            FlightData object with simulation results
        """
        # Validate parameters
        warnings = self.validator.validate_rocket_parameters(rocket_params)
        if warnings:
            print("Warnings:", warnings)
        
        # Set default simulation parameters
        if sim_params is None:
            sim_params = {}
        
        max_time = sim_params.get('max_time', DEFAULT_MAX_TIME)
        time_step = sim_params.get('time_step', DEFAULT_TIME_STEP)
        solver = sim_params.get('solver', DEFAULT_SOLVER)
        
        # Initial conditions
        water_volume_initial = rocket_params['V_bottle'] * rocket_params['water_fraction']
        water_mass_initial = WATER_DENSITY * water_volume_initial
        liquid_gas_mass_initial = rocket_params.get('liquid_gas_mass', 0.0)
        
        initial_state = np.array([0.0, 0.0, water_mass_initial, liquid_gas_mass_initial])
        time_span = (0, max_time)
        
        # Setup events
        events = self._setup_events(rocket_params)
        
        # Solve thrust phase
        solution_thrust = solve_ivp(
            self._rocket_ode,
            time_span,
            initial_state,
            args=(rocket_params,),
            events=events,
            max_step=time_step,
            method=solver,
            rtol=1e-8,
            atol=1e-10
        )
        
        # Check if water depleted during simulation
        water_depletion_time = None
        if solution_thrust.t_events[0].size > 0:
            water_depletion_time = solution_thrust.t_events[0][0]
            
            # Continue simulation for coasting phase
            final_state = solution_thrust.y[:, -1]
            coasting_initial = np.array([final_state[0], final_state[1], 0.0, 0.0])
            
            solution_coasting = solve_ivp(
                self._rocket_ode,
                (water_depletion_time, max_time),
                coasting_initial,
                args=(rocket_params,),
                max_step=time_step,
                method=solver,
                rtol=1e-8,
                atol=1e-10
            )
            
            # Combine solutions
            time = np.concatenate((solution_thrust.t, solution_coasting.t))
            states = np.hstack((solution_thrust.y, solution_coasting.y))
        else:
            time = solution_thrust.t
            states = solution_thrust.y
        
        # Calculate additional quantities
        pressure, temperature, thrust, drag = self._calculate_derived_quantities(
            time, states, rocket_params
        )
        
        # Calculate accelerations
        acceleration = np.gradient(states[1, :], time)
        
        # Create flight data object
        flight_data = FlightData(
            time=time,
            altitude=states[0, :],
            velocity=states[1, :],
            acceleration=acceleration,
            water_mass=states[2, :],
            liquid_gas_mass=states[3, :],
            pressure=pressure,
            temperature=temperature,
            thrust=thrust,
            drag=drag,
            max_altitude=np.max(states[0, :]),
            max_velocity=np.max(states[1, :]),
            flight_time=time[-1],
            water_depletion_time=water_depletion_time or 0.0
        )
        
        return flight_data
    
    def _calculate_derived_quantities(self, time: np.ndarray, states: np.ndarray, 
                                    params: Dict[str, Any]) -> Tuple[np.ndarray, ...]:
        """Calculate pressure, temperature, thrust, and drag over time."""
        pressure = np.zeros_like(time)
        temperature = np.zeros_like(time)
        thrust = np.zeros_like(time)
        drag = np.zeros_like(time)
        
        initial_air_volume = params['V_bottle'] * (1 - params['water_fraction'])
        
        for i in range(len(time)):
            water_mass = states[2, i]
            liquid_gas_mass = states[3, i]
            velocity = states[1, i]
            
            # Calculate air volume
            air_volume = self.physics_engine.calculate_air_volume(params['V_bottle'], water_mass)
            
            # Calculate pressure
            if liquid_gas_mass > 0:
                pressure[i] = 10e5  # 10 bar
                temperature[i] = INITIAL_TEMPERATURE
            elif water_mass > 0:
                pressure[i] = self.physics_engine.calculate_pressure_adiabatic(
                    params['P0'], initial_air_volume, air_volume
                )
                temperature[i] = self.physics_engine.calculate_temperature_adiabatic(
                    INITIAL_TEMPERATURE, params['P0'], pressure[i]
                )
            else:
                pressure[i] = ATMOSPHERIC_PRESSURE
                temperature[i] = self.physics_engine.calculate_temperature_adiabatic(
                    INITIAL_TEMPERATURE, params['P0'], pressure[i]
                )
            
            # Calculate thrust
            if water_mass > 0:
                thrust[i], _, _ = self.physics_engine.calculate_thrust(
                    pressure[i], params['A_nozzle'], params['C_d']
                )
            
            # Calculate drag
            drag[i] = self.physics_engine.calculate_drag(
                velocity, params['C_drag'], params['A_rocket']
            )
        
        return pressure, temperature, thrust, drag