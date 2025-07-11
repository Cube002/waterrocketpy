"""
Test suite for the rocket builder module.
"""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from waterrocketpy.rocket.builder import (
    RocketBuilder, RocketConfiguration, 
    create_standard_rocket, create_competition_rocket, create_high_pressure_rocket
)
from waterrocketpy.core.constants import (
    ATMOSPHERIC_PRESSURE, DEFAULT_BOTTLE_VOLUME, DEFAULT_NOZZLE_DIAMETER,
    DEFAULT_EMPTY_MASS, DEFAULT_WATER_FRACTION, DEFAULT_DRAG_COEFFICIENT,
    DEFAULT_DISCHARGE_COEFFICIENT
)


class TestRocketConfiguration:
    """Test cases for RocketConfiguration class."""
    
    def test_default_initialization(self):
        """Test default rocket configuration initialization."""
        config = RocketConfiguration()
        
        assert config.bottle_volume == DEFAULT_BOTTLE_VOLUME
        assert config.nozzle_diameter == DEFAULT_NOZZLE_DIAMETER
        assert config.empty_mass == DEFAULT_EMPTY_MASS
        assert config.water_fraction == DEFAULT_WATER_FRACTION
        assert config.drag_coefficient == DEFAULT_DRAG_COEFFICIENT
        assert config.nozzle_discharge_coefficient == DEFAULT_DISCHARGE_COEFFICIENT
        assert config.initial_pressure == 10 * ATMOSPHERIC_PRESSURE
        assert config.liquid_gas_mass == 0.0
        assert config.name == "Default Rocket"
        
    def test_post_init_reference_area_calculation(self):
        """Test that reference area is calculated when None."""
        config = RocketConfiguration(bottle_diameter=0.1, reference_area=None)
        expected_area = np.pi * (0.1 / 2) ** 2
        assert np.isclose(config.reference_area, expected_area)
        
    def test_post_init_reference_area_preserved(self):
        """Test that reference area is preserved when provided."""
        custom_area = 0.05
        config = RocketConfiguration(reference_area=custom_area)
        assert config.reference_area == custom_area
        
    def test_nozzle_area_property(self):
        """Test nozzle area calculation."""
        config = RocketConfiguration(nozzle_diameter=0.02)
        expected_area = np.pi * (0.02 / 2) ** 2
        assert np.isclose(config.nozzle_area, expected_area)
        
    def test_water_volume_property(self):
        """Test water volume calculation."""
        config = RocketConfiguration(bottle_volume=0.002, water_fraction=0.5)
        expected_volume = 0.002 * 0.5
        assert np.isclose(config.water_volume, expected_volume)
        
    def test_water_mass_property(self):
        """Test water mass calculation."""
        config = RocketConfiguration(bottle_volume=0.002, water_fraction=0.5)
        # Water density is 1000 kg/m³
        expected_mass = 0.002 * 0.5 * 1000
        assert np.isclose(config.water_mass, expected_mass)
        
    def test_total_mass_property(self):
        """Test total mass calculation."""
        config = RocketConfiguration(
            empty_mass=0.3, 
            bottle_volume=0.002, 
            water_fraction=0.5,
            liquid_gas_mass=0.05
        )
        expected_total = 0.3 + (0.002 * 0.5 * 1000) + 0.05
        assert np.isclose(config.total_mass, expected_total)


