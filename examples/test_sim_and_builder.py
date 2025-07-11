#!/usr/bin/env python3
"""
Simple example demonstrating water rocket simulation using waterrocketpy.

This script shows how to:
1. Create a rocket configuration using the builder pattern
2. Run a simulation with the rocket
3. Display basic results

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
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE


def main():
    """Run a simple water rocket simulation example."""
    
    print("=== Water Rocket Simulation Example ===\n")
    
    # Method 1: Create a rocket using the builder pattern
    print("1. Creating rocket using builder pattern...")
    
    custom_rocket = (RocketBuilder()
                    .set_bottle(volume=0.002, diameter=0.1)  # 2L bottle, 10cm diameter
                    .set_nozzle(diameter=0.015)              # 15mm nozzle
                    .set_mass(empty_mass=0.25, water_fraction=0.33)  # 250g empty, 33% water
                    .set_initial_conditions(pressure=8 * ATMOSPHERIC_PRESSURE)  # 8 bar
                    .set_metadata("Custom Rocket", "Example rocket configuration")
                    .build())
    
    print(f"   Rocket: {custom_rocket.name}")
    print(f"   Water mass: {custom_rocket.water_mass:.3f} kg")
    print(f"   Total mass: {custom_rocket.total_mass:.3f} kg")
    print(f"   Nozzle area: {custom_rocket.nozzle_area*1000:.1f} mm²")
    
    # Method 2: Use a pre-built configuration
    print("\n2. Using pre-built standard rocket...")
    standard_rocket = create_standard_rocket()
    print(f"   Rocket: {standard_rocket.name}")
    
    # Convert rocket configuration to simulation parameters
    print("\n3. Converting to simulation parameters...")
    builder = RocketBuilder.from_dict(standard_rocket.__dict__)
    sim_params = builder.to_simulation_params()
    
    print("   Simulation parameters:")
    for key, value in sim_params.items():
        if isinstance(value, float):
            print(f"     {key}: {value:.6f}")
        else:
            print(f"     {key}: {value}")
    
    # Create simulator and run simulation
    print("\n4. Running simulation...")
    simulator = WaterRocketSimulator()
    
    # Set simulation parameters
    simulation_settings = {
        'max_time': 20.0,      # Maximum simulation time (seconds)
        'time_step': 0.01,     # Time step (seconds)
        'solver': 'RK45'       # ODE solver method
    }
    
    try:
        # Run the simulation
        flight_data = simulator.simulate(sim_params, simulation_settings)
        
        # Display results
        print("\n5. Simulation Results:")
        print(f"   Maximum altitude: {flight_data.max_altitude:.2f} m")
        print(f"   Maximum velocity: {flight_data.max_velocity:.2f} m/s")
        print(f"   Flight time: {flight_data.flight_time:.2f} s")
        print(f"   Water depletion time: {flight_data.water_depletion_time:.2f} s")
        
        # Create simple plots
        print("\n6. Creating plots...")
        create_plots(flight_data)
        
    except Exception as e:
        print(f"   Error during simulation: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


def create_plots(flight_data):
    """Create simple plots of the simulation results."""
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Water Rocket Simulation Results', fontsize=16)
    
    # Plot 1: Altitude vs Time
    ax1.plot(flight_data.time, flight_data.altitude, 'b-', linewidth=2)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Altitude (m)')
    ax1.set_title('Altitude vs Time')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Velocity vs Time
    ax2.plot(flight_data.time, flight_data.velocity, 'r-', linewidth=2)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Velocity (m/s)')
    ax2.set_title('Velocity vs Time')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Water Mass vs Time
    ax3.plot(flight_data.time, flight_data.water_mass, 'g-', linewidth=2)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Water Mass (kg)')
    ax3.set_title('Water Mass vs Time')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Thrust and Drag vs Time
    ax4.plot(flight_data.time, flight_data.thrust, 'orange', linewidth=2, label='Thrust')
    ax4.plot(flight_data.time, flight_data.drag, 'purple', linewidth=2, label='Drag')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Force (N)')
    ax4.set_title('Forces vs Time')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Print some key statistics
    print(f"   Peak thrust: {np.max(flight_data.thrust):.2f} N")
    print(f"   Peak drag: {np.max(flight_data.drag):.2f} N")
    print(f"   Thrust duration: {np.sum(flight_data.thrust > 0) * (flight_data.time[1] - flight_data.time[0]):.2f} s")


def compare_configurations():
    """Compare different rocket configurations."""
    
    print("\n=== Comparing Different Configurations ===\n")
    
    # Create different rocket configurations
    configs = [
        ("Low Pressure", RocketBuilder()
         .set_initial_conditions(pressure=5 * ATMOSPHERIC_PRESSURE)
         .set_metadata("Low Pressure", "5 bar initial pressure")
         .build()),
        
        ("Medium Pressure", RocketBuilder()
         .set_initial_conditions(pressure=8 * ATMOSPHERIC_PRESSURE)
         .set_metadata("Medium Pressure", "8 bar initial pressure")
         .build()),
        
        ("High Pressure", RocketBuilder()
         .set_initial_conditions(pressure=12 * ATMOSPHERIC_PRESSURE)
         .set_metadata("High Pressure", "12 bar initial pressure")
         .build()),
    ]
    
    simulator = WaterRocketSimulator()
    results = []
    
    for name, config in configs:
        print(f"Simulating {name}...")
        builder = RocketBuilder.from_dict(config.__dict__)
        sim_params = builder.to_simulation_params()
        
        try:
            flight_data = simulator.simulate(sim_params, {'max_time': 15.0})
            results.append((name, flight_data))
            print(f"   Max altitude: {flight_data.max_altitude:.2f} m")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Plot comparison
    if results:
        plt.figure(figsize=(10, 6))
        for name, data in results:
            plt.plot(data.time, data.altitude, linewidth=2, label=name)
        
        plt.xlabel('Time (s)')
        plt.ylabel('Altitude (m)')
        plt.title('Altitude Comparison: Different Initial Pressures')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()


if __name__ == "__main__":
    main()
    
    # Uncomment to run comparison
    # compare_configurations()