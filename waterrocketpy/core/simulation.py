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
    DEFAULT_SOLVER, INITIAL_TEMPERATURE, ATMOSPHERIC_PRESSURE, ADIABATIC_INDEX_AIR
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
    air_mass: np.ndarray
    pressure: np.ndarray
    temperature: np.ndarray
    thrust: np.ndarray
    drag: np.ndarray
    max_altitude: float
    max_velocity: float
    flight_time: float
    water_depletion_time: float
    air_depletion_time: float


class WaterRocketSimulator:
    """Main simulation class for water rocket flight."""
    
    def __init__(self, physics_engine: PhysicsEngine = None):
        self.physics_engine = physics_engine or PhysicsEngine()
        self.validator = ParameterValidator()
    
    def _rocket_ode_water_phase(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """
        ODE system for rocket dynamics during water expulsion phase.
        
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
    
    def _rocket_ode_air_phase(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """
        ODE system for rocket dynamics during air expulsion phase.
        
        Args:
            t: Current time
            state: [altitude, velocity, air_mass, temperature]
            params: Rocket parameters
            
        Returns:
            Derivatives [velocity, acceleration, dm_air/dt, dT/dt]
        """
        altitude, velocity, air_mass, temperature = state
        
        if air_mass <= 0:
            return np.array([velocity, -self.physics_engine.gravity, 0, 0])
        
        # Calculate current air volume and pressure
        air_volume = params['V_bottle']  # All bottle volume is now air
        # pressure = self.physics_engine.calculate_air_mass_from_conditions(
        #     ATMOSPHERIC_PRESSURE, temperature, air_volume
        # )
        
        # Calculate pressure from ideal gas law: P = mRT/V
        pressure = air_mass * self.physics_engine.air_gas_constant * temperature / air_volume
        
        # Ensure pressure doesn't go below atmospheric
        pressure = max(pressure, ATMOSPHERIC_PRESSURE)
        
        # Calculate air thrust and mass flow rate
        if pressure > ATMOSPHERIC_PRESSURE:
            thrust, exit_velocity, mass_flow_rate = self.physics_engine.calculate_air_thrust(
                pressure, temperature, params['A_nozzle'], params['C_d']
            )
            dm_dt_air = -mass_flow_rate
            
            # Calculate temperature change due to adiabatic expansion
            # For adiabatic process: TV^(γ-1) = constant
            # dT/dt = -T * (γ-1)/V * dV/dt
            # dV/dt = (dm/dt) * RT/(P*M) = (dm/dt) * R_specific * T / P
            dV_dt = dm_dt_air * self.physics_engine.air_gas_constant * temperature / pressure
            dT_dt = -temperature * (ADIABATIC_INDEX_AIR - 1) / air_volume * dV_dt
        else:
            thrust = 0
            dm_dt_air = 0
            dT_dt = 0
        
        # Calculate drag
        drag = self.physics_engine.calculate_drag(
            velocity, params['C_drag'], params['A_rocket']
        )
        
        # Calculate acceleration
        total_mass = params['m_empty'] + air_mass
        _, acceleration = self.physics_engine.calculate_net_force(thrust, drag, total_mass)
        
        return np.array([velocity, acceleration, dm_dt_air, dT_dt])
    
    def _rocket_ode_coasting_phase(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """
        ODE system for rocket dynamics during coasting phase.
        
        Args:
            t: Current time
            state: [altitude, velocity]
            params: Rocket parameters
            
        Returns:
            Derivatives [velocity, acceleration]
        """
        altitude, velocity = state
        
        # Only drag and gravity forces
        drag = self.physics_engine.calculate_drag(
            velocity, params['C_drag'], params['A_rocket']
        )
        
        # Calculate acceleration
        total_mass = params['m_empty']
        _, acceleration = self.physics_engine.calculate_net_force(0, drag, total_mass)
        
        return np.array([velocity, acceleration])
    
    def _water_depletion_event(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> float:
        """Event function to detect water depletion."""
        return state[2]  # water_mass
    
    def _air_depletion_event(self, t: float, state: np.ndarray, params: Dict[str, Any]) -> float:
        """Event function to detect air depletion (pressure = atmospheric)."""
        if len(state) < 4:
            return 1.0  # Not in air phase
        
        altitude, velocity, air_mass, temperature = state
        if air_mass <= 0:
            return 0.0
        
        # Calculate pressure
        air_volume = params['V_bottle']
        pressure = air_mass * self.physics_engine.air_gas_constant * temperature / air_volume
        
        return pressure - ATMOSPHERIC_PRESSURE
    
    def _setup_water_events(self, params: Dict[str, Any]):
        """Setup event functions for water phase simulation."""
        def water_depletion(t, state, *args):
            return self._water_depletion_event(t, state, params)
                
        water_depletion.terminal = True
        water_depletion.direction = -1
        
        return [water_depletion]
    
    def _setup_air_events(self, params: Dict[str, Any]):
        """Setup event functions for air phase simulation."""
        def air_depletion(t, state, *args):
            return self._air_depletion_event(t, state, params)
                
        air_depletion.terminal = True
        air_depletion.direction = -1
        
        return [air_depletion]
    
    def simulate(self, rocket_params: Dict[str, Any], 
                sim_params: Dict[str, Any] = None) -> FlightData:
        """
        Run complete water rocket simulation with three phases.
        
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
        
        # Initialize storage for all phases
        all_times = []
        all_altitudes = []
        all_velocities = []
        all_water_masses = []
        all_liquid_gas_masses = []
        all_air_masses = []
        all_pressures = []
        all_temperatures = []
        all_thrusts = []
        all_drags = []
        
        water_depletion_time = 0.0
        air_depletion_time = 0.0
        
        # Phase 1: Water expulsion phase
        print("Starting water expulsion phase...")
        water_volume_initial = rocket_params['V_bottle'] * rocket_params['water_fraction']
        water_mass_initial = WATER_DENSITY * water_volume_initial
        liquid_gas_mass_initial = rocket_params.get('liquid_gas_mass', 0.0)
        
        initial_state_water = np.array([0.0, 0.0, water_mass_initial, liquid_gas_mass_initial])
        time_span = (0, max_time)
        
        # Setup events for water phase
        water_events = self._setup_water_events(rocket_params)
        
        # Solve water phase
        solution_water = solve_ivp(
            self._rocket_ode_water_phase,
            time_span,
            initial_state_water,
            args=(rocket_params,),
            events=water_events,
            max_step=time_step,
            method=solver,
            rtol=1e-8,
            atol=1e-10
        )
        
        # Store water phase results
        all_times.append(solution_water.t)
        all_altitudes.append(solution_water.y[0, :])
        all_velocities.append(solution_water.y[1, :])
        all_water_masses.append(solution_water.y[2, :])
        all_liquid_gas_masses.append(solution_water.y[3, :])
        
        # Calculate air mass during water phase
        initial_air_volume = rocket_params['V_bottle'] * (1 - rocket_params['water_fraction'])
        initial_air_mass = self.physics_engine.calculate_air_mass_from_conditions(
            rocket_params['P0'], INITIAL_TEMPERATURE, initial_air_volume
        )
        air_masses_water_phase = np.full_like(solution_water.t, initial_air_mass)
        all_air_masses.append(air_masses_water_phase)
        
        # Phase 2: Air expulsion phase (if water depleted)
        if solution_water.t_events[0].size > 0:
            water_depletion_time = solution_water.t_events[0][0]
            print(f"Water depleted at t={water_depletion_time:.3f}s, starting air expulsion phase...")
            
            # Get final state from water phase
            final_state_water = solution_water.y[:, -1]
            
            # Calculate initial conditions for air phase
            final_altitude = final_state_water[0]
            final_velocity = final_state_water[1]
            
            # Calculate air mass and temperature at start of air phase
            air_volume_at_transition = rocket_params['V_bottle']
            initial_air_volume = rocket_params['V_bottle'] * (1 - rocket_params['water_fraction'])
            
            # Pressure at end of water phase
            pressure_at_transition = self.physics_engine.calculate_pressure_adiabatic(
                rocket_params['P0'], initial_air_volume, air_volume_at_transition
            )
            
            # Temperature at end of water phase
            temperature_at_transition = self.physics_engine.calculate_temperature_adiabatic(
                INITIAL_TEMPERATURE, rocket_params['P0'], pressure_at_transition
            )
            
            # Air mass at transition
            air_mass_at_transition = self.physics_engine.calculate_air_mass_from_conditions(
                pressure_at_transition, temperature_at_transition, air_volume_at_transition
            )
            
            initial_state_air = np.array([
                final_altitude, final_velocity, air_mass_at_transition, temperature_at_transition
            ])
            
            # Setup events for air phase
            air_events = self._setup_air_events(rocket_params)
            
            # Solve air phase
            solution_air = solve_ivp(
                self._rocket_ode_air_phase,
                (water_depletion_time, max_time),
                initial_state_air,
                args=(rocket_params,),
                events=air_events,
                max_step=time_step,
                method=solver,
                rtol=1e-8,
                atol=1e-10
            )
            
            # Store air phase results
            all_times.append(solution_air.t)
            all_altitudes.append(solution_air.y[0, :])
            all_velocities.append(solution_air.y[1, :])
            all_water_masses.append(np.zeros_like(solution_air.t))
            all_liquid_gas_masses.append(np.zeros_like(solution_air.t))
            all_air_masses.append(solution_air.y[2, :])
            
            # Phase 3: Coasting phase (if air depleted)
            if solution_air.t_events[0].size > 0:
                air_depletion_time = solution_air.t_events[0][0]
                print(f"Air depleted at t={air_depletion_time:.3f}s, starting coasting phase...")
                
                # Get final state from air phase
                final_state_air = solution_air.y[:, -1]
                final_altitude = final_state_air[0]
                final_velocity = final_state_air[1]
                
                initial_state_coasting = np.array([final_altitude, final_velocity])
                
                # Solve coasting phase
                solution_coasting = solve_ivp(
                    self._rocket_ode_coasting_phase,
                    (air_depletion_time, max_time),
                    initial_state_coasting,
                    args=(rocket_params,),
                    max_step=time_step,
                    method=solver,
                    rtol=1e-8,
                    atol=1e-10
                )
                
                # Store coasting phase results
                all_times.append(solution_coasting.t)
                all_altitudes.append(solution_coasting.y[0, :])
                all_velocities.append(solution_coasting.y[1, :])
                all_water_masses.append(np.zeros_like(solution_coasting.t))
                all_liquid_gas_masses.append(np.zeros_like(solution_coasting.t))
                all_air_masses.append(np.zeros_like(solution_coasting.t))
        
        # Combine all phases
        time = np.concatenate(all_times)
        altitude = np.concatenate(all_altitudes)
        velocity = np.concatenate(all_velocities)
        water_mass = np.concatenate(all_water_masses)
        liquid_gas_mass = np.concatenate(all_liquid_gas_masses)
        air_mass = np.concatenate(all_air_masses)
        
        # Calculate derived quantities for all phases
        pressure, temperature, thrust, drag = self._calculate_derived_quantities(
            time, altitude, velocity, water_mass, liquid_gas_mass, air_mass, rocket_params
        )
        
        # Calculate accelerations
        acceleration = np.gradient(velocity, time)
        
        # Create flight data object
        flight_data = FlightData(
            time=time,
            altitude=altitude,
            velocity=velocity,
            acceleration=acceleration,
            water_mass=water_mass,
            liquid_gas_mass=liquid_gas_mass,
            air_mass=air_mass,
            pressure=pressure,
            temperature=temperature,
            thrust=thrust,
            drag=drag,
            max_altitude=np.max(altitude),
            max_velocity=np.max(velocity),
            flight_time=time[-1],
            water_depletion_time=water_depletion_time,
            air_depletion_time=air_depletion_time
        )
        
        return flight_data
    
    def _calculate_derived_quantities(self, time: np.ndarray, altitude: np.ndarray, 
                                    velocity: np.ndarray, water_mass: np.ndarray,
                                    liquid_gas_mass: np.ndarray, air_mass: np.ndarray,
                                    params: Dict[str, Any]) -> Tuple[np.ndarray, ...]:
        """Calculate pressure, temperature, thrust, and drag over time."""
        pressure = np.zeros_like(time)
        temperature = np.zeros_like(time)
        thrust = np.zeros_like(time)
        drag = np.zeros_like(time)
        
        initial_air_volume = params['V_bottle'] * (1 - params['water_fraction'])
        
        for i in range(len(time)):
            water_mass_i = water_mass[i]
            liquid_gas_mass_i = liquid_gas_mass[i]
            air_mass_i = air_mass[i]
            velocity_i = velocity[i]
            
            # Calculate air volume
            air_volume = self.physics_engine.calculate_air_volume(params['V_bottle'], water_mass_i)
            
            # Calculate pressure and temperature
            if liquid_gas_mass_i > 0:
                pressure[i] = 10e5  # 10 bar
                temperature[i] = INITIAL_TEMPERATURE
            elif water_mass_i > 0:
                # Water expulsion phase
                pressure[i] = self.physics_engine.calculate_pressure_adiabatic(
                    params['P0'], initial_air_volume, air_volume
                )
                temperature[i] = self.physics_engine.calculate_temperature_adiabatic(
                    INITIAL_TEMPERATURE, params['P0'], pressure[i]
                )
            elif air_mass_i > 0:
                # Temperature calculated from previous time step in ODE
                if i > 0:
                    temperature[i] = temperature[i-1]
                else:
                    temperature[i] = self.physics_engine.calculate_temperature_adiabatic(
                        INITIAL_TEMPERATURE, params['P0'], pressure[i]
                    )
                # Air expulsion phase
                air_volume_full = params['V_bottle']
                pressure[i] = air_mass_i * self.physics_engine.air_gas_constant * temperature[i] / air_volume_full
                pressure[i] = max(pressure[i], ATMOSPHERIC_PRESSURE)
                
            else:
                # Coasting phase
                pressure[i] = ATMOSPHERIC_PRESSURE
                temperature[i] = INITIAL_TEMPERATURE
            
            # Calculate thrust
            if water_mass_i > 0:
                thrust[i], _, _ = self.physics_engine.calculate_thrust(
                    pressure[i], params['A_nozzle'], params['C_d']
                )
            elif air_mass_i > 0 and pressure[i] > ATMOSPHERIC_PRESSURE:
                thrust[i], _, _ = self.physics_engine.calculate_air_thrust(
                    pressure[i], temperature[i], params['A_nozzle'], params['C_d']
                )
            else:
                thrust[i] = 0
            
            # Calculate drag
            drag[i] = self.physics_engine.calculate_drag(
                velocity_i, params['C_drag'], params['A_rocket']
            )
        
        return pressure, temperature, thrust, drag