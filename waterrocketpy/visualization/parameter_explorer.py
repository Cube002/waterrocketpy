#!/usr/bin/env python3
"""
Water Rocket Parameter Exploration Tool

This script provides comprehensive parameter exploration capabilities for water rocket simulations.
Features:
- Parameter sweeping with configurable ranges
- Multi-parameter analysis with 2D plotting
- Sensitivity analysis (derivatives)
- Extensible design for adding new parameters and targets
- Robust error handling and progress tracking
"""

from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE
from waterrocketpy.rocket.builder import RocketBuilder, create_standard_rocket
from waterrocketpy.core.simulation import WaterRocketSimulator
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Callable, Tuple, Optional
from dataclasses import dataclass
from itertools import combinations
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# Add the package to the path (for development)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@dataclass
class ParameterConfig:
    """Configuration for a parameter to explore."""

    name: str
    base_value: float
    min_factor: float = 0.5  # minimum as factor of base value
    max_factor: float = 2.0  # maximum as factor of base value
    num_points: int = 10  # number of points to sample
    unit: str = ""  # unit for display

    @property
    def min_value(self) -> float:
        return self.base_value * self.min_factor

    @property
    def max_value(self) -> float:
        return self.base_value * self.max_factor

    @property
    def values(self) -> np.ndarray:
        return np.linspace(self.min_value, self.max_value, self.num_points)


@dataclass
class ExplorationResult:
    """Results from parameter exploration."""

    parameter_names: List[str]
    parameter_values: Dict[str, np.ndarray]
    target_values: np.ndarray
    target_name: str
    target_unit: str
    base_target_value: float
    sensitivity_analysis: Dict[str, float]


