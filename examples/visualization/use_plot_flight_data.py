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
    from waterrocketpy.rocket.builder import RocketBuilder, create_standard_rocket
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




def main():
    """Main function to run simulation and create all plots."""
    print("Water Rocket Flight Data Visualization")
    print("=" * 50)
    
    # Setup plotting style
    setup_plot_style()
    
    try:
        # Create and run simulation
        print("1. Creating standard rocket...")
        rocket = create_standard_rocket()
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
        
        # Print summary
        print_flight_summary(flight_data, phases)
        
        # Create all plots
        print("5. Generating plots...")
        
        figs = []
        
        print("   - Trajectory and velocity plots...")
        figs.append(plot_trajectory_and_velocity(flight_data, phases))
        
        print("   - Forces and acceleration plots...")
        figs.append(plot_forces_and_acceleration(flight_data, phases))
        
        print("   - Propellant and pressure plots...")
        figs.append(plot_propellant_and_pressure(flight_data, phases))
        
        print("   - Exhaust properties plots...")
        figs.append(plot_exhaust_properties(flight_data, phases))
        
        print("   - Air exit conditions plots...")
        figs.append(plot_air_exit_conditions(flight_data, phases))
        
        # Show all plots
        print("6. Displaying plots...")
        plt.show()
        
        print("✓ All plots generated successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()