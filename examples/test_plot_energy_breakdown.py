#!/usr/bin/env python3
"""
Example demonstrating energy breakdown analysis for water rocket simulation.

This script shows how to:
1. Run a water rocket simulation
2. Perform detailed energy analysis
3. Create energy breakdown plots
4. Understand energy flow through the system
"""

import sys
import os
import numpy as np

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE
from waterrocketpy.analysis.plotter import plot_energy_breakdown, plot_energy_pie_chart


def main():
    """Run energy analysis example."""
    
    print("=== Water Rocket Energy Analysis Example ===\n")
    
    # Create a rocket configuration
    print("1. Creating rocket configuration...")
    rocket_config = (RocketBuilder()
                    .set_bottle(volume=0.002, diameter=0.1)  # 2L bottle
                    .set_nozzle(diameter=0.015)              # 15mm nozzle
                    .set_mass(empty_mass=0.25, water_fraction=0.4)  # 250g empty, 40% water
                    .set_initial_conditions(pressure=10 * ATMOSPHERIC_PRESSURE)  # 10 bar
                    .set_metadata("Energy Analysis Rocket", "Rocket for energy analysis")
                    .build())
    
    print(f"   Rocket: {rocket_config.name}")
    print(f"   Initial pressure: {rocket_config.initial_pressure/ATMOSPHERIC_PRESSURE:.1f} bar")
    print(f"   Water fraction: {rocket_config.water_fraction:.1%}")
    print(f"   Water mass: {rocket_config.water_mass:.3f} kg")
    
    # Convert to simulation parameters
    print("\n2. Converting to simulation parameters...")
    builder = RocketBuilder.from_dict(rocket_config.__dict__)
    rocket_params = builder.to_simulation_params()
    
    # Create simulator and run simulation
    print("\n3. Running simulation...")
    simulator = WaterRocketSimulator()
    
    sim_settings = {
        'max_time': 15.0,
        'time_step': 0.01,
        'solver': 'RK45'
    }
    
    try:
        # Run simulation
        flight_data = simulator.simulate(rocket_params, sim_settings)
        
        print(f"   ✓ Simulation completed successfully!")
        print(f"   Maximum altitude: {flight_data.max_altitude:.2f} m")
        print(f"   Maximum velocity: {flight_data.max_velocity:.2f} m/s")
        print(f"   Flight time: {flight_data.flight_time:.2f} s")
        print(f"   Water depletion time: {flight_data.water_depletion_time:.2f} s")
        
        # Perform energy analysis
        print("\n4. Performing energy breakdown analysis...")
        energy_components = plot_energy_breakdown(flight_data, rocket_params)
        
        # Create pie chart
        print("\n5. Creating energy distribution pie chart...")
        plot_energy_pie_chart(energy_components)
        
        # Print detailed energy analysis
        print_detailed_energy_analysis(energy_components, flight_data)
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()


