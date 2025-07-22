"""
Water Rocket Parameter Optimization using SciPy

This module provides optimization capabilities for water rocket simulations,
allowing you to find optimal parameters for maximum altitude, velocity, or flight time.
"""

import sys
import os
import numpy as np
from scipy.optimize import differential_evolution, minimize
from typing import Dict, List, Tuple, Optional, Callable
import warnings

# Assuming these imports work based on your code structure
from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE


class WaterRocketOptimizer:
    """
    Optimizer for water rocket parameters using SciPy optimization algorithms.
    """

    def __init__(
        self,
        L_cone: float = 0.08,
        material_name: str = "PET",
        simulation_settings: Optional[Dict] = None,
    ):
        """
        Initialize the optimizer with fixed parameters.

        Args:
            L_cone: Nose cone length (fixed parameter)
            material_name: Material name (fixed parameter)
            simulation_settings: Simulation configuration
        """
        self.L_cone = L_cone
        self.material_name = material_name

        # Default simulation settings
        self.simulation_settings = simulation_settings or {
            "max_time": 20,
            "time_step": 0.01,
            "solver": "RK45",
        }

        # Create simulator instance
        self.simulator = WaterRocketSimulator()

        # Cache for avoiding repeated identical simulations
        self._simulation_cache = {}

        # Optimization statistics
        self.n_evaluations = 0
        self.best_result = None
        self.optimization_history = []

    def objective_function(
        self, params: np.ndarray, target: str = "max_altitude"
    ) -> float:
        """
        Objective function for optimization.

        Args:
            params: Array of parameters [L_body, d_body, p_max_bar, nozzle_diameter, water_fraction]
            target: Optimization target ('max_altitude', 'max_velocity', 'flight_time')

        Returns:
            Negative value of the target metric (for minimization)
        """
        L_body, d_body, p_max_bar, nozzle_diameter, water_fraction = params

        # Convert pressure from bar to Pa
        p_max = p_max_bar * ATMOSPHERIC_PRESSURE

        # Create cache key
        cache_key = tuple(np.round(params, 8))

        if cache_key in self._simulation_cache:
            flight_data = self._simulation_cache[cache_key]
        else:
            try:
                # Build rocket configuration
                builder = RocketBuilder()
                config = (
                    builder.build_from_dimensions(
                        L_body=L_body,
                        L_cone=self.L_cone,
                        d_body=d_body,
                        p_max=p_max,
                        nozzle_diameter=nozzle_diameter,
                        material_name=self.material_name,
                        water_fraction=water_fraction,
                    )
                    .set_metadata(
                        name="Optimization Rocket",
                        description="Rocket being optimized",
                    )
                    .build()
                )

                # Convert to simulation parameters
                builder_from_config = RocketBuilder.from_dict(config.__dict__)
                sim_params = builder_from_config.to_simulation_params()

                # Run simulation
                flight_data = self.simulator.simulate(
                    sim_params, self.simulation_settings
                )

                # Cache the result
                self._simulation_cache[cache_key] = flight_data

            except Exception as e:
                # Return a large penalty for invalid configurations
                warnings.warn(
                    f"Simulation failed with parameters {params}: {e}"
                )
                return 1e6

        self.n_evaluations += 1

        # Extract target metric
        if target == "max_altitude":
            result = flight_data.max_altitude
        elif target == "max_velocity":
            result = flight_data.max_velocity
        elif target == "flight_time":
            result = flight_data.flight_time
        else:
            raise ValueError(f"Unknown target: {target}")

        # Store optimization history
        self.optimization_history.append(
            {
                "evaluation": self.n_evaluations,
                "params": params.copy(),
                "result": result,
                "target": target,
            }
        )

        # Update best result
        if self.best_result is None or result > self.best_result["result"]:
            self.best_result = {
                "params": params.copy(),
                "result": result,
                "target": target,
                "flight_data": flight_data,
            }
            print(
                f"New best {target}: {result:.4f} at evaluation {self.n_evaluations}"
            )
            print(
                f"  Params: L_body={params[0]:.3f}, d_body={params[1]:.3f}, "
                f"p_max={params[2]:.1f}bar, nozzle_d={params[3]:.4f}, "
                f"water_frac={params[4]:.3f}"
            )

        # Return negative for minimization
        return -result

    def optimize(
        self,
        bounds: List[Tuple[float, float]],
        target: str = "max_altitude",
        method: str = "differential_evolution",
        **optimizer_kwargs,
    ) -> Dict:
        """
        Optimize rocket parameters.

        Args:
            bounds: List of (min, max) tuples for each parameter
                   [L_body, d_body, p_max_bar, nozzle_diameter, water_fraction]
            target: Optimization target ('max_altitude', 'max_velocity', 'flight_time')
            method: Optimization method ('differential_evolution' or 'minimize')
            **optimizer_kwargs: Additional arguments passed to the optimizer

        Returns:
            Optimization result dictionary
        """
        print(f"Starting optimization for {target} using {method}")
        print(f"Parameter bounds: {bounds}")

        # Reset optimization statistics
        self.n_evaluations = 0
        self.best_result = None
        self.optimization_history = []
        self._simulation_cache = {}

        # Define objective function with fixed target
        def obj_func(params):
            return self.objective_function(params, target)

        # Set default optimizer parameters
        if method == "differential_evolution":
            default_kwargs = {
                "maxiter": 100,
                "popsize": 15,
                "seed": 42,
                "disp": True,
            }
            default_kwargs.update(optimizer_kwargs)

            result = differential_evolution(obj_func, bounds, **default_kwargs)

        elif method == "minimize":
            # For minimize, we need an initial guess
            x0 = optimizer_kwargs.pop("x0", None)
            if x0 is None:
                # Create initial guess from middle of bounds
                x0 = [(b[0] + b[1]) / 2 for b in bounds]

            default_kwargs = {
                "method": "L-BFGS-B",
                "options": {"disp": True, "maxiter": 100},
            }
            default_kwargs.update(optimizer_kwargs)

            result = minimize(obj_func, x0, bounds=bounds, **default_kwargs)
        else:
            raise ValueError(f"Unknown optimization method: {method}")

        # Prepare result dictionary
        optimization_result = {
            "success": result.success,
            "message": result.message,
            "n_evaluations": self.n_evaluations,
            "best_params": {
                "L_body": result.x[0],
                "d_body": result.x[1],
                "p_max_bar": result.x[2],
                "nozzle_diameter": result.x[3],
                "water_fraction": result.x[4],
            },
            "best_value": -result.fun,
            "target": target,
            "scipy_result": result,
            "best_flight_data": (
                self.best_result["flight_data"] if self.best_result else None
            ),
        }

        print(f"\nOptimization completed!")
        print(f"Best {target}: {optimization_result['best_value']:.4f}")
        print(f"Best parameters:")
        for param, value in optimization_result["best_params"].items():
            print(f"  {param}: {value:.4f}")

        return optimization_result

    def get_default_bounds(self) -> List[Tuple[float, float]]:
        """
        Get reasonable default bounds for optimization parameters.

        Returns:
            List of (min, max) bounds for [L_body, d_body, p_max_bar, nozzle_diameter, water_fraction]
        """
        return [
            (0.1, 0.5),  # L_body: 10-50 cm
            (0.05, 0.12),  # d_body: 5-12 cm diameter
            (2.0, 12.0),  # p_max_bar: 2-12 bar
            (0.005, 0.025),  # nozzle_diameter: 5-25 mm
            (0.1, 0.8),  # water_fraction: 10-80%
        ]


