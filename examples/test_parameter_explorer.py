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
import matplotlib.pyplot as plt

# Add the package to the path (for development)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder, create_standard_rocket
from waterrocketpy.visualization.parameter_explorer import ParameterExplorer
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE


def main():
    """Run a comprehensive parameter exploration example."""
    
    print("=== Water Rocket Parameter Exploration Example ===\n")
    
    # 1. Create base rocket configuration
    print("1. Creating base rocket configuration...")
    base_rocket = create_standard_rocket()
    print(f"   Base rocket: {base_rocket.name}")
    
    # Initialize the parameter explorer
    explorer = ParameterExplorer()
    
    # 2. Extract and display base parameters
    print("\n2. Extracting base parameters from rocket...")
    base_params = explorer.extract_base_parameters(base_rocket)
    
    print("   Base parameter values:")
    for name, value in base_params.items():
        unit_map = {
            'pressure': f'Pa ({value/ATMOSPHERIC_PRESSURE:.1f} bar)',
            'water_fraction': f'({value*100:.1f}%)',
            'nozzle_diameter': f'm ({value*1000:.1f} mm)',
            'bottle_volume': f'm³ ({value*1000:.1f} L)',
            'bottle_diameter': f'm ({value*100:.1f} cm)',
            'empty_mass': f'kg ({value*1000:.0f} g)',
            'drag_coefficient': ''
        }
        unit_str = unit_map.get(name, '')
        print(f"     {name:16s}: {value:8.4f} {unit_str}")
    
    # 3. Define exploration scenario
    print("\n3. Setting up parameter exploration...")
    
    # Choose parameters to explore (start with 3 most impactful ones)
    # Now this will work correctly!
    parameters_to_explore = ['initial_pressure', 'water_fraction', 'nozzle_diameter']

    # The script will properly map these to P0, water_fraction, and A_nozzle
    # and you should see all parameters affecting the apogee as expected!
    target_metric = 'apogee'  # Primary target: maximum altitude
    
    print(f"   Parameters to explore: {parameters_to_explore}")
    print(f"   Target metric: {target_metric}")
    
    # 4. Configure parameter ranges with reasonable bounds
    print("\n4. Configuring parameter ranges...")
    
    custom_ranges = {
        'pressure': {
            'min_factor': 0.5,    # 50% of base pressure (4 bar if base is 8 bar)
            'max_factor': 2.0,    # 200% of base pressure (16 bar)
            'num_points': 8,      # 8 sample points
            'unit': 'Pa'
        },
        'water_fraction': {
            'min_factor': 0.6,    # 60% of base water fraction
            'max_factor': 1.8,    # 180% of base (but capped at 99%)
            'num_points': 8,
            'unit': '%'
        },
        'nozzle_diameter': {
            'min_factor': 0.6,    # 60% of base nozzle diameter
            'max_factor': 2.0,    # 200% of base
            'num_points': 8,
            'unit': 'mm'
        }
    }
    
    param_configs = explorer.create_parameter_configs(
        base_params, 
        parameters_to_explore,
        custom_ranges
    )
    
    # Display the ranges that will be explored
    for param_name, config in param_configs.items():
        print(f"   {param_name}:")
        print(f"     Range: {config.min_value:.4f} to {config.max_value:.4f} {config.unit}")
        print(f"     Points: {config.num_points}")
    
    # 5. Run the parameter exploration
    print(f"\n5. Running parameter exploration...")
    print(f"   This will generate {len(parameters_to_explore)*(len(parameters_to_explore)-1)//2} parameter pair combinations")
    print(f"   Total simulations: ~{sum(config.num_points**2 for config in param_configs.values()) // len(param_configs)}")
    
    # Use slightly extended simulation time for better results
    sim_settings = {
        'max_time': 25.0,     # Extended time to capture full flight
        'time_step': 0.01,    # Good balance of accuracy and speed
        'solver': 'RK45'      # Robust ODE solver
    }
    
    results = explorer.explore_multiple_parameters(
        base_rocket, 
        param_configs, 
        target=target_metric,
        sim_settings=sim_settings
    )
    
    # 6. Display basic results summary
    print(f"\n6. Exploration completed!")
    print(f"   Generated {len(results)} parameter combination results")
    
    # Get base target value for reference
    base_flight_data = explorer.simulate_single_point(base_rocket, {}, sim_settings)
    if base_flight_data:
        base_apogee = base_flight_data.max_altitude
        print(f"   Base rocket apogee: {base_apogee:.2f} m")
    
    # 7. Create visualizations
    print("\n7. Creating visualization plots...")
    explorer.plot_results(results, save_plots=False)  # Set to True to save plots
    
    # 8. Print detailed sensitivity analysis
    print("\n8. Sensitivity Analysis Results:")
    explorer.print_sensitivity_analysis(results)
    
    # 9. Optional: Demonstrate single parameter exploration
    print("\n9. Bonus: Single parameter exploration example...")
    demonstrate_single_parameter_exploration(explorer, base_rocket, param_configs, sim_settings)
    
    print("\n=== Parameter exploration complete! ===")
    print("\nKey takeaways:")
    print("- Check the sensitivity analysis to see which parameters matter most")
    print("- Use the contour plots to find optimal parameter combinations")
    print("- The 3D surface plots show the parameter interaction effects")


def demonstrate_single_parameter_exploration(explorer, base_rocket, param_configs, sim_settings):
    """Demonstrate single parameter exploration for comparison."""
    
    # Explore just pressure with more detail
    pressure_config = param_configs['pressure']
    pressure_config.num_points = 15  # More points for smoother curve
    
    print(f"   Exploring pressure in detail ({pressure_config.num_points} points)...")
    
    single_result = explorer.explore_single_parameter(
        base_rocket,
        pressure_config,
        target='apogee',
        sim_settings=sim_settings
    )
    
    # Plot single parameter result
    explorer.plot_results([single_result])
    
    print(f"   Pressure sensitivity: {single_result.sensitivity_analysis['pressure']:.2f} m/Pa")


def compare_target_metrics():
    """Optional function to compare different target metrics."""
    
    print("\n=== Bonus: Comparing Different Target Metrics ===")
    
    explorer = ParameterExplorer()
    base_rocket = create_standard_rocket()
    base_params = explorer.extract_base_parameters(base_rocket)
    
    # Simple single parameter exploration for different targets
    pressure_config = explorer.create_parameter_configs(
        base_params, 
        ['pressure'],
        {'pressure': {'min_factor': 0.5, 'max_factor': 2.0, 'num_points': 10}}
    )['pressure']
    
    targets = ['apogee', 'max_velocity', 'flight_time']
    
    plt.figure(figsize=(15, 5))
    
    for i, target in enumerate(targets, 1):
        result = explorer.explore_single_parameter(
            base_rocket, 
            pressure_config, 
            target=target
        )
        
        plt.subplot(1, 3, i)
        param_values = result.parameter_values['pressure']
        mask = ~np.isnan(result.target_values)
        
        plt.plot(param_values[mask]/ATMOSPHERIC_PRESSURE, result.target_values[mask], 'o-')
        plt.axhline(y=result.base_target_value, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('Pressure (bar)')
        plt.ylabel(f'{result.target_name} ({result.target_unit})')
        plt.title(f'{result.target_name} vs Pressure')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    print("Different metrics respond differently to pressure changes!")


if __name__ == "__main__":
    main()
    
    # Uncomment to see comparison of different target metrics
    # compare_target_metrics()