def print_detailed_energy_analysis(energy_components, flight_data):
    """Print detailed energy analysis results."""
    
    print("\n=== Detailed Energy Analysis ===")
    
    # Initial energy
    E_initial = energy_components.initial_stored_energy
    print(f"\nInitial Energy in Pressurized Air: {E_initial:.2f} J")
    
    # Energy at key moments
    thrust_end_idx = np.where(flight_data.thrust <= 0.1)[0]
    if len(thrust_end_idx) > 0:
        thrust_end_idx = thrust_end_idx[0]
    else:
        thrust_end_idx = len(flight_data.time) - 1
    
    apogee_idx = np.argmax(flight_data.altitude)
    
    print(f"\nEnergy at End of Thrust Phase (t = {flight_data.time[thrust_end_idx]:.2f} s):")
    print(f"  Rocket Kinetic Energy: {energy_components.kinetic_energy_rocket[thrust_end_idx]:.2f} J")
    print(f"  Rocket Potential Energy: {energy_components.potential_energy_rocket[thrust_end_idx]:.2f} J")
    print(f"  Expelled Water Kinetic Energy: {energy_components.kinetic_energy_expelled_water[thrust_end_idx]:.2f} J")
    print(f"  Energy Lost to Drag: {energy_components.energy_lost_to_drag[thrust_end_idx]:.2f} J")
    
    print(f"\nEnergy at Apogee (t = {flight_data.time[apogee_idx]:.2f} s):")
    print(f"  Rocket Kinetic Energy: {energy_components.kinetic_energy_rocket[apogee_idx]:.2f} J")
    print(f"  Rocket Potential Energy: {energy_components.potential_energy_rocket[apogee_idx]:.2f} J")
    print(f"  Energy Lost to Drag: {energy_components.energy_lost_to_drag[apogee_idx]:.2f} J")
    
    # Energy conversion efficiency
    final_useful_energy = (energy_components.kinetic_energy_rocket[-1] + 
                          energy_components.potential_energy_rocket[-1])
    efficiency = final_useful_energy / E_initial * 100
    
    print(f"\nEnergy Conversion Efficiency: {efficiency:.1f}%")
    print(f"  (Percentage of initial energy converted to rocket motion)")
    
    # Energy losses
    drag_loss_percent = energy_components.energy_lost_to_drag[-1] / E_initial * 100
    expelled_water_percent = energy_components.kinetic_energy_expelled_water[-1] / E_initial * 100
    
    print(f"\nEnergy Loss Analysis:")
    print(f"  Lost to aerodynamic drag: {drag_loss_percent:.1f}%")
    print(f"  Carried away by expelled water: {expelled_water_percent:.1f}%")
    
    # Peak power
    power_thrust = flight_data.thrust * flight_data.velocity
    peak_power_idx = np.argmax(power_thrust)
    peak_power = power_thrust[peak_power_idx]
    
    print(f"\nPeak Power Output: {peak_power:.2f} W at t = {flight_data.time[peak_power_idx]:.2f} s")
    
    # Energy balance check
    balance_error_percent = abs(energy_components.energy_balance_error[-1]) / E_initial * 100
    print(f"\nEnergy Balance Error: {balance_error_percent:.3f}%")
    if balance_error_percent < 1.0:
        print("  ✓ Energy conservation is well maintained")
    else:
        print("  ⚠ Significant energy balance error - check calculations")


def compare_different_pressures():
    """Compare energy breakdown for different initial pressures."""
    
    print("\n=== Comparing Energy Breakdown for Different Pressures ===\n")
    
    pressures = [6, 8, 10, 12]  # bar
    results = []
    
    for pressure_bar in pressures:
        print(f"Analyzing {pressure_bar} bar rocket...")
        
        # Create rocket
        rocket_config = (RocketBuilder()
                        .set_bottle(volume=0.002, diameter=0.1)
                        .set_nozzle(diameter=0.015)
                        .set_mass(empty_mass=0.25, water_fraction=0.4)
                        .set_initial_conditions(pressure=pressure_bar * ATMOSPHERIC_PRESSURE)
                        .build())
        
        # Convert to simulation parameters
        builder = RocketBuilder.from_dict(rocket_config.__dict__)
        rocket_params = builder.to_simulation_params()
        
        # Simulate
        simulator = WaterRocketSimulator()
        flight_data = simulator.simulate(rocket_params, {'max_time': 15.0})
        
        # Analyze energy
        from waterrocketpy.analysis.plotter import EnergyAnalyzer
        analyzer = EnergyAnalyzer()
        energy_components = analyzer.analyze_energy_breakdown(flight_data, rocket_params)
        
        results.append({
            'pressure': pressure_bar,
            'max_altitude': flight_data.max_altitude,
            'initial_energy': energy_components.initial_stored_energy,
            'efficiency': ((energy_components.kinetic_energy_rocket[-1] + 
                          energy_components.potential_energy_rocket[-1]) / 
                         energy_components.initial_stored_energy * 100)
        })
        
        print(f"  Max altitude: {flight_data.max_altitude:.1f} m")
        print(f"  Initial energy: {energy_components.initial_stored_energy:.1f} J")
        print(f"  Efficiency: {results[-1]['efficiency']:.1f}%")
    
    # Summary comparison
    print(f"\nPressure Comparison Summary:")
    print(f"{'Pressure (bar)':<15} {'Max Alt (m)':<12} {'Initial E (J)':<15} {'Efficiency (%)':<15}")
    print("-" * 60)
    for result in results:
        print(f"{result['pressure']:<15} {result['max_altitude']:<12.1f} "
              f"{result['initial_energy']:<15.1f} {result['efficiency']:<15.1f}")


if __name__ == "__main__":
    main()
    
    # Uncomment to run pressure comparison
    # compare_different_pressures()