# Convenience functions for common use cases
def optimize_for_altitude(
    bounds: Optional[List[Tuple[float, float]]] = None,
    method: str = "differential_evolution",
    **kwargs,
) -> Dict:
    """Optimize rocket for maximum altitude."""
    optimizer = WaterRocketOptimizer()
    if bounds is None:
        bounds = optimizer.get_default_bounds()
    return optimizer.optimize(
        bounds, target="max_altitude", method=method, **kwargs
    )


def optimize_for_velocity(
    bounds: Optional[List[Tuple[float, float]]] = None,
    method: str = "differential_evolution",
    **kwargs,
) -> Dict:
    """Optimize rocket for maximum velocity."""
    optimizer = WaterRocketOptimizer()
    if bounds is None:
        bounds = optimizer.get_default_bounds()
    return optimizer.optimize(
        bounds, target="max_velocity", method=method, **kwargs
    )


def optimize_for_flight_time(
    bounds: Optional[List[Tuple[float, float]]] = None,
    method: str = "differential_evolution",
    **kwargs,
) -> Dict:
    """Optimize rocket for maximum flight time."""
    optimizer = WaterRocketOptimizer()
    if bounds is None:
        bounds = optimizer.get_default_bounds()
    return optimizer.optimize(
        bounds, target="flight_time", method=method, **kwargs
    )


# Example usage
if __name__ == "__main__":
    # Example 1: Optimize for maximum altitude with default bounds
    print("Example 1: Optimizing for maximum altitude")
    result_altitude = optimize_for_altitude()

    # Example 2: Optimize for maximum velocity with custom bounds
    print("\nExample 2: Optimizing for maximum velocity with custom bounds")
    custom_bounds = [
        (0.15, 0.35),  # L_body: 15-35 cm
        (0.08, 0.10),  # d_body: 8-10 cm (around standard bottle size)
        (6.0, 10.0),  # p_max_bar: 6-10 bar
        (0.008, 0.015),  # nozzle_diameter: 8-15 mm
        (0.2, 0.5),  # water_fraction: 20-50%
    ]
    result_velocity = optimize_for_velocity(bounds=custom_bounds)

    # Example 3: Optimize using minimize method instead of
    # differential_evolution
    print("\nExample 3: Optimizing flight time using minimize method")
    result_flight_time = optimize_for_flight_time(
        method="minimize", x0=[0.25, 0.088, 8.0, 0.01, 0.3]  # Initial guess
    )

    # Example 4: Advanced usage with custom optimizer settings
    print("\nExample 4: Advanced optimization with custom settings")
    optimizer = WaterRocketOptimizer(
        simulation_settings={
            "max_time": 0.5,  # Longer simulation time
            "time_step": 0.005,  # Smaller time step for accuracy
            "solver": "RK45",
        }
    )

    advanced_result = optimizer.optimize(
        bounds=optimizer.get_default_bounds(),
        target="max_altitude",
        method="differential_evolution",
        maxiter=50,  # Fewer iterations for faster testing
        popsize=10,  # Smaller population
    )

    print(f"\nOptimization complete! Check the results above.")
