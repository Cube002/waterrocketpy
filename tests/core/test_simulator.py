"""
Tests for waterrocketpy.core.simulation module.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from dataclasses import fields
from waterrocketpy.core.validation import ParameterValidator, ValidationError

# Import the module under test
try:
    from waterrocketpy.core.simulation import (
        WaterRocketSimulator,
        FlightData,
        filter_unique_time_series
    )
    from waterrocketpy.core.physics_engine import PhysicsEngine
    from waterrocketpy.core.validation import ParameterValidator
    from waterrocketpy.core.constants import (
        WATER_DENSITY,
        ATMOSPHERIC_PRESSURE,
        INITIAL_TEMPERATURE,
        ADIABATIC_INDEX_AIR
    )
except ImportError:
    # Mock imports for testing when module isn't available
    pytest.skip("waterrocketpy module not available", allow_module_level=True)


class TestFlightData:
    """Tests for FlightData dataclass."""
    
    def test_flight_data_creation(self):
        """Test FlightData object creation with all required fields."""
        # Create sample data
        time = np.linspace(0, 10, 100)
        altitude = np.sin(time)
        velocity = np.cos(time)
        
        flight_data = FlightData(
            time=time,
            altitude=altitude,
            velocity=velocity,
            acceleration=np.zeros_like(time),
            water_mass=np.ones_like(time),
            liquid_gas_mass=np.zeros_like(time),
            air_mass=np.ones_like(time) * 0.1,
            pressure=np.ones_like(time) * 1e5,
            air_temperature=np.ones_like(time) * 300,
            thrust=np.zeros_like(time),
            drag=np.zeros_like(time),
            water_exhaust_speed=np.zeros_like(time),
            air_exhaust_speed=np.zeros_like(time),
            water_mass_flow_rate=np.zeros_like(time),
            air_mass_flow_rate=np.zeros_like(time),
            air_exit_pressure=np.ones_like(time) * ATMOSPHERIC_PRESSURE,
            air_exit_temperature=np.ones_like(time) * INITIAL_TEMPERATURE,
            max_altitude=1.0,
            max_velocity=1.0,
            flight_time=10.0,
            water_depletion_time=5.0,
            air_depletion_time=8.0
        )
        
        assert isinstance(flight_data, FlightData)
        assert len(flight_data.time) == 100
        assert flight_data.max_altitude == 1.0
        assert flight_data.flight_time == 10.0
    
    def test_flight_data_fields(self):
        """Test that FlightData has all expected fields."""
        expected_fields = {
            'time', 'altitude', 'velocity', 'acceleration', 'water_mass',
            'liquid_gas_mass', 'air_mass', 'pressure', 'air_temperature',
            'thrust', 'drag', 'water_exhaust_speed', 'air_exhaust_speed',
            'water_mass_flow_rate', 'air_mass_flow_rate', 'air_exit_pressure',
            'air_exit_temperature', 'max_altitude', 'max_velocity',
            'flight_time', 'water_depletion_time', 'air_depletion_time'
        }
        
        actual_fields = {field.name for field in fields(FlightData)}
        assert actual_fields == expected_fields


class TestWaterRocketSimulator:
    """Tests for WaterRocketSimulator class."""
    
    @pytest.fixture
    def mock_physics_engine(self):
        """Create a mock physics engine for testing."""
        engine = Mock(spec=PhysicsEngine)
        engine.gravity = 9.81
        engine.air_gas_constant = 287.0
        engine.calculate_air_volume.return_value = 0.001
        engine.calculate_pressure_adiabatic.return_value = 2e5
        engine.calculate_temperature_adiabatic.return_value = 280
        engine.calculate_water_thrust.return_value = (100, 50, 0.1)
        engine.calculate_air_thrust.return_value = (50, 200, 0.01, 1.5e5, 270)
        engine.calculate_drag.return_value = 5.0
        engine.calculate_net_force.return_value = (95, 2.0)
        engine.calculate_air_mass_from_conditions.return_value = 0.002
        return engine
    
    @pytest.fixture
    def mock_validator(self):
        """Create a mock parameter validator."""
        validator = Mock(spec=ParameterValidator)
        validator.validate_rocket_parameters.return_value = []
        return validator
    
    @pytest.fixture
    def simulator(self, mock_physics_engine):
        """Create a simulator with mocked dependencies."""
        with patch('waterrocketpy.core.simulation.PhysicsEngine', return_value=mock_physics_engine), \
             patch('waterrocketpy.core.simulation.ParameterValidator') as mock_val_class:
            mock_val_class.return_value.validate_rocket_parameters.return_value = []
            sim = WaterRocketSimulator(mock_physics_engine)
            return sim
    
    @pytest.fixture
    def sample_rocket_params(self):
        """Sample rocket parameters for testing."""
        return {
            'V_bottle': 0.002,  # 2L bottle
            'water_fraction': 0.3,
            'P0': 2e5,  # initial pressure in Pascals
            'A_nozzle': 0.0001,  # nozzle area
            'C_d': 0.8,  # discharge coefficient
            'm_empty': 0.1,  # empty rocket mass
            'C_drag': 0.5,  # drag coefficient
            'A_rocket': 0.01,  # rocket cross-sectional area
            'liquid_gas_mass': 0.0
        }
    
    def test_simulator_initialization(self):
        """Test simulator initialization."""
        # Test with default physics engine
        sim1 = WaterRocketSimulator()
        assert sim1.physics_engine is not None
        assert sim1.validator is not None
        assert isinstance(sim1.derived_data, dict)
        
        # Test with custom physics engine
        custom_engine = Mock()
        sim2 = WaterRocketSimulator(custom_engine)
        assert sim2.physics_engine is custom_engine
    
    def test_store_derived_quantities(self, simulator):
        """Test storage of derived quantities during simulation."""
        simulator._store_derived_quantities(
            t=1.0,
            pressure=2e5,
            temperature=280,
            thrust=100,
            drag=5,
            water_exhaust_speed=50,
            water_mass_flow_rate=0.1
        )
        
        assert len(simulator.derived_data['time']) == 1
        assert simulator.derived_data['time'][0] == 1.0
        assert simulator.derived_data['pressure'][0] == 2e5
        assert simulator.derived_data['thrust'][0] == 100
        assert simulator.derived_data['water_exhaust_speed'][0] == 50
    
    def test_water_depletion_event(self, simulator, sample_rocket_params):
        """Test water depletion event detection."""
        # Test with water remaining
        state_with_water = np.array([10, 5, 0.5, 0])  # altitude, velocity, water_mass, liquid_gas_mass
        result = simulator._water_depletion_event(1.0, state_with_water, sample_rocket_params)
        assert result == 0.5  # Should return water mass
        
        # Test with no water
        state_no_water = np.array([10, 5, 0, 0])
        result = simulator._water_depletion_event(1.0, state_no_water, sample_rocket_params)
        assert result == 0
    
    def test_air_depletion_event(self, simulator, sample_rocket_params):
        """Test air depletion event detection."""
        # Test with short state (not in air phase)
        short_state = np.array([10, 5])
        result = simulator._air_depletion_event(1.0, short_state, sample_rocket_params)
        assert result == 1.0
        
        # Test with air remaining (pressure > atmospheric)
        # Mock the physics engine to return high pressure
        simulator.physics_engine.air_gas_constant = 287.0
        state_with_air = np.array([10, 5, 0.003, 280])  # altitude, velocity, air_mass, temperature
        
        result = simulator._air_depletion_event(1.0, state_with_air, sample_rocket_params)
        # Should return positive value (pressure difference)
        assert result >= 0
        
        # Test with no air
        state_no_air = np.array([10, 5, 0, 280])
        result = simulator._air_depletion_event(1.0, state_no_air, sample_rocket_params)
        assert result == 0.0
    
    def test_hit_ground_event(self, simulator, sample_rocket_params):
        """Test ground impact event detection."""
        # Test above ground
        state_above = np.array([10, 5])
        result = simulator._hit_ground_event(1.0, state_above, sample_rocket_params)
        assert result == 10  # Should return altitude
        
        # Test at ground level
        state_ground = np.array([0, 5])
        result = simulator._hit_ground_event(1.0, state_ground, sample_rocket_params)
        assert result == 0.0
        
        # Test below ground
        state_below = np.array([-1, 5])
        result = simulator._hit_ground_event(1.0, state_below, sample_rocket_params)
        assert result == 0.0
    
    def test_rocket_ode_water_phase(self, simulator, sample_rocket_params):
        """Test water phase ODE system."""
        state = np.array([5, 10, 0.6, 0])  # altitude, velocity, water_mass, liquid_gas_mass
        
        derivatives = simulator._rocket_ode_water_phase(1.0, state, sample_rocket_params)
        
        # Should return [velocity, acceleration, dm_water/dt, dm_gas/dt]
        assert len(derivatives) == 4
        assert derivatives[0] == 10  # velocity derivative = velocity
        assert isinstance(derivatives[1], (int, float))  # acceleration
        assert derivatives[2] <= 0  # water mass should decrease or stay same
        
        # Check that derived quantities were stored
        assert len(simulator.derived_data['time']) > 0
    
    def test_rocket_ode_air_phase(self, simulator, sample_rocket_params):
        """Test air phase ODE system."""
        state = np.array([10, 15, 0.002, 280])  # altitude, velocity, air_mass, temperature
        
        derivatives = simulator._rocket_ode_air_phase(1.0, state, sample_rocket_params)
        
        # Should return [velocity, acceleration, dm_air/dt, dT/dt]
        assert len(derivatives) == 4
        assert derivatives[0] == 15  # velocity derivative = velocity
        assert isinstance(derivatives[1], (int, float))  # acceleration
        assert derivatives[2] <= 0  # air mass should decrease or stay same
        
        # Test with zero air mass
        state_no_air = np.array([10, 15, 0, 280])
        derivatives_no_air = simulator._rocket_ode_air_phase(1.0, state_no_air, sample_rocket_params)
        assert derivatives_no_air[2] == 0  # no mass flow
        assert derivatives_no_air[3] == 0  # no temperature change
    
    def test_rocket_ode_coasting_phase(self, simulator, sample_rocket_params):
        """Test coasting phase ODE system."""
        state = np.array([20, 5])  # altitude, velocity
        
        derivatives = simulator._rocket_ode_coasting_phase(
            1.0, state, sample_rocket_params, 1e5, 280
        )
        
        # Should return [velocity, acceleration]
        assert len(derivatives) == 2
        assert derivatives[0] == 5  # velocity derivative = velocity
        assert isinstance(derivatives[1], (int, float))  # acceleration (should be negative due to gravity/drag)
    
    def test_setup_events(self, simulator, sample_rocket_params):
        """Test event setup functions."""
        # Test water events
        water_events = simulator._setup_water_events(sample_rocket_params)
        assert len(water_events) == 1
        assert hasattr(water_events[0], 'terminal')
        assert water_events[0].terminal is True
        
        # Test air events
        air_events = simulator._setup_air_events(sample_rocket_params)
        assert len(air_events) == 1
        assert hasattr(air_events[0], 'terminal')
        assert air_events[0].terminal is True
        
        # Test coasting events
        coasting_events = simulator._setup_coasting_events(sample_rocket_params)
        assert len(coasting_events) == 1
        assert hasattr(coasting_events[0], 'terminal')
        assert coasting_events[0].terminal is True
    
    @patch('waterrocketpy.core.simulation.solve_ivp')
    @patch('waterrocketpy.core.simulation.interp1d')
    def test_simulate_water_only(self, mock_interp1d, mock_solve_ivp, simulator, sample_rocket_params):
        """Test simulation with only water phase (no events triggered)."""
        # Mock solve_ivp to return a solution that doesn't trigger water depletion
        mock_solution = Mock()
        mock_solution.t = np.linspace(0, 5, 100)
        mock_solution.y = np.array([
            np.linspace(0, 100, 100),  # altitude
            np.linspace(0, 50, 100),   # velocity
            np.linspace(0.6, 0.1, 100),  # water_mass (doesn't reach zero)
            np.zeros(100)  # liquid_gas_mass
        ])
        mock_solution.t_events = [np.array([])]  # No events triggered
        mock_solve_ivp.return_value = mock_solution
        
        # Mock interpolation
        mock_interp_func = Mock()
        mock_interp_func.return_value = np.ones(100)
        mock_interp1d.return_value = mock_interp_func
        
        # Run simulation
        result = simulator.simulate(sample_rocket_params)
        
        # Verify result
        assert isinstance(result, FlightData)
        assert len(result.time) == 100
        assert result.water_depletion_time == 0.0  # No water depletion
        assert result.air_depletion_time == 0.0    # No air phase
    
    @patch('waterrocketpy.core.simulation.solve_ivp')
    @patch('waterrocketpy.core.simulation.interp1d')
    def test_simulate_full_flight(self, mock_interp1d, mock_solve_ivp, simulator, sample_rocket_params):
        """Test complete simulation with all three phases."""
        # Mock solutions for each phase
        solutions = []
        
        # Water phase solution (triggers water depletion)
        water_solution = Mock()
        water_solution.t = np.linspace(0, 2, 50)
        water_solution.y = np.array([
            np.linspace(0, 50, 50),    # altitude
            np.linspace(0, 30, 50),    # velocity
            np.linspace(0.6, 0, 50),   # water_mass (reaches zero)
            np.zeros(50)               # liquid_gas_mass
        ])
        water_solution.t_events = [np.array([2.0])]  # Water depleted at t=2
        solutions.append(water_solution)
        
        # Air phase solution (triggers air depletion)
        air_solution = Mock()
        air_solution.t = np.linspace(2, 5, 30)
        air_solution.y = np.array([
            np.linspace(50, 80, 30),     # altitude
            np.linspace(30, 20, 30),     # velocity
            np.linspace(0.002, 0.0001, 30),  # air_mass
            np.linspace(280, 250, 30)    # temperature
        ])
        air_solution.t_events = [np.array([5.0])]  # Air depleted at t=5
        solutions.append(air_solution)
        
        # Coasting phase solution
        coasting_solution = Mock()
        coasting_solution.t = np.linspace(5, 10, 50)
        coasting_solution.y = np.array([
            np.linspace(80, 0, 50),      # altitude (lands)
            np.linspace(20, -20, 50)     # velocity
        ])
        coasting_solution.t_events = [np.array([])]  # No events
        solutions.append(coasting_solution)
        
        mock_solve_ivp.side_effect = solutions
        
        # Mock interpolation
        mock_interp_func = Mock()
        mock_interp_func.return_value = np.ones(130)  # Total length
        mock_interp1d.return_value = mock_interp_func
        
        # Run simulation
        result = simulator.simulate(sample_rocket_params)
        
        # Verify result
        assert isinstance(result, FlightData)
        assert result.water_depletion_time == 2.0
        assert result.air_depletion_time == 5.0
        assert mock_solve_ivp.call_count == 3  # Three phases
    
    def test_simulate_with_warnings(self, simulator, sample_rocket_params):
        """Test simulation with parameter validation warnings."""
        # Mock validator to return warnings
        simulator.validator.validate_rocket_parameters.return_value = ["Test warning"]
        
        with patch('builtins.print') as mock_print:
            # This would normally run a full simulation, but we'll patch solve_ivp
            with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
                mock_solution = Mock()
                mock_solution.t = np.array([0, 1])
                mock_solution.y = np.array([[0, 10], [0, 5], [0.6, 0.5], [0, 0]])
                mock_solution.t_events = [np.array([])]
                mock_solve_ivp.return_value = mock_solution
                
                with patch('waterrocketpy.core.simulation.interp1d'):
                    simulator.simulate(sample_rocket_params)
            
            # Check that warnings were printed
            mock_print.assert_called()
    
    def test_simulate_custom_sim_params(self, simulator, sample_rocket_params):
        """Test simulation with custom simulation parameters."""
        custom_sim_params = {
            'max_time': 20.0,
            'time_step': 0.01,
            'solver': 'RK45'
        }
        
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            mock_solution = Mock()
            mock_solution.t = np.array([0, 1])
            mock_solution.y = np.array([[0, 10], [0, 5], [0.6, 0.5], [0, 0]])
            mock_solution.t_events = [np.array([])]
            mock_solve_ivp.return_value = mock_solution
            
            with patch('waterrocketpy.core.simulation.interp1d'):
                simulator.simulate(sample_rocket_params, custom_sim_params)
            
            # Verify solve_ivp was called with custom parameters
            assert mock_solve_ivp.called
            # Check that max_step parameter was passed correctly
            call_kwargs = mock_solve_ivp.call_args[1]
            assert call_kwargs['max_step'] == 0.01
            assert call_kwargs['method'] == 'RK45'


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_filter_unique_time_series(self):
        """Test filtering of duplicate time values."""
        # Create test data with duplicate times
        time = np.array([0, 1, 1, 2, 2, 2, 3])
        altitude = np.array([0, 10, 15, 20, 25, 30, 35])
        velocity = np.array([0, 5, 7, 10, 12, 15, 18])
        
        # Filter duplicates
        filtered = filter_unique_time_series(time, altitude, velocity)
        
        # Should have 4 unique time values: 0, 1, 2, 3
        assert len(filtered[0]) == 4
        assert np.array_equal(filtered[0], [0, 1, 2, 3])
        
        # Check that corresponding values are preserved
        assert len(filtered[1]) == 4  # altitude
        assert len(filtered[2]) == 4  # velocity
        
        # Should keep first occurrence of each time
        assert filtered[1][1] == 10  # First altitude at t=1
        assert filtered[1][2] == 20  # First altitude at t=2
    
    def test_filter_unique_time_series_already_unique(self):
        """Test filtering when times are already unique."""
        time = np.array([0, 1, 2, 3])
        altitude = np.array([0, 10, 20, 30])
        
        filtered = filter_unique_time_series(time, altitude)
        
        # Should be unchanged
        assert np.array_equal(filtered[0], time)
        assert np.array_equal(filtered[1], altitude)
    
    def test_filter_unique_time_series_empty(self):
        """Test filtering with empty arrays."""
        time = np.array([])
        altitude = np.array([])
        
        filtered = filter_unique_time_series(time, altitude)
        
        assert len(filtered[0]) == 0
        assert len(filtered[1]) == 0


# Integration tests
class TestSimulationIntegration:
    """Integration tests for the simulation system."""
    
    @pytest.fixture
    def realistic_rocket_params(self):
        """Realistic rocket parameters for integration testing."""
        return {
            'V_bottle': 0.002,      # 2L bottle
            'water_fraction': 0.3,   # 30% water
            'P0': 300000,           # 3 bar initial pressure
            'A_nozzle': 0.00005,    # 0.5 cm² nozzle area
            'C_d': 0.8,             # discharge coefficient
            'm_empty': 0.15,        # 150g empty rocket mass
            'C_drag': 0.5,          # drag coefficient
            'A_rocket': 0.008,      # rocket cross-sectional area
            'liquid_gas_mass': 0.0  # no liquid gas
        }
    
    @pytest.mark.slow
    def test_realistic_simulation(self, realistic_rocket_params):
        """Test simulation with realistic parameters (marked as slow test)."""
        # This test would run an actual simulation if we had the real modules
        # For now, we'll skip it unless explicitly running integration tests
        #pytest.skip("Integration test - requires full module setup")
        
        simulator = WaterRocketSimulator()
        result = simulator.simulate(realistic_rocket_params)
        
        # Basic sanity checks
        assert result.max_altitude > 0
        assert result.max_velocity > 0
        assert result.flight_time > 0
        assert len(result.time) > 10  # Should have reasonable number of points


# Parametrized tests
class TestParametrizedSimulation:
    """Parametrized tests for different rocket configurations."""
    
    @pytest.mark.parametrize("water_fraction", [0.1, 0.3, 0.5, 0.7])
    def test_different_water_fractions(self, water_fraction):
        """Test simulation with different water fractions."""
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': water_fraction,
            'P0': 300000,
            'A_nozzle': 0.00005,
            'C_d': 0.8,
            'm_empty': 0.15,
            'C_drag': 0.5,
            'A_rocket': 0.008,
            'liquid_gas_mass': 0.0
        }
        
        # Mock the simulation for testing
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            mock_solution = Mock()
            mock_solution.t = np.linspace(0, 5, 100)
            mock_solution.y = np.array([
                np.linspace(0, 50, 100),
                np.linspace(0, 20, 100),
                np.linspace(water_fraction, 0, 100),
                np.zeros(100)
            ])
            mock_solution.t_events = [np.array([])]
            mock_solve_ivp.return_value = mock_solution
            
            with patch('waterrocketpy.core.simulation.interp1d'):
                simulator = WaterRocketSimulator()
                result = simulator.simulate(rocket_params)
                
                assert isinstance(result, FlightData)
    
    @pytest.mark.parametrize("pressure", [200000, 300000, 400000, 500000])
    def test_different_pressures(self, pressure):
        """Test simulation with different initial pressures."""
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.3,
            'P0': pressure,
            'A_nozzle': 0.00005,
            'C_d': 0.8,
            'm_empty': 0.15,
            'C_drag': 0.5,
            'A_rocket': 0.008,
            'liquid_gas_mass': 0.0
        }
        
        # Mock test as above
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            mock_solution = Mock()
            mock_solution.t = np.linspace(0, 5, 100)
            mock_solution.y = np.array([
                np.linspace(0, 50, 100),
                np.linspace(0, 20, 100),
                np.linspace(0.6, 0, 100),
                np.zeros(100)
            ])
            mock_solution.t_events = [np.array([])]
            mock_solve_ivp.return_value = mock_solution
            
            with patch('waterrocketpy.core.simulation.interp1d'):
                simulator = WaterRocketSimulator()
                result = simulator.simulate(rocket_params)
                
                assert isinstance(result, FlightData)


# Error handling tests
class TestSimulationErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_invalid_parameters_validation(self):
        """Test that invalid parameters raise ValidationError from ParameterValidator."""
        invalid_params = {
            'P0': -100000,             # Invalid: negative pressure
            'A_nozzle': 0.0001,        # Valid
            'V_bottle': -0.002,        # Invalid: negative volume
            'water_fraction': 1.5,     # Invalid: >1
            'C_d': 0.05,               # Invalid: out of range
            'm_empty': 0.1,            # Valid
            'C_drag': 2.5,             # Invalid: too high
            'A_rocket': 0.01           # Valid
        }

        with pytest.raises(ValidationError) as exc_info:
            ParameterValidator.validate_rocket_parameters(invalid_params)

        # Confirm that the correct message is included
        assert "must be greater" in str(exc_info.value) or "must be between" in str(exc_info.value)

    def test_valid_parameters_with_warnings(self):
        """Test that valid but extreme parameters return appropriate warnings."""
        extreme_params = {
            'P0': 60 * 101325,         # Valid but very high pressure
            'A_nozzle': 0.0001,
            'V_bottle': 0.002,
            'water_fraction': 0.95,    # Too high
            'C_d': 0.55,               # Low
            'm_empty': 0.1,
            'C_drag': 1.6,             # High
            'A_rocket': 0.01
        }

        warnings = ParameterValidator.validate_rocket_parameters(extreme_params)

        assert "very high" in " ".join(warnings)
        assert any("low" in w for w in warnings)
        assert any("high" in w for w in warnings)
        
    def test_solver_failure_handling(self):
        """Test handling of solver failures."""
        simulator = WaterRocketSimulator()
        rocket_params = {
            'V_bottle': 0.002,
            'water_fraction': 0.3,
            'P0': 300000,
            'A_nozzle': 0.00005,
            'C_d': 0.8,
            'm_empty': 0.15,
            'C_drag': 0.5,
            'A_rocket': 0.008,
            'liquid_gas_mass': 0.0
        }
        
        with patch('waterrocketpy.core.simulation.solve_ivp') as mock_solve_ivp:
            # Simulate solver failure
            mock_solve_ivp.side_effect = RuntimeError("Solver failed")
            
            with pytest.raises(RuntimeError):
                simulator.simulate(rocket_params)


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])