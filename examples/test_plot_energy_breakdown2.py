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
import matplotlib.pyplot as plt

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE
from waterrocketpy.analysis.plotter import plot_energy_breakdown, plot_energy_pie_chart
from waterrocketpy.analysis.energy_breakdown import tenergy_breakdown


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
        energy_components = tenergy_breakdown(flight_data, rocket_params)
        
        # Display energy analysis results
        print_energy_summary(energy_components)
        
        # Create energy breakdown plots
        print("\n5. Creating energy breakdown plots...")
        create_energy_plots(energy_components, flight_data)
        
        print("\n   ✓ Energy analysis completed successfully!")
        print("   Check the generated plots for detailed energy flow visualization.")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()


def print_energy_summary(energy_components):
    """Print summary of energy analysis results."""
    
    print(f"   Initial total energy: {energy_components.total_initial_energy:.2f} J")
    print(f"   Maximum kinetic energy: {energy_components.max_kinetic_energy:.2f} J")
    print(f"   Maximum potential energy: {energy_components.max_potential_energy:.2f} J")
    print(f"   Total drag loss: {energy_components.total_drag_loss:.2f} J")
    print(f"   Total expelled energy: {energy_components.total_expelled_energy:.2f} J")
    
    # Energy conservation check
    final_error = energy_components.energy_conservation_error[-1]
    print(f"   Energy conservation error: {final_error:.2f}%")
    
    if final_error < 5.0:
        print("   ✓ Energy conservation is good!")
    elif final_error < 10.0:
        print("   ⚠ Energy conservation is acceptable")
    else:
        print("   ✗ Energy conservation error is high - check simulation")
    
    # Energy distribution at peak altitude
    peak_idx = np.argmax(energy_components.rocket_potential_energy)
    peak_time = energy_components.time[peak_idx]
    
    print(f"\n   Energy distribution at peak altitude (t={peak_time:.2f}s):")
    print(f"   - Internal energy: {energy_components.air_internal_energy[peak_idx]:.2f} J")
    print(f"   - Kinetic energy: {energy_components.rocket_kinetic_energy[peak_idx]:.2f} J")
    print(f"   - Potential energy: {energy_components.rocket_potential_energy[peak_idx]:.2f} J")
    print(f"   - Expelled energy: {energy_components.water_out_kinetic_energy[peak_idx] + energy_components.water_out_potential_energy[peak_idx] + energy_components.air_out_kinetic_energy[peak_idx] + energy_components.air_out_potential_energy[peak_idx]:.2f} J")
    print(f"   - Drag losses: {energy_components.drag_energy_loss[peak_idx]:.2f} J")