class TestRocketBuilder:
    """Test cases for RocketBuilder class."""
    
    def test_default_initialization(self):
        """Test default builder initialization."""
        builder = RocketBuilder()
        assert isinstance(builder.config, RocketConfiguration)
        assert builder.config.name == "Default Rocket"
        
    def test_set_bottle_parameters(self):
        """Test setting bottle parameters."""
        builder = RocketBuilder()
        builder.set_bottle(volume=0.003, diameter=0.12, length=0.35)
        
        assert builder.config.bottle_volume == 0.003
        assert builder.config.bottle_diameter == 0.12
        assert builder.config.bottle_length == 0.35
        
    def test_set_bottle_parameters_partial(self):
        """Test setting bottle parameters without length."""
        builder = RocketBuilder()
        original_length = builder.config.bottle_length
        builder.set_bottle(volume=0.003, diameter=0.12)
        
        assert builder.config.bottle_volume == 0.003
        assert builder.config.bottle_diameter == 0.12
        assert builder.config.bottle_length == original_length
        
    def test_set_nozzle_parameters(self):
        """Test setting nozzle parameters."""
        builder = RocketBuilder()
        builder.set_nozzle(diameter=0.018, discharge_coefficient=0.95)
        
        assert builder.config.nozzle_diameter == 0.018
        assert builder.config.nozzle_discharge_coefficient == 0.95
        
    def test_set_nozzle_parameters_partial(self):
        """Test setting nozzle parameters without discharge coefficient."""
        builder = RocketBuilder()
        original_cd = builder.config.nozzle_discharge_coefficient
        builder.set_nozzle(diameter=0.018)
        
        assert builder.config.nozzle_diameter == 0.018
        assert builder.config.nozzle_discharge_coefficient == original_cd
        
    def test_set_mass_parameters(self):
        """Test setting mass parameters."""
        builder = RocketBuilder()
        builder.set_mass(empty_mass=0.4, water_fraction=0.6)
        
        assert builder.config.empty_mass == 0.4
        assert builder.config.water_fraction == 0.6
        
    def test_set_aerodynamics(self):
        """Test setting aerodynamic parameters."""
        builder = RocketBuilder()
        builder.set_aerodynamics(drag_coefficient=0.4, reference_area=0.008)
        
        assert builder.config.drag_coefficient == 0.4
        assert builder.config.reference_area == 0.008
        
    def test_set_initial_conditions(self):
        """Test setting initial conditions."""
        builder = RocketBuilder()
        builder.set_initial_conditions(pressure=15 * ATMOSPHERIC_PRESSURE, temperature=320)
        
        assert builder.config.initial_pressure == 15 * ATMOSPHERIC_PRESSURE
        assert builder.config.initial_temperature == 320
        
    def test_add_liquid_gas(self):
        """Test adding liquid gas propellant."""
        builder = RocketBuilder()
        builder.add_liquid_gas(mass=0.08)
        
        assert builder.config.liquid_gas_mass == 0.08
        
    def test_set_metadata(self):
        """Test setting metadata."""
        builder = RocketBuilder()
        builder.set_metadata(name="Test Rocket", description="Test configuration")
        
        assert builder.config.name == "Test Rocket"
        assert builder.config.description == "Test configuration"
        
    def test_builder_chaining(self):
        """Test that builder methods can be chained."""
        builder = RocketBuilder()
        result = (builder
                 .set_bottle(volume=0.002, diameter=0.1)
                 .set_nozzle(diameter=0.015)
                 .set_mass(empty_mass=0.25, water_fraction=0.33)
                 .set_metadata("Chained Rocket"))
        
        assert result is builder
        assert builder.config.bottle_volume == 0.002
        assert builder.config.nozzle_diameter == 0.015
        assert builder.config.empty_mass == 0.25
        assert builder.config.name == "Chained Rocket"
        
    @patch('waterrocketpy.core.validation.ParameterValidator.validate_rocket_parameters')
    def test_build_with_validation(self, mock_validate):
        """Test build method with validation."""
        mock_validate.return_value = []
        
        builder = RocketBuilder()
        config = builder.build()
        
        assert isinstance(config, RocketConfiguration)
        mock_validate.assert_called_once()
        
    @patch('waterrocketpy.core.validation.ParameterValidator.validate_rocket_parameters')
    @patch('builtins.print')
    def test_build_with_warnings(self, mock_print, mock_validate):
        """Test build method with validation warnings."""
        mock_validate.return_value = ["Warning 1", "Warning 2"]
        
        builder = RocketBuilder()
        config = builder.build()
        
        assert isinstance(config, RocketConfiguration)
        mock_validate.assert_called_once()
        mock_print.assert_called()
        
    def test_to_simulation_params(self):
        """Test conversion to simulation parameters."""
        builder = RocketBuilder()
        builder.set_bottle(volume=0.002, diameter=0.1)
        builder.set_nozzle(diameter=0.015)
        builder.set_mass(empty_mass=0.25, water_fraction=0.33)
        builder.set_initial_conditions(pressure=8 * ATMOSPHERIC_PRESSURE)
        
        params = builder.to_simulation_params()
        
        expected_keys = [
            'P0', 'A_nozzle', 'V_bottle', 'water_fraction', 'C_d',
            'm_empty', 'C_drag', 'A_rocket', 'liquid_gas_mass'
        ]
        
        for key in expected_keys:
            assert key in params
            
        assert params['P0'] == 8 * ATMOSPHERIC_PRESSURE
        assert params['V_bottle'] == 0.002
        assert params['water_fraction'] == 0.33
        assert params['m_empty'] == 0.25
        assert np.isclose(params['A_nozzle'], np.pi * (0.015 / 2) ** 2)
        
    def test_from_dict(self):
        """Test creating builder from dictionary."""
        data = {
            'bottle_volume': 0.003,
            'nozzle_diameter': 0.02,
            'empty_mass': 0.3,
            'name': 'Dict Rocket'
        }
        
        builder = RocketBuilder.from_dict(data)
        
        assert builder.config.bottle_volume == 0.003
        assert builder.config.nozzle_diameter == 0.02
        assert builder.config.empty_mass == 0.3
        assert builder.config.name == 'Dict Rocket'
        
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        builder = RocketBuilder()
        builder.set_bottle(volume=0.002, diameter=0.1)
        builder.set_metadata("JSON Test Rocket")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            builder.to_json(f.name)
            
            # Read back and verify
            builder2 = RocketBuilder.from_json(f.name)
            
            assert builder2.config.bottle_volume == 0.002
            assert builder2.config.bottle_diameter == 0.1
            assert builder2.config.name == "JSON Test Rocket"
            
        # Clean up
        Path(f.name).unlink()
        
    def test_from_json_file_not_found(self):
        """Test error handling when JSON file is not found."""
        with pytest.raises(FileNotFoundError):
            RocketBuilder.from_json("nonexistent_file.json")
            
    def test_reset(self):
        """Test resetting builder to default configuration."""
        builder = RocketBuilder()
        builder.set_bottle(volume=0.003, diameter=0.12)
        builder.set_metadata("Modified Rocket")
        
        builder.reset()
        
        assert builder.config.bottle_volume == DEFAULT_BOTTLE_VOLUME
        assert builder.config.name == "Default Rocket"


