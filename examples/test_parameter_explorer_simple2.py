#!/usr/bin/env python3
# examples/test_parameter_explorer_simple.py
"""
Simple example demonstrating water rocket parameter exploration.

This script shows how to:
1. Create a base rocket configuration
2. Set up parameter exploration ranges
3. Run multi-parameter analysis
4. Visualize results with 2D plots and sensitivity analysis
5. Compare different target metrics

Run this from the root of your waterrocketpy package directory.
"""

import sys
import os
import numpy as np

# Add the package to the path (for development)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from waterrocketpy.rocket.builder import create_standard_rocket
from waterrocketpy.visualization.parameter_explorer import ParameterExplorer

def run_simple_test():
    print("=== Simple Water Rocket Parameter Exploration Test ===")

    # Step 1: Create base rocket
    base_rocket = create_standard_rocket()

    # Step 2: Initialize the parameter explorer
    explorer = ParameterExplorer()

    # Step 3: Extract base parameters from rocket
    base_params = explorer.extract_base_parameters(base_rocket)

    # Step 4: Choose one or two parameters to explore
    parameters_to_explore = ['initial_pressure', 'water_fraction']
    target_metric = 'apogee'  # Try also: 'flight_time', 'max_velocity'

    # Step 5: Define custom exploration ranges
    param_configs = explorer.create_parameter_configs(
        base_params,
        parameters_to_explore,
        custom_ranges={
            'initial_pressure': {'min_factor': 0.5, 'max_factor': 2.0, 'num_points': 6},
            'water_fraction': {'min_factor': 0.5, 'max_factor': 1.5, 'num_points': 6}
        }
    )

    # Step 6: Run multi-parameter exploration
    results = explorer.explore_multiple_parameters(
        base_rocket,
        param_configs,
        target=target_metric,
        sim_settings={'max_time': 15.0, 'time_step': 0.01}
    )

    # Step 7: Plot the results
    explorer.plot_results(results)

    # Step 8: Sensitivity summary
    #explorer.print_sensitivity_analysis(results)

    print("\n=== Test Completed ===")

if __name__ == "__main__":
    run_simple_test()
