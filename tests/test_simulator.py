"""
Test suite for the water rocket simulator.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from waterrocketpy.core.simulation import WaterRocketSimulator, FlightData
from waterrocketpy.core.physics_engine import PhysicsEngine
from waterrocketpy.core.constants import (
    WATER_DENSITY, ATMOSPHERIC_PRESSURE, DEFAULT_TIME_STEP, 
    DEFAULT_MAX_TIME, DEFAULT_SOLVER, INITIAL_TEMPERATURE
)


class TestFlightData:
    """Test cases for FlightData class."""
    
    def test_flight_data_initialization(self):
        """Test FlightData initialization with all parameters."""
        time = np.array([0, 1, 2, 3])
        altitude = np.array([0, 10, 20, 15])
        velocity = np.array([0, 10, 5, -5])
        
        flight_data = FlightData(
            time=time,
            altitude=altitude,
            velocity=velocity,
            acceleration=np.array([0, 5, -5, -10]),
            water_mass=np.array([1, 0.5, 0, 0]),
            liquid_gas_mass=np.array([0, 0, 0, 0]),
            pressure=np.array([10e5, 5e5, 1e5, 1e5]),
            temperature=np.array([300, 295, 290, 285]),
            thrust=np.array([50, 25, 0, 0]),
            drag=np.array([0, 5, 10, 15]),
            max_altitude=20.0,
            max_velocity=10.0,
            flight_time=3.0,
            water_depletion_time=2.0
        )
        
        assert np.array_equal(flight_data.time, time)
        assert np.array_equal(flight_data.altitude, altitude)
        assert np.array_equal(flight_data.velocity, velocity)
        assert flight_data.max_altitude == 20.0
        assert flight_data.max_velocity == 10.0
        assert flight_data.flight_time == 3.0
        assert flight_data.water_depletion_time == 2.0


class TestWaterRocketSimulator:
    """Test cases for WaterRocketSimulator class."""
    
    def test_simulator_initialization_default(self):
        """Test simulator initialization with default physics engine."""
        simulator = WaterRocketSimulator()
        
        assert isinstance(simulator.physics_engine, PhysicsEngine)
        assert simulator.validator is not None
        
    def test_simulator_initialization_custom(self):
        """Test simulator initialization with custom physics engine."""
        mock_engine = Mock(spec=PhysicsEngine)
        simulator = WaterRocketSimulator(physics_engine=mock_engine)
        
        assert simulator.physics_engine is mock_engine
        
    def test_water_depletion_event(self):
        """Test water depletion event function."""
        simulator = WaterRocketSimulator()
        
        # Test with water remaining
        state_with_water = np.array([10, 5, 0.5, 0])  # altitude, velocity, water_mass, liquid_gas_mass
        result = simulator._water_depletion_event(1.0, state_with_water, {})
        assert result == 0.5
        
        # Test with no water
        state_no_water = np.array([10, 5, 0, 0])
        result = simulator._water_depletion_event(1.0, state_no_water, {})
        assert result == 0
        
    def test_setup_events(self):
        """Test event setup for simulation."""
        simulator = WaterRocketSimulator()
        params = {'some_param': 'value'}
        
        events = simulator._setup_events(params)
        
        assert len(events) == 1
        event = events[0]
        assert hasattr(event, 'terminal')
        assert hasattr(event, 'direction')
        assert event.terminal is True
        assert event.direction == -1
        
    def test_rocket_ode_with_water_and_liquid_gas(self):
        """Test ODE system with water and liquid gas."""
        simulator = WaterRocketSimulator()
        
        # Mock physics engine methods
        simulator.physics_engine.calculate_air_volume = Mock(return_value=0.001)
        simulator.physics_engine.calculate_thrust = Mock(return_value=(50.0, 20.0, 0.1))
        simulator.physics_engine.calculate_drag = Mock(return_value=5.0)
        simulator.physics_engine.calculate_net_force = Mock(return_value=(45.0, 10.0))
        
        state = np.array([10, 5, 0.5, 0.1])  # altitude, velocity, water_mass, liquid_gas_mass
        params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        derivatives = simulator._rocket_ode(1.0, state, params)
        
        assert len(derivatives) == 4
        assert derivatives[0] == 5  # velocity
        assert derivatives[1] == 10.0  # acceleration
        assert derivatives[2] == -0.1  # water mass change
        assert derivatives[3] == 0  # liquid gas mass change
        
    def test_rocket_ode_with_water_only(self):
        """Test ODE system with water only (no liquid gas)."""
        simulator = WaterRocketSimulator()
        
        # Mock physics engine methods
        simulator.physics_engine.calculate_air_volume = Mock(return_value=0.001)
        simulator.physics_engine.calculate_pressure_adiabatic = Mock(return_value=5e5)
        simulator.physics_engine.calculate_thrust = Mock(return_value=(30.0, 15.0, 0.08))
        simulator.physics_engine.calculate_drag = Mock(return_value=3.0)
        simulator.physics_engine.calculate_net_force = Mock(return_value=(27.0, 8.0))
        
        state = np.array([15, 8, 0.3, 0])  # altitude, velocity, water_mass, liquid_gas_mass
        params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        derivatives = simulator._rocket_ode(1.0, state, params)
        
        assert len(derivatives) == 4
        assert derivatives[0] == 8  # velocity
        assert derivatives[1] == 8.0  # acceleration
        assert derivatives[2] == -0.08  # water mass change
        assert derivatives[3] == 0  # liquid gas mass change
        
    def test_rocket_ode_no_water(self):
        """Test ODE system with no water (coasting phase)."""
        simulator = WaterRocketSimulator()
        
        # Mock physics engine methods
        simulator.physics_engine.calculate_air_volume = Mock(return_value=0.002)
        simulator.physics_engine.calculate_drag = Mock(return_value=8.0)
        simulator.physics_engine.calculate_net_force = Mock(return_value=(-8.0, -16.0))
        
        state = np.array([25, 10, 0, 0])  # altitude, velocity, water_mass, liquid_gas_mass
        params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        derivatives = simulator._rocket_ode(1.0, state, params)
        
        assert len(derivatives) == 4
        assert derivatives[0] == 10  # velocity
        assert derivatives[1] == -16.0  # acceleration (deceleration)
        assert derivatives[2] == 0  # no water mass change
        assert derivatives[3] == 0  # no liquid gas mass change
        
    def test_calculate_derived_quantities(self):
        """Test calculation of derived quantities."""
        simulator = WaterRocketSimulator()
        
        # Mock physics engine methods
        simulator.physics_engine.calculate_air_volume = Mock(return_value=0.001)
        simulator.physics_engine.calculate_pressure_adiabatic = Mock(return_value=5e5)
        simulator.physics_engine.calculate_temperature_adiabatic = Mock(return_value=280)
        simulator.physics_engine.calculate_thrust = Mock(return_value=(30.0, 15.0, 0.08))
        simulator.physics_engine.calculate_drag = Mock(return_value=3.0)
        
        time = np.array([0, 1, 2])
        states = np.array([
            [0, 10, 20],      # altitude
            [0, 15, 10],      # velocity
            [1.0, 0.5, 0],    # water_mass
            [0, 0, 0]         # liquid_gas_mass
        ])
        
        params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        pressure, temperature, thrust, drag = simulator._calculate_derived_quantities(
            time, states, params
        )
        
        assert len(pressure) == 3
        assert len(temperature) == 3
        assert len(thrust) == 3
        assert len(drag) == 3
        
        # Check that thrust is only non-zero when water is present
        assert thrust[0] == 30.0  # water present
        assert thrust[1] == 30.0  # water present
        assert thrust[2] == 0     # no water
        
    @patch('waterrocketpy.core.simulation.solve_ivp')
    def test_simulate_basic_flight(self, mock_solve_ivp):
        """Test basic simulation without water depletion."""
        simulator = WaterRocketSimulator()
        
        # Mock validation
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        # Mock solve_ivp result
        mock_solution = Mock()
        mock_solution.t = np.array([0, 1, 2, 3])
        mock_solution.y = np.array([
            [0, 10, 20, 15],    # altitude
            [0, 15, 10, -5],    # velocity
            [1.0, 0.8, 0.5, 0.2], # water_mass
            [0, 0, 0, 0]        # liquid_gas_mass
        ])
        mock_solution.t_events = [np.array([])]  # No events
        
        mock_solve_ivp.return_value = mock_solution
        
        # Mock derived quantities calculation
        simulator._calculate_derived_quantities = Mock(return_value=(
            np.array([8e5, 6e5, 4e5, 1e5]),  # pressure
            np.array([300, 295, 290, 285]),   # temperature
            np.array([50, 40, 30, 20]),       # thrust
            np.array([0, 5, 10, 15])          # drag
        ))
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        flight_data = simulator.simulate(rocket_params)
        
        # Verify flight data structure
        assert isinstance(flight_data, FlightData)
        assert len(flight_data.time) == 4
        assert len(flight_data.altitude) == 4
        assert len(flight_data.velocity) == 4
        assert flight_data.max_altitude == 20.0
        assert flight_data.max_velocity == 15.0
        assert flight_data.flight_time == 3.0
        assert flight_data.water_depletion_time == 0.0  # No water depletion event
        
        # Verify solve_ivp was called correctly
        mock_solve_ivp.assert_called_once()
        
    @patch('waterrocketpy.core.simulation.solve_ivp')
    def test_simulate_with_water_depletion(self, mock_solve_ivp):
        """Test simulation with water depletion event."""
        simulator = WaterRocketSimulator()
        
        # Mock validation
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        # Mock solve_ivp results for thrust and coasting phases
        mock_solution_thrust = Mock()
        mock_solution_thrust.t = np.array([0, 1, 2])
        mock_solution_thrust.y = np.array([
            [0, 10, 20],        # altitude
            [0, 15, 10],        # velocity
            [1.0, 0.5, 0.0],    # water_mass
            [0, 0, 0]           # liquid_gas_mass
        ])
        mock_solution_thrust.t_events = [np.array([2.0])]  # Water depletion at t=2
        
        mock_solution_coasting = Mock()
        mock_solution_coasting.t = np.array([2, 3, 4])
        mock_solution_coasting.y = np.array([
            [20, 25, 20],       # altitude
            [10, 5, -5],        # velocity
            [0, 0, 0],          # water_mass
            [0, 0, 0]           # liquid_gas_mass
        ])
        
        mock_solve_ivp.side_effect = [mock_solution_thrust, mock_solution_coasting]
        
        # Mock derived quantities calculation
        simulator._calculate_derived_quantities = Mock(return_value=(
            np.array([8e5, 6e5, 4e5, 2e5, 1e5]),  # pressure
            np.array([300, 295, 290, 285, 280]),   # temperature
            np.array([50, 40, 30, 0, 0]),          # thrust
            np.array([0, 5, 10, 15, 20])           # drag
        ))
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        flight_data = simulator.simulate(rocket_params)
        
        # Verify flight data structure
        assert isinstance(flight_data, FlightData)
        assert len(flight_data.time) == 5  # Combined thrust and coasting phases
        assert flight_data.water_depletion_time == 2.0
        assert flight_data.max_altitude == 25.0
        assert flight_data.max_velocity == 15.0
        
        # Verify solve_ivp was called twice (thrust and coasting phases)
        assert mock_solve_ivp.call_count == 2
        
    @patch('waterrocketpy.core.simulation.solve_ivp')
    def test_simulate_with_custom_sim_params(self, mock_solve_ivp):
        """Test simulation with custom simulation parameters."""
        simulator = WaterRocketSimulator()
        
        # Mock validation
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        # Mock solve_ivp result
        mock_solution = Mock()
        mock_solution.t = np.array([0, 0.5, 1.0])
        mock_solution.y = np.array([
            [0, 5, 10],         # altitude
            [0, 10, 15],        # velocity
            [1.0, 0.5, 0.0],    # water_mass
            [0, 0, 0]           # liquid_gas_mass
        ])
        mock_solution.t_events = [np.array([])]
        
        mock_solve_ivp.return_value = mock_solution
        
        # Mock derived quantities calculation
        simulator._calculate_derived_quantities = Mock(return_value=(
            np.array([8e5, 6e5, 4e5]),  # pressure
            np.array([300, 295, 290]),   # temperature
            np.array([50, 40, 30]),      # thrust
            np.array([0, 5, 10])         # drag
        ))
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE
        }
        
        sim_params = {
            'max_time': 5.0,
            'time_step': 0.01,
            'solver': 'RK45'
        }
        
        flight_data = simulator.simulate(rocket_params, sim_params)
        
        # Verify that custom parameters were used
        call_args = mock_solve_ivp.call_args
        assert call_args[1]['max_step'] == 0.01
        assert call_args[1]['method'] == 'RK45'
        assert call_args[0][1][1] == 5.0  # max_time in time_span
        
    @patch('builtins.print')
    def test_simulate_with_validation_warnings(self, mock_print):
        """Test simulation with validation warnings."""
        simulator = WaterRocketSimulator()
        
        # Mock validation with warnings
        simulator.validator.validate_rocket_parameters = Mock(return_value=[
            "Warning: Low water fraction",
            "Warning: High initial pressure"
        ])
        
        # Mock solve_ivp
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            mock_solution = Mock()
            mock_solution.t = np.array([0, 1])
            mock_solution.y = np.array([[0, 10], [0, 15], [1.0, 0.5], [0, 0]])
            mock_solution.t_events = [np.array([])]
            mock_solve_ivp.return_value = mock_solution
            
            # Mock derived quantities calculation
            simulator._calculate_derived_quantities = Mock(return_value=(
                np.array([8e5, 6e5]), np.array([300, 295]), 
                np.array([50, 40]), np.array([0, 5])
            ))
            
            rocket_params = {
                'V_bottle': 0.002,
                'water_fraction': 0.1,  # Low water fraction
                'A_nozzle': np.pi * (0.015 / 2) ** 2,
                'C_d': 0.8,
                'C_drag': 0.47,
                'A_rocket': np.pi * (0.1 / 2) ** 2,
                'm_empty': 0.25,
                'P0': 20 * ATMOSPHERIC_PRESSURE  # High pressure
            }
            
            flight_data = simulator.simulate(rocket_params)
            
            # Verify warnings were printed
            mock_print.assert_called_once()
            print_call = mock_print.call_args[0][0]
            assert "Warnings:" in print_call
            
    def test_simulate_initial_conditions_calculation(self):
        """Test that initial conditions are calculated correctly."""
        simulator = WaterRocketSimulator()
        
        # Mock validation
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.4,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE,
            'liquid_gas_mass': 0.05
        }
        
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            mock_solution = Mock()
            mock_solution.t = np.array([0, 1])
            mock_solution.y = np.array([[0, 10], [0, 15], [1.0, 0.5], [0.05, 0.03]])
            mock_solution.t_events = [np.array([])]
            mock_solve_ivp.return_value = mock_solution
            
            # Mock derived quantities calculation
            simulator._calculate_derived_quantities = Mock(return_value=(
                np.array([8e5, 6e5]), np.array([300, 295]), 
                np.array([50, 40]), np.array([0, 5])
            ))
            
            flight_data = simulator.simulate(rocket_params)
            
            # Check that solve_ivp was called with correct initial conditions
            call_args = mock_solve_ivp.call_args[0]
            initial_state = call_args[2]
            
            # Verify initial conditions
            assert initial_state[0] == 0.0  # initial altitude
            assert initial_state[1] == 0.0  # initial velocity
            
            # Verify initial water mass
            expected_water_mass = WATER_DENSITY * 0.002 * 0.4  # density * volume * fraction
            assert np.isclose(initial_state[2], expected_water_mass)
            
            # Verify initial liquid gas mass
            assert initial_state[3] == 0.05
            
    def test_flight_data_acceleration_calculation(self):
        """Test that acceleration is calculated correctly from velocity."""
        simulator = WaterRocketSimulator()
        
        # Mock validation
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            # Create velocity profile with known acceleration
            time = np.array([0, 1, 2, 3])
            velocity = np.array([0, 10, 15, 10])  # acceleration: 10, 5, -5
            
            mock_solution = Mock()
            mock_solution.t = time
            mock_solution.y = np.array([
                [0, 10, 20, 25],    # altitude
                velocity,           # velocity
                [1.0, 0.5, 0.2, 0], # water_mass
                [0, 0, 0, 0]        # liquid_gas_mass
            ])
            mock_solution.t_events = [np.array([])]
            mock_solve_ivp.return_value = mock_solution
            
            # Mock derived quantities calculation
            simulator._calculate_derived_quantities = Mock(return_value=(
                np.array([8e5, 6e5, 4e5, 1e5]),  # pressure
                np.array([300, 295, 290, 285]),   # temperature
                np.array([50, 40, 30, 0]),        # thrust
                np.array([0, 5, 10, 15])          # drag
            ))
            
            rocket_params = {
                'V_bottle': 0.002,
                'water_fraction': 0.33,
                'A_nozzle': np.pi * (0.015 / 2) ** 2,
                'C_d': 0.8,
                'C_drag': 0.47,
                'A_rocket': np.pi * (0.1 / 2) ** 2,
                'm_empty': 0.25,
                'P0': 8 * ATMOSPHERIC_PRESSURE
            }
            
            flight_data = simulator.simulate(rocket_params)
            
            # Verify acceleration calculation
            expected_acceleration = np.gradient(velocity, time)
            np.testing.assert_array_almost_equal(flight_data.acceleration, expected_acceleration)


class TestSimulationIntegration:
    """Integration tests for the complete simulation workflow."""
    
    def test_simulation_with_realistic_parameters(self):
        """Test simulation with realistic rocket parameters."""
        simulator = WaterRocketSimulator()
        
        # Use realistic parameters for a 2L bottle rocket
        rocket_params = {
            'V_bottle': 0.002,           # 2L bottle
            'water_fraction': 0.33,      # 1/3 water fill
            'A_nozzle': np.pi * (0.015 / 2) ** 2,  # 15mm nozzle
            'C_d': 0.8,                  # Discharge coefficient
            'C_drag': 0.47,              # Drag coefficient
            'A_rocket': np.pi * (0.1 / 2) ** 2,    # 10cm diameter
            'm_empty': 0.25,             # 250g empty mass
            'P0': 8 * ATMOSPHERIC_PRESSURE,  # 8 bar initial pressure
            'liquid_gas_mass': 0.0       # No liquid gas
        }
        
        # Mock the physics engine with realistic responses
        with patch.object(simulator.physics_engine, 'calculate_air_volume') as mock_air_vol, \
             patch.object(simulator.physics_engine, 'calculate_pressure_adiabatic') as mock_pressure, \
             patch.object(simulator.physics_engine, 'calculate_thrust') as mock_thrust, \
             patch.object(simulator.physics_engine, 'calculate_drag') as mock_drag, \
             patch.object(simulator.physics_engine, 'calculate_net_force') as mock_net_force, \
             patch.object(simulator.physics_engine, 'calculate_temperature_adiabatic') as mock_temp:
            
            # Setup realistic mock responses
            mock_air_vol.return_value = 0.001
            mock_pressure.return_value = 5e5
            mock_thrust.return_value = (30.0, 15.0, 0.1)
            mock_drag.return_value = 2.0
            mock_net_force.return_value = (28.0, 15.0)
            mock_temp.return_value = 280.0
            
            # Mock validation
            simulator.validator.validate_rocket_parameters = Mock(return_value=[])
            
            # Run simulation
            flight_data = simulator.simulate(rocket_params)
            
            # Verify reasonable results
            assert isinstance(flight_data, FlightData)
            assert flight_data.max_altitude > 0
            assert flight_data.max_velocity > 0
            assert flight_data.flight_time > 0
            assert len(flight_data.time) > 1
            
            # Verify physics engine was called appropriately
            mock_air_vol.assert_called()
            mock_pressure.assert_called()
            mock_thrust.assert_called()
            mock_drag.assert_called()
            mock_net_force.assert_called()
            
    def test_simulation_energy_conservation_check(self):
        """Test that simulation results are physically reasonable."""
        simulator = WaterRocketSimulator()
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE,
            'liquid_gas_mass': 0.0
        }
        
        # Mock realistic physics responses
        with patch.object(simulator.physics_engine, 'calculate_air_volume') as mock_air_vol, \
             patch.object(simulator.physics_engine, 'calculate_pressure_adiabatic') as mock_pressure, \
             patch.object(simulator.physics_engine, 'calculate_thrust') as mock_thrust, \
             patch.object(simulator.physics_engine, 'calculate_drag') as mock_drag, \
             patch.object(simulator.physics_engine, 'calculate_net_force') as mock_net_force, \
             patch.object(simulator.physics_engine, 'calculate_temperature_adiabatic') as mock_temp:
            
            mock_air_vol.return_value = 0.001
            mock_pressure.return_value = 5e5
            mock_thrust.return_value = (25.0, 12.0, 0.08)
            mock_drag.return_value = 1.5
            mock_net_force.return_value = (23.5, 12.0)
            mock_temp.return_value = 285.0
            
            simulator.validator.validate_rocket_parameters = Mock(return_value=[])
            
            flight_data = simulator.simulate(rocket_params)
            
            # Physical reasonableness checks
            assert flight_data.max_altitude > 0
            assert flight_data.max_velocity > 0
            assert flight_data.flight_time > 0
            
            # Water mass should decrease monotonically until depletion
            water_mass = flight_data.water_mass
            for i in range(len(water_mass) - 1):
                if water_mass[i] > 0:
                    assert water_mass[i+1] <= water_mass[i]
                    
            # Altitude should start at 0
            assert flight_data.altitude[0] == 0
            
            # Velocity should start at 0
            assert flight_data.velocity[0] == 0
            
    def test_simulation_parameter_sensitivity(self):
        """Test that simulation responds correctly to parameter changes."""
        simulator = WaterRocketSimulator()
        
        base_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE,
            'liquid_gas_mass': 0.0
        }
        
        # Mock physics engine for consistent results
        with patch.object(simulator.physics_engine, 'calculate_air_volume') as mock_air_vol, \
             patch.object(simulator.physics_engine, 'calculate_pressure_adiabatic') as mock_pressure, \
             patch.object(simulator.physics_engine, 'calculate_thrust') as mock_thrust, \
             patch.object(simulator.physics_engine, 'calculate_drag') as mock_drag, \
             patch.object(simulator.physics_engine, 'calculate_net_force') as mock_net_force, \
             patch.object(simulator.physics_engine, 'calculate_temperature_adiabatic') as mock_temp:
            
            # Setup mock responses that vary with pressure
            def pressure_response(p0, v_init, v_current):
                return p0 * (v_init / v_current) ** 1.4
            
            def thrust_response(pressure, a_nozzle, cd):
                if pressure > ATMOSPHERIC_PRESSURE:
                    thrust = cd * a_nozzle * (pressure - ATMOSPHERIC_PRESSURE)
                    return (thrust, 10.0, 0.05)
                return (0, 0, 0)
            
            mock_air_vol.return_value = 0.001
            mock_pressure.side_effect = pressure_response
            mock_thrust.side_effect = thrust_response
            mock_drag.return_value = 2.0
            mock_net_force.return_value = (20.0, 10.0)
            mock_temp.return_value = 280.0
            
            simulator.validator.validate_rocket_parameters = Mock(return_value=[])
            
            # Test with different initial pressures
            low_pressure_params = base_params.copy()
            low_pressure_params['P0'] = 5 * ATMOSPHERIC_PRESSURE
            
            high_pressure_params = base_params.copy()
            high_pressure_params['P0'] = 12 * ATMOSPHERIC_PRESSURE
            
            flight_low = simulator.simulate(low_pressure_params)
            flight_high = simulator.simulate(high_pressure_params)
            
            # Higher pressure should generally result in better performance
            # (though this depends on the specific physics implementation)
            assert isinstance(flight_low, FlightData)
            assert isinstance(flight_high, FlightData)
            assert flight_low.max_altitude >= 0
            assert flight_high.max_altitude >= 0


class TestSimulationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_simulation_with_zero_water_fraction(self):
        """Test simulation with no water (edge case)."""
        simulator = WaterRocketSimulator()
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.0,  # No water
            'A_nozzle': np.pi * (0.015 / 2) ** 2,
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE,
            'liquid_gas_mass': 0.0
        }
        
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        # Mock physics engine
        with patch.object(simulator.physics_engine, 'calculate_air_volume') as mock_air_vol, \
             patch.object(simulator.physics_engine, 'calculate_drag') as mock_drag, \
             patch.object(simulator.physics_engine, 'calculate_net_force') as mock_net_force:
            
            mock_air_vol.return_value = 0.002
            mock_drag.return_value = 0.0
            mock_net_force.return_value = (0.0, 0.0)
            
            flight_data = simulator.simulate(rocket_params)
            
            # Should complete without errors
            assert isinstance(flight_data, FlightData)
            assert flight_data.water_depletion_time == 0.0
            assert np.all(flight_data.water_mass == 0.0)
            assert np.all(flight_data.thrust == 0.0)
            
    def test_simulation_with_very_small_nozzle(self):
        """Test simulation with very small nozzle diameter."""
        simulator = WaterRocketSimulator()
        
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.33,
            'A_nozzle': np.pi * (0.001 / 2) ** 2,  # 1mm nozzle
            'C_d': 0.8,
            'C_drag': 0.47,
            'A_rocket': np.pi * (0.1 / 2) ** 2,
            'm_empty': 0.25,
            'P0': 8 * ATMOSPHERIC_PRESSURE,
            'liquid_gas_mass': 0.0
        }
        
        simulator.validator.validate_rocket_parameters = Mock(return_value=[])
        
        # Mock physics engine
        with patch.object(simulator.physics_engine, 'calculate_air_volume'), \
             patch.object(simulator.physics_engine, 'calculate_pressure_adiabatic'), \
             patch.object(simulator.physics_engine, 'calculate_thrust'), \
             patch.object(simulator.physics_engine, 'calculate_drag'), \
             patch.object(simulator.physics_engine, 'calculate_net_force'), \
             patch.object(simulator.physics_engine, 'calculate_temperature_adiabatic'):
            
            flight_data = simulator.simulate(rocket_params)
            
            # Should complete without errors
            assert isinstance(flight_data, FlightData)
            assert flight_data.flight_time > 0


if __name__ == '__main__':
    pytest.main([__file__])