class TestPrebuiltRockets:
    """Test cases for prebuilt rocket configurations."""
    
    def test_create_standard_rocket(self):
        """Test standard rocket creation."""
        rocket = create_standard_rocket()
        
        assert isinstance(rocket, RocketConfiguration)
        assert rocket.name == "Standard 2L Rocket"
        assert rocket.bottle_volume == 0.002
        assert rocket.bottle_diameter == 0.1
        assert rocket.nozzle_diameter == 0.015
        assert rocket.empty_mass == 0.25
        assert rocket.water_fraction == 0.33
        assert rocket.initial_pressure == 8 * ATMOSPHERIC_PRESSURE
        
    def test_create_competition_rocket(self):
        """Test competition rocket creation."""
        rocket = create_competition_rocket()
        
        assert isinstance(rocket, RocketConfiguration)
        assert rocket.name == "Competition Rocket"
        assert rocket.bottle_volume == 0.0015
        assert rocket.bottle_diameter == 0.08
        assert rocket.nozzle_diameter == 0.012
        assert rocket.nozzle_discharge_coefficient == 0.98
        assert rocket.empty_mass == 0.15
        assert rocket.water_fraction == 0.4
        assert rocket.drag_coefficient == 0.3
        assert rocket.initial_pressure == 12 * ATMOSPHERIC_PRESSURE
        
    def test_create_high_pressure_rocket(self):
        """Test high pressure rocket creation."""
        rocket = create_high_pressure_rocket()
        
        assert isinstance(rocket, RocketConfiguration)
        assert rocket.name == "High Pressure Rocket"
        assert rocket.bottle_volume == 0.001
        assert rocket.nozzle_diameter == 0.020
        assert rocket.empty_mass == 0.3
        assert rocket.water_fraction == 0.25
        assert rocket.liquid_gas_mass == 0.05
        assert rocket.initial_pressure == 15 * ATMOSPHERIC_PRESSURE
        
    def test_prebuilt_rockets_valid_parameters(self):
        """Test that all prebuilt rockets have valid parameters."""
        rockets = [
            create_standard_rocket(),
            create_competition_rocket(),
            create_high_pressure_rocket()
        ]
        
        for rocket in rockets:
            # Basic validation checks
            assert rocket.bottle_volume > 0
            assert rocket.nozzle_diameter > 0
            assert rocket.empty_mass > 0
            assert 0 < rocket.water_fraction < 1
            assert rocket.initial_pressure > ATMOSPHERIC_PRESSURE
            assert rocket.nozzle_area > 0
            assert rocket.water_volume > 0
            assert rocket.total_mass > 0


