#!/usr/bin/env python3
# examples/test_parameter_explorer_simple.py
"""
Simple example demonstrating ...

This script shows how to:

Run this from the root of your waterrocketpy package directory.
"""

from waterrocketpy.visualization.parameter_explorer import ParameterExplorer
from waterrocketpy.rocket.builder import RocketBuilder, create_standard_rocket
from waterrocketpy.core.simulation import WaterRocketSimulator
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add the package to the path (for development)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    """Run a simple water rocket simulation example."""

    print("=== Water Rocket Simulation Example ===\n")

    # Method 1: Create a rocket using the builder pattern
    print("1. Creating rocket using builder pattern...")
    # Basic usage example
    explorer = ParameterExplorer()
    base_rocket = create_standard_rocket()

    # Define parameters to explore
    parameters = ["empty_mass", "water_fraction", "nozzle_diameter"]

    # Extract base parameters
    base_params = explorer.extract_base_parameters(base_rocket)
    print("\n2. Base parameters:")
    for name, value in base_params.items():
        print(f"   {name}: {value}")

    # Run exploration
    results = explorer.explore_multiple_parameters(
        base_rocket,
        explorer.create_parameter_configs(base_params, parameters),
        target="apogee",
    )

    # Visualize and analyze
    results[0]
    explorer.print_sensitivity_analysis(results)    
    explorer.plot_results(results)
    print("\n3. Exploration completed successfully!")
    
if __name__ == "__main__":
    main()
