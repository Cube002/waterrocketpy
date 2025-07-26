#!/usr/bin/env python3
"""
Comprehensive flight data visualization script for water rocket simulation.
Creates multiple organized plots showing all aspects of the rocket's flight performance.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from waterrocketpy.core.simulation import WaterRocketSimulator
    from waterrocketpy.rocket.builder import RocketBuilder, create_standard_rocket, create_standard_IPT_rocket
    from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE, INITIAL_TEMPERATURE
    from waterrocketpy.visualization.plot_flight_data import (
        setup_plot_style,
        identify_flight_phases,
        plot_trajectory_and_velocity,
        plot_forces_and_acceleration,
        plot_propellant_and_pressure,
        plot_exhaust_properties,
        plot_air_exit_conditions,
        print_flight_summary)
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure you're running this from the correct directory.")
    sys.exit(1)


def get_next_run_directory(base_dir="Plots", prefix="run_"):
    """Finds the next available indexed run directory like run_001, run_002, etc."""
    os.makedirs(base_dir, exist_ok=True)
    existing = [d for d in os.listdir(base_dir) if d.startswith(prefix) and d[len(prefix):].isdigit()]
    indices = [int(d[len(prefix):]) for d in existing]
    next_index = max(indices, default=0) + 1
    run_dir = os.path.join(base_dir, f"{prefix}{next_index:03d}")
    os.makedirs(run_dir)
    return run_dir

def main():
    """Main function to run simulation and create all plots."""
    print("Water Rocket Flight Data Visualization")
    print("=" * 50)

    # Setup plotting style
    setup_plot_style()

    # Prepare output folder
    output_dir = get_next_run_directory()
    print(f"✓ Output directory created: {output_dir}")

    try:
        # Create and run simulation
        print("1. Creating standard rocket...")
        rocket = create_standard_IPT_rocket()
        print(f"   ✓ Rocket created: {rocket.name}")

        print("2. Setting up simulation...")
        builder = RocketBuilder.from_dict(rocket.__dict__)
        sim_params = builder.to_simulation_params()

        simulator = WaterRocketSimulator()
        sim_settings = {"max_time": 100.0, "time_step": 0.01, "solver": "RK45"}

        print("3. Running simulation...")
        flight_data = simulator.simulate(sim_params, sim_settings)
        print(f"   ✓ Simulation completed! {len(flight_data.time)} data points generated")

        # Identify flight phases
        print("4. Analyzing flight phases...")
        phases = identify_flight_phases(flight_data)

        # Print summary to terminal
        print_flight_summary(flight_data, phases)

        # Save simulation parameters to file
        params_file = os.path.join(output_dir, "simulation_parameters.txt")
        with open(params_file, "w") as f:
            f.write("=== Rocket Parameters ===\n")
            for key, value in rocket.__dict__.items():
                f.write(f"{key}: {value}\n")

            f.write("\n=== Simulation Settings ===\n")
            for key, value in sim_settings.items():
                f.write(f"{key}: {value}\n")

        print(f"   ✓ Simulation parameters saved to {params_file}")

        # Generate and save plots
        print("5. Generating and saving plots...")
        plot_funcs = [
            ("trajectory_and_velocity", plot_trajectory_and_velocity),
            ("forces_and_acceleration", plot_forces_and_acceleration),
            ("propellant_and_pressure", plot_propellant_and_pressure),
            ("exhaust_properties", plot_exhaust_properties),
            ("air_exit_conditions", plot_air_exit_conditions),
        ]

        for name, func in plot_funcs:
            print(f"   - Plotting {name.replace('_', ' ')}...")
            fig = func(flight_data, phases)
            fig_path = os.path.join(output_dir, f"{name}.png")
            fig.savefig(fig_path, dpi=300, bbox_inches="tight")
            print(f"     ✓ Saved to {fig_path}")

        print("✓ All plots generated and saved successfully!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()



if __name__ == "__main__":
    main()