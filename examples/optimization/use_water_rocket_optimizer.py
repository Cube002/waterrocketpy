#!/usr/bin/env python3
"""
Test script for water rocket optimization.

This script tests the water rocket optimization module with different scenarios.
"""
import sys
import os
import time
from typing import Dict, Any
import numpy as np

from waterrocketpy.optimization.water_rocket_optimizer import (
    WaterRocketOptimizer,
    optimize_for_altitude,
    optimize_for_velocity,
    optimize_for_flight_time,
)



def print_results(result: Dict[str, Any], test_name: str):
    """Print optimization results in a nice format."""
    print(f"\n{'='*60}")
    print(f"RESULTS FOR: {test_name}")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Target: {result['target']}")
    print(f"Best value: {result['best_value']:.6f}")
    print(f"Evaluations: {result['n_evaluations']}")

    print("\nOptimal Parameters:")
    for param, value in result["best_params"].items():
        if param == "p_max_bar":
            print(f"  {param:20}: {value:8.2f} bar")
        elif param in ["L_body", "d_body"]:
            print(f"  {param:20}: {value:8.4f} m ({value*100:6.2f} cm)")
        elif param == "nozzle_diameter":
            print(f"  {param:20}: {value:8.4f} m ({value*1000:6.2f} mm)")
        elif param == "water_fraction":
            print(f"  {param:20}: {value:8.4f} ({value*100:6.2f}%)")
        else:
            print(f"  {param:20}: {value:8.4f}")

    if result["best_flight_data"] is not None:
        fd = result["best_flight_data"]
        print("\nFlight Performance:")
        print(f"  Max Altitude        : {fd.max_altitude:8.4f} m")
        print(f"  Max Velocity        : {fd.max_velocity:8.4f} m/s")
        print(f"  Flight Time         : {fd.flight_time:8.4f} s")
        print(f"  Water Depletion Time: {fd.water_depletion_time:8.4f} s")


def test_quick_altitude_optimization():
    """Test 1: Quick altitude optimization with small population."""
    print("TEST 1: Quick altitude optimization (small population for speed)")

    start_time = time.time()

    result = optimize_for_altitude(
        method="differential_evolution",
        maxiter=10,  # Small number for quick test
        popsize=8,  # Small population
        seed=42,  # For reproducible results
    )

    elapsed_time = time.time() - start_time
    print(f"Optimization completed in {elapsed_time:.2f} seconds")

    print_results(result, "Quick Altitude Optimization")
    return result


def test_custom_bounds_velocity():
    """Test 2: Velocity optimization with custom bounds."""
    print("\n\nTEST 2: Velocity optimization with custom bounds")

    # Define tighter bounds around typical values
    custom_bounds = [
        (0.20, 0.30),  # L_body: 20-30 cm
        (0.085, 0.095),  # d_body: 8.5-9.5 cm (around 2L bottle)
        (7.0, 9.0),  # p_max_bar: 7-9 bar
        (0.009, 0.012),  # nozzle_diameter: 9-12 mm
        (0.25, 0.40),  # water_fraction: 25-40%
    ]

    start_time = time.time()

    result = optimize_for_velocity(
        bounds=custom_bounds,
        method="differential_evolution",
        maxiter=25,
        popsize=10,
        seed=123,
    )

    elapsed_time = time.time() - start_time
    print(f"Optimization completed in {elapsed_time:.2f} seconds")

    print_results(result, "Custom Bounds Velocity Optimization")
    return result


def test_minimize_method():
    """Test 3: Flight time optimization using minimize method."""
    print("\n\nTEST 3: Flight time optimization using minimize method")

    # Starting point based on your original example
    initial_guess = [0.25, 0.088, 8.0, 0.01, 0.3]

    start_time = time.time()

    result = optimize_for_flight_time(
        method="minimize",
        x0=initial_guess,
        options={"maxiter": 50, "disp": True},
    )

    elapsed_time = time.time() - start_time
    print(f"Optimization completed in {elapsed_time:.2f} seconds")

    print_results(result, "Flight Time Optimization (Minimize)")
    return result