class TestRocketBuilderIntegration:
    """Integration tests for rocket builder."""
    
    def test_complete_rocket_build_workflow(self):
        """Test complete workflow from building to simulation parameters."""
        # Build a custom rocket
        builder = RocketBuilder()
        rocket = (builder
                 .set_bottle(volume=0.0025, diameter=0.11)
                 .set_nozzle(diameter=0.016, discharge_coefficient=0.96)
                 .set_mass(empty_mass=0.28, water_fraction=0.35)
                 .set_aerodynamics(drag_coefficient=0.35, reference_area=0.009)
                 .set_initial_conditions(pressure=9 * ATMOSPHERIC_PRESSURE, temperature=295)
                 .add_liquid_gas(mass=0.03)
                 .set_metadata("Integration Test Rocket", "Test rocket for integration")
                 .build())
        
        # Verify rocket properties
        assert rocket.name == "Integration Test Rocket"
        assert rocket.bottle_volume == 0.0025
        assert rocket.total_mass > 0
        
        # Convert to simulation parameters
        params = builder.to_simulation_params()
        
        # Verify simulation parameters are correctly mapped
        assert params['V_bottle'] == 0.0025
        assert params['P0'] == 9 * ATMOSPHERIC_PRESSURE
        assert params['water_fraction'] == 0.35
        assert params['m_empty'] == 0.28
        assert params['liquid_gas_mass'] == 0.03
        assert params['C_d'] == 0.96
        assert params['C_drag'] == 0.35
        assert params['A_rocket'] == 0.009
        
        # Verify calculated nozzle area
        expected_nozzle_area = np.pi * (0.016 / 2) ** 2
        assert np.isclose(params['A_nozzle'], expected_nozzle_area)
        
    def test_builder_parameter_validation_integration(self):
        """Test that builder integrates properly with parameter validation."""
        with patch('waterrocketpy.core.validation.ParameterValidator') as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate_rocket_parameters.return_value = []
            mock_validator.return_value = mock_instance
            
            builder = RocketBuilder()
            rocket = builder.build()
            
            # Verify validator was called with correct parameters
            mock_instance.validate_rocket_parameters.assert_called_once()
            call_args = mock_instance.validate_rocket_parameters.call_args[0][0]
            
            # Check that all required parameters are present
            required_params = ['P0', 'A_nozzle', 'V_bottle', 'water_fraction', 'C_d',
                             'm_empty', 'C_drag', 'A_rocket', 'liquid_gas_mass']
            for param in required_params:
                assert param in call_args


if __name__ == '__main__':
    pytest.main([__file__])