def create_energy_plots(energy_components, flight_data):
    """Create comprehensive energy breakdown plots."""
    
    # Set up the plotting style
    plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Energy components over time
    ax1 = plt.subplot(2, 3, 1)
    plot_energy_components_time(ax1, energy_components)
    
    # 2. Energy flow (cumulative)
    ax2 = plt.subplot(2, 3, 2)
    plot_energy_flow(ax2, energy_components)
    
    # 3. Energy conservation check
    ax3 = plt.subplot(2, 3, 3)
    plot_energy_conservation(ax3, energy_components)
    
    # 4. Energy pie chart at different times
    ax4 = plt.subplot(2, 3, 4)
    plot_energy_pie_at_time(ax4, energy_components, "Launch", 0)
    
    # 5. Energy pie chart at peak altitude
    ax5 = plt.subplot(2, 3, 5)
    peak_idx = np.argmax(energy_components.rocket_potential_energy)
    plot_energy_pie_at_time(ax5, energy_components, "Peak Altitude", peak_idx)
    
    # 6. Energy efficiency metrics
    ax6 = plt.subplot(2, 3, 6)
    plot_energy_efficiency(ax6, energy_components, flight_data)
    
    plt.tight_layout()
    plt.savefig('energy_breakdown_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_energy_components_time(ax, energy_components):
    """Plot energy components over time."""
    
    time = energy_components.time
    
    ax.plot(time, energy_components.air_internal_energy, 'r-', label='Internal Energy', linewidth=2)
    ax.plot(time, energy_components.rocket_kinetic_energy, 'b-', label='Kinetic Energy', linewidth=2)
    ax.plot(time, energy_components.rocket_potential_energy, 'g-', label='Potential Energy', linewidth=2)
    ax.plot(time, energy_components.drag_energy_loss, 'k--', label='Drag Loss', linewidth=2)
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Energy (J)')
    ax.set_title('Energy Components vs Time')
    ax.legend()
    ax.grid(True, alpha=0.3)


def plot_energy_flow(ax, energy_components):
    """Plot cumulative energy flow."""
    
    time = energy_components.time
    
    # Cumulative expelled energy
    total_expelled = (energy_components.water_out_kinetic_energy + 
                     energy_components.water_out_potential_energy +
                     energy_components.air_out_kinetic_energy + 
                     energy_components.air_out_potential_energy)
    
    ax.plot(time, total_expelled, 'orange', label='Total Expelled', linewidth=2)
    ax.plot(time, energy_components.water_out_kinetic_energy + energy_components.water_out_potential_energy, 
            'cyan', label='Water Expelled', linewidth=2)
    ax.plot(time, energy_components.air_out_kinetic_energy + energy_components.air_out_potential_energy, 
            'purple', label='Air Expelled', linewidth=2)
    ax.plot(time, energy_components.drag_energy_loss, 'red', label='Drag Loss', linewidth=2)
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Cumulative Energy (J)')
    ax.set_title('Cumulative Energy Flow')
    ax.legend()
    ax.grid(True, alpha=0.3)


def plot_energy_conservation(ax, energy_components):
    """Plot energy conservation error."""
    
    time = energy_components.time
    error = energy_components.energy_conservation_error
    
    ax.plot(time, error, 'r-', linewidth=2)
    ax.axhline(y=5.0, color='orange', linestyle='--', label='5% threshold')
    ax.axhline(y=10.0, color='red', linestyle='--', label='10% threshold')
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Energy Conservation Error (%)')
    ax.set_title('Energy Conservation Check')
    ax.legend()
    ax.grid(True, alpha=0.3)


def plot_energy_pie_at_time(ax, energy_components, title, time_idx):
    """Plot energy distribution pie chart at specific time."""
    
    if time_idx >= len(energy_components.time):
        time_idx = -1
    
    # Calculate energy components at this time
    internal = energy_components.air_internal_energy[time_idx]
    kinetic = energy_components.rocket_kinetic_energy[time_idx]
    potential = energy_components.rocket_potential_energy[time_idx]
    expelled = (energy_components.water_out_kinetic_energy[time_idx] + 
               energy_components.water_out_potential_energy[time_idx] +
               energy_components.air_out_kinetic_energy[time_idx] + 
               energy_components.air_out_potential_energy[time_idx])
    drag_loss = energy_components.drag_energy_loss[time_idx]
    
    # Filter out very small values for cleaner pie chart
    energies = [internal, kinetic, potential, expelled, drag_loss]
    labels = ['Internal', 'Kinetic', 'Potential', 'Expelled', 'Drag Loss']
    
    # Only include components with >1% of total
    total_energy = sum(energies)
    if total_energy > 0:
        filtered_energies = []
        filtered_labels = []
        for e, l in zip(energies, labels):
            if e / total_energy > 0.01:  # >1%
                filtered_energies.append(e)
                filtered_labels.append(l)
        
        if filtered_energies:
            colors = ['red', 'blue', 'green', 'orange', 'gray'][:len(filtered_energies)]
            ax.pie(filtered_energies, labels=filtered_labels, colors=colors, autopct='%1.1f%%')
    
    ax.set_title(f'{title}\n(t={energy_components.time[time_idx]:.2f}s)')


def plot_energy_efficiency(ax, energy_components, flight_data):
    """Plot energy efficiency metrics."""
    
    # Calculate efficiency metrics
    time = energy_components.time
    
    # Kinetic efficiency: kinetic energy / initial energy
    kinetic_efficiency = energy_components.rocket_kinetic_energy / energy_components.total_initial_energy * 100
    
    # Potential efficiency: potential energy / initial energy  
    potential_efficiency = energy_components.rocket_potential_energy / energy_components.total_initial_energy * 100
    
    # Total useful efficiency: (kinetic + potential) / initial
    total_efficiency = kinetic_efficiency + potential_efficiency
    
    ax.plot(time, kinetic_efficiency, 'b-', label='Kinetic Efficiency', linewidth=2)
    ax.plot(time, potential_efficiency, 'g-', label='Potential Efficiency', linewidth=2)
    ax.plot(time, total_efficiency, 'purple', label='Total Efficiency', linewidth=2)
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Efficiency (%)')
    ax.set_title('Energy Conversion Efficiency')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add peak efficiency annotation
    peak_total_idx = np.argmax(total_efficiency)
    peak_eff = total_efficiency[peak_total_idx]
    peak_time = time[peak_total_idx]
    ax.annotate(f'Peak: {peak_eff:.1f}%', 
                xy=(peak_time, peak_eff), 
                xytext=(peak_time + 1, peak_eff + 5),
                arrowprops=dict(arrowstyle='->', color='purple'))


if __name__ == "__main__":
    main()