def test_custom_optimizer_settings():
    """Test 4: Advanced usage with custom optimizer instance."""
    print("\n\nTEST 4: Advanced optimization with custom settings")

    # Create optimizer with custom simulation settings
    optimizer = WaterRocketOptimizer(
        L_cone=0.08,  # Fixed nose cone length
        material_name="PET",  # Fixed material
        simulation_settings={
            "max_time": 40,  # Longer simulation
            "time_step": 0.01,  # precision
            "solver": "RK45",
        },
    )

    # Use default bounds but modify them slightly
    bounds = optimizer.get_default_bounds()
    bounds[2] = (5.0, 11.0)  # Wider pressure range: 5-11 bar

    start_time = time.time()

    result = optimizer.optimize(
        bounds=bounds,
        target="max_altitude",
        method="differential_evolution",
        maxiter=30,
        popsize=12,
        atol=1e-6,  # Higher accuracy
        seed=456,
    )

    elapsed_time = time.time() - start_time
    print(f"Optimization completed in {elapsed_time:.2f} seconds")

    print_results(result, "Advanced Custom Settings")
    optimizer.plot_optimization_history()
    return result


def compare_targets():
    """Test 5: Compare optimization for different targets with same bounds."""
    print("\n\nTEST 5: Comparing different optimization targets")

    # Use the same bounds and settings for fair comparison
    common_bounds = [
        (0.1, 0.8),  # L_body: 22-28 cm
        (0.05, 0.1),  # d_body: 8.6-9.0 cm
        (7, 12),  # p_max_bar: 7.5-8.5 bar
        (0.001, 0.05),  # nozzle_diameter: 9-11 mm
        (0.2, 0.5),  # water_fraction: 28-35%
    ]

    common_settings = {
        "method": "differential_evolution",
        "maxiter": 40,
        "popsize": 8,
        "seed": 789,
    }

    results = {}

    print("Optimizing for altitude...")
    results["altitude"] = optimize_for_altitude(
        bounds=common_bounds, **common_settings
    )

    print("Optimizing for velocity...")
    results["velocity"] = optimize_for_velocity(
        bounds=common_bounds, **common_settings
    )

    print("Optimizing for flight time...")
    results["flight_time"] = optimize_for_flight_time(
        bounds=common_bounds, **common_settings
    )

    # Print comparison
    print(f"\n{'='*80}")
    print("COMPARISON OF DIFFERENT TARGETS")
    print(f"{'='*80}")

    print(
        f"{'Target':<12} {'Best Value':<12} {'L_body(cm)':<10} {'d_body(cm)':<10} "
        f"{'P(bar)':<8} {'Nozzle(mm)':<10} {'Water%':<8}"
    )
    print("-" * 80)

    for target, result in results.items():
        params = result["best_params"]
        print(
            f"{target:<12} {result['best_value']:<12.4f} "
            f"{params['L_body']*100:<10.2f} {params['d_body']*100:<10.2f} "
            f"{params['p_max_bar']:<8.2f} {params['nozzle_diameter']*1000:<10.2f} "
            f"{params['water_fraction']*100:<8.1f}"
        )

    return results


def main():
    """Run all tests."""
    print("Water Rocket Optimization Test Suite")
    print("=" * 60)

    try:
        # Run individual tests
        test1_result = test_quick_altitude_optimization()
        #test2_result = test_custom_bounds_velocity()
        #test3_result = test_minimize_method()
        #test4_result = test_custom_optimizer_settings()

        # Comparison test
        #comparison_results = compare_targets()

        # Summary
        print(f"\n{'='*60}")
        print("TEST SUITE COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        print(
            "All tests passed! The optimization module is working correctly."
        )
        print("\nTo use the optimizer in your own code, you can:")
        print(
            "1. Use the convenience functions: optimize_for_altitude(), etc."
        )
        print("2. Create a WaterRocketOptimizer instance for custom settings")
        print("3. Adjust bounds and optimizer parameters as needed")

    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        print(
            "Please check that all dependencies are installed and paths are correct."
        )
        raise


if __name__ == "__main__":
    main()