class ParameterExplorer:
    """Main class for water rocket parameter exploration."""

    def __init__(self,verbose: bool = False):
        self.verbose = verbose  # Enable verbose output for debugging
        self.simulator = WaterRocketSimulator(verbose=self.verbose)
        

        # Define available target extractors
        self.target_extractors = {
            "apogee": ("max_altitude", "m", "Maximum Altitude"),
            "max_velocity": ("max_velocity", "m/s", "Maximum Velocity"),
            "flight_time": ("flight_time", "s", "Flight Time"),
            "water_depletion_time": (
                "water_depletion_time",
                "s",
                "Water Depletion Time",
            ),
            "air_depletion_time": (
                "air_depletion_time",
                "s",
                "Air Depletion Time",
            ),
        }

        # Define parameter mappings - maps explorer parameter names to simulation parameter keys
        # Format: 'explorer_name': ('sim_param_key', 'display_name', 'unit',
        # default_range)
        self.parameter_mappings = {
            # Pressure and initial conditions
            "initial_pressure": (
                "P0",
                "Initial Pressure",
                "Pa",
                {"min_factor": 0.3, "max_factor": 3.0},
            ),
            "pressure": (
                "P0",
                "Initial Pressure",
                "Pa",
                {"min_factor": 0.3, "max_factor": 3.0},
            ),  # alias
            # Water and mass parameters
            "water_fraction": (
                "water_fraction",
                "Water Fraction",
                "-",
                {"min_factor": 0.3, "max_factor": 2.5},
            ),
            # Nozzle parameters
            "nozzle_area": (
                "A_nozzle",
                "Nozzle Area",
                "m²",
                {"min_factor": 0.4, "max_factor": 3.0},
            ),
            "nozzle_diameter": (
                "A_nozzle",
                "Nozzle Diameter",
                "m",
                {
                    "min_factor": 0.5,
                    "max_factor": 2.5,
                    "convert_func": self._diameter_to_area,
                },
            ),
            "nozzle_discharge_coefficient": (
                "C_d",
                "Nozzle Discharge Coefficient",
                "-",
                {"min_factor": 0.5, "max_factor": 1.5},
            ),
            # Bottle parameters
            "bottle_volume": (
                "V_bottle",
                "Bottle Volume",
                "m³",
                {"min_factor": 0.5, "max_factor": 2.0},
            ),
            # Mass parameters
            "empty_mass": (
                "m_empty",
                "Empty Mass",
                "kg",
                {"min_factor": 0.5, "max_factor": 2.0},
            ),
            # Aerodynamic parameters
            "drag_coefficient": (
                "C_drag",
                "Drag Coefficient",
                "-",
                {"min_factor": 0.3, "max_factor": 3.0},
            ),
            "reference_area": (
                "A_rocket",
                "Reference Area",
                "m²",
                {"min_factor": 0.5, "max_factor": 2.0},
            ),
            "rocket_diameter": (
                "A_rocket",
                "Rocket Diameter",
                "m",
                {
                    "min_factor": 0.7,
                    "max_factor": 1.5,
                    "convert_func": self._diameter_to_area,
                },
            ),
            # Liquid gas
            "liquid_gas_mass": (
                "liquid_gas_mass",
                "Liquid Gas Mass",
                "kg",
                {"min_factor": 0.0, "max_factor": 10.0},
            ),
        }

    def _diameter_to_area(self, diameter: float) -> float:
        """Convert diameter to circular area."""
        return np.pi * (diameter / 2) ** 2

    def _update_parameter(
        self, params: Dict[str, Any], explorer_param_name: str, value: float
    ):
        """Generic parameter updater using the parameter mappings."""
        if explorer_param_name not in self.parameter_mappings:
            raise ValueError(f"Unknown parameter: {explorer_param_name}")

        mapping = self.parameter_mappings[explorer_param_name]
        sim_param_key = mapping[0]

        # Apply conversion function if specified
        if len(mapping) > 4 and "convert_func" in mapping[4]:
            convert_func = mapping[4]["convert_func"]
            converted_value = convert_func(value)
        else:
            converted_value = value

        # Apply parameter-specific constraints
        if explorer_param_name == "water_fraction":
            converted_value = np.clip(converted_value, 0.01, 0.99)
        elif "area" in explorer_param_name.lower():
            converted_value = max(
                converted_value, 1e-6
            )  # Prevent zero/negative areas
        elif "mass" in explorer_param_name.lower():
            converted_value = max(
                converted_value, 0.0
            )  # Prevent negative mass
        elif "pressure" in explorer_param_name.lower():
            converted_value = max(
                converted_value, ATMOSPHERIC_PRESSURE
            )  # Minimum atmospheric pressure

        # Debug output
        old_value = params.get(sim_param_key, "NOT FOUND")
        if(self.verbose):
            print(f"Debug - Updating {explorer_param_name} -> {sim_param_key}")
            print(f"Debug - Old value: {old_value}")
            print(f"Debug - New value: {converted_value}") 


        params[sim_param_key] = converted_value

    def extract_base_parameters(self, rocket) -> Dict[str, float]:
        """Extract base parameter values from a rocket configuration."""
        # Convert rocket to simulation parameters to get the base values
        builder = RocketBuilder.from_dict(rocket.__dict__)
        sim_params = builder.to_simulation_params()

        base_params = {}

        print("Debug - Available simulation parameters:")
        for key, value in sim_params.items():
            print(f"  {key}: {value}")

        # Extract parameters based on our mappings
        for (
            explorer_param_name,
            mapping_info,
        ) in self.parameter_mappings.items():
            sim_param_key = mapping_info[0]

            if sim_param_key in sim_params:
                value = sim_params[sim_param_key]

                # Convert area back to diameter if needed
                if (
                    "diameter" in explorer_param_name
                    and "area" in sim_param_key.lower()
                ):
                    # Convert area to diameter: A = π(d/2)², so d = 2√(A/π)
                    value = 2 * np.sqrt(value / np.pi)

                base_params[explorer_param_name] = value

        print("\nDebug - Extracted base parameters:")
        for key, value in base_params.items():
            print(f"  {key}: {value}")

        return base_params

    def create_parameter_configs(
        self,
        base_params: Dict[str, float],
        parameter_names: List[str],
        custom_ranges: Dict[str, Dict] = None,
    ) -> Dict[str, ParameterConfig]:
        """Create parameter configurations for exploration."""
        configs = {}

        for param_name in parameter_names:
            if param_name not in base_params:
                raise ValueError(
                    f"Parameter '{param_name}' not found in base parameters. Available: {list(base_params.keys())}"
                )

            if param_name not in self.parameter_mappings:
                raise ValueError(
                    f"Parameter '{param_name}' not defined in parameter mappings. Available: {list(self.parameter_mappings.keys())}"
                )

            # Get mapping info
            mapping = self.parameter_mappings[param_name]
            sim_param_key, display_name, unit = mapping[:3]
            default_range = mapping[4] if len(mapping) > 4 else {}

            # Apply custom ranges if provided
            if custom_ranges and param_name in custom_ranges:
                range_config = {**default_range, **custom_ranges[param_name]}
            else:
                range_config = default_range

            configs[param_name] = ParameterConfig(
                name=param_name,
                base_value=base_params[param_name],
                unit=unit,
                **{
                    k: v
                    for k, v in range_config.items()
                    if k != "convert_func"
                },
            )

        return configs

    def simulate_single_point(
        self,
        base_rocket,
        param_values: Dict[str, float],
        sim_settings: Dict[str, Any] = None,
    ) -> Optional[Any]:
        """Simulate a single parameter point."""
        try:
            # Create a copy of the base rocket parameters
            builder = RocketBuilder.from_dict(base_rocket.__dict__)
            sim_params = builder.to_simulation_params()
            if(self.verbose):
                print(f"Debug - Simulating with param_values: {param_values}")
                print(
                    f"Debug - Original sim_params keys: {list(sim_params.keys())}"
                )

            # Update parameters using the generic updater
            for param_name, value in param_values.items():
                self._update_parameter(sim_params, param_name, value)
            if(self.verbose):
                print(
                    f"Debug - Updated sim_params keys: {list(sim_params.keys())}"
                )

            # Default simulation settings
            if sim_settings is None:
                sim_settings = {
                    "max_time": 15.0,
                    "time_step": 0.01,
                    "solver": "RK45",
                }

            # Run simulation
            flight_data = self.simulator.simulate(sim_params, sim_settings)
            return flight_data

        except Exception as e:
            warnings.warn(
                f"Simulation failed for parameters {param_values}: {e}"
            )
            print(f"Debug - Exception details: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def explore_single_parameter(
        self,
        base_rocket,
        param_config: ParameterConfig,
        target: str = "apogee",
        sim_settings: Dict[str, Any] = None,
    ) -> ExplorationResult:
        """Explore a single parameter."""
        print(f"Exploring parameter: {param_config.name}")

        target_attr, target_unit, target_display = self.target_extractors[
            target
        ]

        # Get base target value
        base_flight_data = self.simulate_single_point(
            base_rocket, {}, sim_settings
        )
        if base_flight_data is None:
            raise RuntimeError("Base simulation failed")
        base_target_value = getattr(base_flight_data, target_attr)

        # Explore parameter range
        target_values = []
        valid_param_values = []

        for param_value in param_config.values:
            flight_data = self.simulate_single_point(
                base_rocket, {param_config.name: param_value}, sim_settings
            )

            if flight_data is not None:
                target_values.append(getattr(flight_data, target_attr))
                valid_param_values.append(param_value)
            else:
                target_values.append(np.nan)
                valid_param_values.append(param_value)

        # Calculate sensitivity (numerical derivative at base value)
        sensitivity = self._calculate_sensitivity(
            base_rocket, param_config, target, base_target_value, sim_settings
        )

        return ExplorationResult(
            parameter_names=[param_config.name],
            parameter_values={param_config.name: np.array(valid_param_values)},
            target_values=np.array(target_values),
            target_name=target_display,
            target_unit=target_unit,
            base_target_value=base_target_value,
            sensitivity_analysis={param_config.name: sensitivity},
        )

    def explore_multiple_parameters(
        self,
        base_rocket,
        param_configs: Dict[str, ParameterConfig],
        target: str = "apogee",
        sim_settings: Dict[str, Any] = None,
        use_parallel: bool = True,
    ) -> List[ExplorationResult]:
        """Explore multiple parameters with pairwise combinations."""

        print(
            f"Exploring {len(param_configs)} parameters: {list(param_configs.keys())}"
        )

        target_attr, target_unit, target_display = self.target_extractors[
            target
        ]

        # Get base target value
        base_flight_data = self.simulate_single_point(
            base_rocket, {}, sim_settings
        )
        if base_flight_data is None:
            raise RuntimeError("Base simulation failed")
        base_target_value = getattr(base_flight_data, target_attr)

        results = []
        param_names = list(param_configs.keys())

        # Generate all pairwise combinations
        for param1_name, param2_name in combinations(param_names, 2):
            print(f"  Exploring pair: {param1_name} vs {param2_name}")

            param1_config = param_configs[param1_name]
            param2_config = param_configs[param2_name]

            # Create parameter grids
            p1_values = param1_config.values
            p2_values = param2_config.values
            P1, P2 = np.meshgrid(p1_values, p2_values)

            target_grid = np.full_like(P1, np.nan)

            # Simulate all combinations
            total_sims = P1.size
            completed_sims = 0

            for i in range(P1.shape[0]):
                for j in range(P1.shape[1]):
                    param_values = {
                        param1_name: P1[i, j],
                        param2_name: P2[i, j],
                    }

                    flight_data = self.simulate_single_point(
                        base_rocket, param_values, sim_settings
                    )

                    if flight_data is not None:
                        target_grid[i, j] = getattr(flight_data, target_attr)

                    completed_sims += 1
                    if completed_sims % 10 == 0:
                        print(
                            f"    Progress: {completed_sims}/{total_sims} ({100*completed_sims/total_sims:.1f}%)"
                        )

            # Calculate sensitivities for both parameters
            sensitivity1 = self._calculate_sensitivity(
                base_rocket,
                param1_config,
                target,
                base_target_value,
                sim_settings,
            )
            sensitivity2 = self._calculate_sensitivity(
                base_rocket,
                param2_config,
                target,
                base_target_value,
                sim_settings,
            )

            results.append(
                ExplorationResult(
                    parameter_names=[param1_name, param2_name],
                    parameter_values={
                        param1_name: p1_values,
                        param2_name: p2_values,
                    },
                    target_values=target_grid,
                    target_name=target_display,
                    target_unit=target_unit,
                    base_target_value=base_target_value,
                    sensitivity_analysis={
                        param1_name: sensitivity1,
                        param2_name: sensitivity2,
                    },
                )
            )

        return results

    def _calculate_sensitivity(
        self,
        base_rocket,
        param_config: ParameterConfig,
        target: str,
        base_target_value: float,
        sim_settings: Dict[str, Any] = None,
    ) -> float:
        """Calculate sensitivity (numerical derivative) of target with respect to parameter."""
        target_attr, _, _ = self.target_extractors[target]

        # Small perturbation (1% of base value)
        delta = param_config.base_value * 0.01

        # Simulate with positive perturbation
        plus_flight_data = self.simulate_single_point(
            base_rocket,
            {param_config.name: param_config.base_value + delta},
            sim_settings,
        )

        # Simulate with negative perturbation
        minus_flight_data = self.simulate_single_point(
            base_rocket,
            {param_config.name: param_config.base_value - delta},
            sim_settings,
        )

        if plus_flight_data is not None and minus_flight_data is not None:
            plus_value = getattr(plus_flight_data, target_attr)
            minus_value = getattr(minus_flight_data, target_attr)

            # Central difference
            sensitivity = (plus_value - minus_value) / (2 * delta)
        else:
            # Fallback to one-sided difference
            if plus_flight_data is not None:
                plus_value = getattr(plus_flight_data, target_attr)
                sensitivity = (plus_value - base_target_value) / delta
            elif minus_flight_data is not None:
                minus_value = getattr(minus_flight_data, target_attr)
                sensitivity = (base_target_value - minus_value) / delta
            else:
                sensitivity = 0.0

        return sensitivity

    def plot_results(
        self, results: List[ExplorationResult], save_plots: bool = False
    ):
        """Create plots for exploration results."""

        for i, result in enumerate(results):
            if len(result.parameter_names) == 1:
                self._plot_single_parameter(result, save_plots, i)
            elif len(result.parameter_names) == 2:
                self._plot_two_parameters(result, save_plots, i)

    def _plot_single_parameter(
        self, result: ExplorationResult, save_plots: bool, plot_idx: int
    ):
        """Plot results for single parameter exploration."""
        param_name = result.parameter_names[0]
        param_values = result.parameter_values[param_name]

        plt.figure(figsize=(10, 6))

        # Remove NaN values for plotting
        mask = ~np.isnan(result.target_values)
        x_vals = param_values[mask]
        y_vals = result.target_values[mask]

        plt.plot(x_vals, y_vals, "o-", linewidth=2, markersize=6)
        plt.axhline(
            y=result.base_target_value,
            color="red",
            linestyle="--",
            alpha=0.7,
            label="Base Value",
        )

        plt.xlabel(f'{param_name.replace("_", " ").title()}')
        plt.ylabel(f"{result.target_name} ({result.target_unit})")
        plt.title(
            f'{result.target_name} vs {param_name.replace("_", " ").title()}'
        )
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Add sensitivity annotation
        sensitivity = result.sensitivity_analysis[param_name]
        plt.text(
            0.05,
            0.95,
            f"Sensitivity: {sensitivity:.2e} {result.target_unit}/unit",
            transform=plt.gca().transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        plt.tight_layout()

        if save_plots:
            plt.savefig(
                f"parameter_exploration_{plot_idx}_{param_name}.png",
                dpi=300,
                bbox_inches="tight",
            )

        plt.show()

    def _plot_two_parameters(
        self, result: ExplorationResult, save_plots: bool, plot_idx: int
    ):
        """Plot results for two parameter exploration."""
        param1_name, param2_name = result.parameter_names
        param1_values = result.parameter_values[param1_name]
        param2_values = result.parameter_values[param2_name]

        # Create 2D contour plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Contour plot
        P1, P2 = np.meshgrid(param1_values, param2_values)
        contour = ax1.contour(
            P1,
            P2,
            result.target_values,
            levels=15,
            colors="black",
            alpha=0.5,
            linewidths=0.5,
        )
        contourf = ax1.contourf(
            P1, P2, result.target_values, levels=20, cmap="viridis", alpha=0.8
        )
        ax1.clabel(contour, inline=True, fontsize=8)

        cbar1 = plt.colorbar(contourf, ax=ax1)
        cbar1.set_label(f"{result.target_name} ({result.target_unit})")

        ax1.set_xlabel(f'{param1_name.replace("_", " ").title()}')
        ax1.set_ylabel(f'{param2_name.replace("_", " ").title()}')
        ax1.set_title(f"{result.target_name} Contour Map")
        ax1.grid(True, alpha=0.3)

        # 3D surface plot
        from mpl_toolkits.mplot3d import Axes3D

        ax2 = fig.add_subplot(122, projection="3d")

        surface = ax2.plot_surface(
            P1, P2, result.target_values, cmap="viridis", alpha=0.8
        )
        ax2.set_xlabel(f'{param1_name.replace("_", " ").title()}')
        ax2.set_ylabel(f'{param2_name.replace("_", " ").title()}')
        ax2.set_zlabel(f"{result.target_name} ({result.target_unit})")
        ax2.set_title(f"{result.target_name} Surface")

        cbar2 = plt.colorbar(surface, ax=ax2, shrink=0.5)
        cbar2.set_label(f"{result.target_name} ({result.target_unit})")

        plt.tight_layout()

        if save_plots:
            plt.savefig(
                f"parameter_exploration_{plot_idx}_{param1_name}_{param2_name}.png",
                dpi=300,
                bbox_inches="tight",
            )

        plt.show()

    def get_available_parameters(self) -> Dict[str, str]:
        """Get list of available parameters and their descriptions."""
        available = {}
        for param_name, mapping in self.parameter_mappings.items():
            sim_param_key, display_name, unit = mapping[:3]
            available[param_name] = (
                f"{display_name} ({unit}) -> {sim_param_key}"
            )
        return available

    def add_parameter_mapping(
        self,
        explorer_name: str,
        sim_param_key: str,
        display_name: str,
        unit: str,
        range_config: Dict = None,
        convert_func: Callable = None,
    ):
        """Add a new parameter mapping for exploration.

        Args:
            explorer_name: Name used in the explorer (e.g., 'nozzle_diameter')
            sim_param_key: Key in simulation parameters (e.g., 'A_nozzle')
            display_name: Human-readable name for plots
            unit: Unit for display
            range_config: Dictionary with 'min_factor', 'max_factor', etc.
            convert_func: Optional function to convert explorer value to sim value
        """
        mapping = [sim_param_key, display_name, unit]
        if range_config or convert_func:
            config = range_config or {}
            if convert_func:
                config["convert_func"] = convert_func
            mapping.append(config)

        self.parameter_mappings[explorer_name] = tuple(mapping)
        
        
        
        
    def print_sensitivity_analysis(self, results: List[ExplorationResult]):
        """Print sensitivity analysis results."""
        print("\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS")
        print("=" * 60)

        all_sensitivities = {}

        for result in results:
            for param_name, sensitivity in result.sensitivity_analysis.items():
                if param_name not in all_sensitivities:
                    all_sensitivities[param_name] = []
                all_sensitivities[param_name].append(abs(sensitivity))

        # Average sensitivities and sort by magnitude
        avg_sensitivities = {
            name: np.mean(values) for name, values in all_sensitivities.items()
        }
        sorted_params = sorted(
            avg_sensitivities.items(), key=lambda x: x[1], reverse=True
        )

        print(f"\nParameter Sensitivities (for {results[0].target_name}):")
        print("-" * 50)

        for param_name, avg_sensitivity in sorted_params:
            unit = results[0].target_unit
            print(f"{param_name:20s}: {avg_sensitivity:12.2e} {unit}/unit")

        # Relative importance
        max_sensitivity = (
            max(avg_sensitivities.values()) if avg_sensitivities else 1
        )

        print(
            f"\nRelative Importance (normalized to most sensitive parameter):"
        )
        print("-" * 50)

        for param_name, avg_sensitivity in sorted_params:
            relative = avg_sensitivity / max_sensitivity * 100
            print(f"{param_name:20s}: {relative:6.1f}%")

def main():
    """Example usage of the parameter explorer."""

    print("=== Water Rocket Parameter Explorer ===\n")

    # Create base rocket configuration
    print("1. Creating base rocket configuration...")
    base_rocket = create_standard_rocket()
    print(f"   Base rocket: {base_rocket.name}")

    # Initialize explorer
    explorer = ParameterExplorer()

    # Extract base parameters
    base_params = explorer.extract_base_parameters(base_rocket)
    print("\n2. Base parameters:")
    for name, value in base_params.items():
        print(f"   {name}: {value}")

    # Define parameters to explore - now using correct parameter names
    parameters_to_explore = [
        "initial_pressure",
        "water_fraction",
        "nozzle_diameter",
    ]
    target_metric = "apogee"

    print(f"\n3. Available parameters:")
    available_params = explorer.get_available_parameters()
    for name, description in available_params.items():
        print(f"   {name}: {description}")

    print(f"\n4. Exploring parameters: {parameters_to_explore}")
    print(f"   Target metric: {target_metric}")

    # Create parameter configurations
    param_configs = explorer.create_parameter_configs(
        base_params,
        parameters_to_explore,
        custom_ranges={
            "initial_pressure": {
                "min_factor": 0.4,
                "max_factor": 2.5,
                "num_points": 8,
            },
            "water_fraction": {
                "min_factor": 0.5,
                "max_factor": 1.8,
                "num_points": 8,
            },
            "nozzle_diameter": {
                "min_factor": 0.6,
                "max_factor": 2.0,
                "num_points": 8,
            },
        },
    )

    # Run exploration
    print("\n5. Running parameter exploration...")
    results = explorer.explore_multiple_parameters(
        base_rocket,
        param_configs,
        target=target_metric,
        sim_settings={"max_time": 20.0, "time_step": 0.01},
    )

    # Display results
    print(f"\n6. Generated {len(results)} result sets")

    # Create plots
    print("\n7. Creating plots...")
    explorer.plot_results(results)

    # Print sensitivity analysis
    explorer.print_sensitivity_analysis(results)

    print("\nExploration complete!")


if __name__ == "__main__":
    main()
