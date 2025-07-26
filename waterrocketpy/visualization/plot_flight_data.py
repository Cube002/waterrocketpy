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
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure you're running this from the correct directory.")
    sys.exit(1)


def setup_plot_style():
    """Configure matplotlib for professional-looking plots."""
    plt.style.use('seaborn-v0_8')
    plt.rcParams.update({
        'figure.figsize': (16, 12),
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'lines.linewidth': 1.5,
        'grid.alpha': 0.3
    })


def identify_flight_phases(flight_data):
    """
    Identify the different phases of flight for visualization.
    
    Returns:
        dict: Phase boundaries and information
    """
    phases = {
        'water_end': flight_data.water_depletion_time,
        'air_end': flight_data.air_depletion_time,
        'flight_end': flight_data.flight_time
    }
    
    # Find apogee (maximum altitude)
    apogee_idx = np.argmax(flight_data.altitude)
    phases['apogee_time'] = flight_data.time[apogee_idx]
    phases['apogee_altitude'] = flight_data.max_altitude
    
    return phases


def add_phase_backgrounds(ax, phases, alpha=0.1):
    """Add colored backgrounds to distinguish flight phases."""
    colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral']
    labels = ['Water Phase', 'Air Phase', 'Coasting Up', 'Descent']
    
    # Get axis limits
    ylim = ax.get_ylim()
    height = ylim[1] - ylim[0]
    
    times = [0, phases['water_end'], phases['air_end'], 
             phases['apogee_time'], phases['flight_end']]
    
    for i in range(len(times)-1):
        if times[i+1] > times[i]:  # Only add if phase exists
            width = times[i+1] - times[i]
            if width > 0:
                rect = patches.Rectangle(
                    (times[i], ylim[0]), width, height,
                    linewidth=0, edgecolor='none',
                    facecolor=colors[min(i, len(colors)-1)],
                    alpha=alpha, zorder=0
                )
                ax.add_patch(rect)


def plot_trajectory_and_velocity(flight_data, phases):
    """Plot altitude and velocity vs time."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Altitude plot
    ax1.plot(flight_data.time, flight_data.altitude, 'b-', linewidth=2, label='Altitude')
    add_phase_backgrounds(ax1, phases)
    
    # Mark key events
    ax1.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7, label='Water depleted')
    ax1.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7, label='Air depleted')
    ax1.axvline(phases['apogee_time'], color='green', linestyle='--', alpha=0.7, label='Apogee')
    
    ax1.set_ylabel('Altitude (m)')
    ax1.set_title('Rocket Trajectory')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Velocity plot
    ax2.plot(flight_data.time, flight_data.velocity, 'r-', linewidth=2, label='Velocity')
    add_phase_backgrounds(ax2, phases)
    
    # Mark key events
    ax2.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax2.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    ax2.axvline(phases['apogee_time'], color='green', linestyle='--', alpha=0.7)
    ax2.axhline(0, color='black', linestyle='-', alpha=0.3)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Velocity (m/s)')
    ax2.set_title('Rocket Velocity')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    return fig


def plot_forces_and_acceleration(flight_data, phases):
    """Plot forces and acceleration."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Forces plot
    ax1.plot(flight_data.time, flight_data.thrust, 'g-', linewidth=2, label='Thrust')
    ax1.plot(flight_data.time, flight_data.drag, 'r-', linewidth=2, label='Drag')
    
    # Calculate weight (assuming constant during powered flight)
    # Weight changes as propellant is expelled
    total_mass = flight_data.water_mass + flight_data.air_mass + 0.15  # Assuming 0.15kg empty mass
    weight = total_mass * 9.81
    ax1.plot(flight_data.time, weight, 'k--', linewidth=1.5, label='Weight', alpha=0.7)
    
    add_phase_backgrounds(ax1, phases)
    ax1.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax1.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    
    ax1.set_ylabel('Force (N)')
    ax1.set_title('Forces Acting on Rocket')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_yscale('log')
    
    # Acceleration plot
    ax2.plot(flight_data.time, flight_data.acceleration, 'purple', linewidth=2, label='Acceleration')
    add_phase_backgrounds(ax2, phases)
    
    ax2.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax2.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    ax2.axhline(0, color='black', linestyle='-', alpha=0.3)
    ax2.axhline(-9.81, color='gray', linestyle=':', alpha=0.7, label='Gravity')
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Acceleration (m/s²)')
    ax2.set_title('Rocket Acceleration')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    return fig


def plot_propellant_and_pressure(flight_data, phases):
    """Plot propellant masses and pressure."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Propellant masses
    ax1.plot(flight_data.time, flight_data.water_mass * 1000, 'b-', linewidth=2, label='Water mass')
    ax1.plot(flight_data.time, flight_data.air_mass * 1000, 'g-', linewidth=2, label='Air mass')
    ax1.plot(flight_data.time, flight_data.liquid_gas_mass * 1000, 'orange', linewidth=2, label='Liquid gas mass')
    
    add_phase_backgrounds(ax1, phases)
    ax1.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax1.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    
    ax1.set_ylabel('Mass (g)')
    ax1.set_title('Propellant Masses')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Pressure and temperature
    ax2_temp = ax2.twinx()
    
    # Pressure (convert to bar for readability)
    pressure_bar = flight_data.pressure / 1e5
    line1 = ax2.plot(flight_data.time, pressure_bar, 'r-', linewidth=2, label='Pressure')
    ax2.axhline(ATMOSPHERIC_PRESSURE / 1e5, color='red', linestyle=':', alpha=0.7, label='Atmospheric')
    
    # Temperature
    line2 = ax2_temp.plot(flight_data.time, flight_data.air_temperature, 'orange', linewidth=2, label='Temperature')
    ax2_temp.axhline(INITIAL_TEMPERATURE, color='orange', linestyle=':', alpha=0.7, label='Initial temp')
    
    add_phase_backgrounds(ax2, phases)
    ax2.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax2.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Pressure (bar)', color='r')
    ax2_temp.set_ylabel('Temperature (K)', color='orange')
    ax2.set_title('Pressure and Temperature')
    ax2.grid(True, alpha=0.3)
    
    # Combine legends
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_temp.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    return fig


def plot_exhaust_properties(flight_data, phases):
    """Plot exhaust velocities and mass flow rates."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Exhaust velocities
    # Handle None values by replacing with 0
    water_exhaust = np.nan_to_num(flight_data.water_exhaust_speed, 0)
    air_exhaust = np.nan_to_num(flight_data.air_exhaust_speed, 0)
    
    ax1.plot(flight_data.time, water_exhaust, 'b-', linewidth=2, label='Water exhaust speed')
    ax1.plot(flight_data.time, air_exhaust, 'g-', linewidth=2, label='Air exhaust speed')
    
    add_phase_backgrounds(ax1, phases)
    ax1.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax1.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    
    ax1.set_ylabel('Exhaust Speed (m/s)')
    ax1.set_title('Exhaust Velocities')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Mass flow rates
    water_flow = np.nan_to_num(flight_data.water_mass_flow_rate, 0) * 1000  # Convert to g/s
    air_flow = np.nan_to_num(flight_data.air_mass_flow_rate, 0) * 1000
    
    ax2.plot(flight_data.time, -water_flow, 'b-', linewidth=2, label='Water flow rate')  # Negative because it's outflow
    ax2.plot(flight_data.time, -air_flow, 'g-', linewidth=2, label='Air flow rate')
    
    add_phase_backgrounds(ax2, phases)
    ax2.axvline(phases['water_end'], color='red', linestyle='--', alpha=0.7)
    ax2.axvline(phases['air_end'], color='orange', linestyle='--', alpha=0.7)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Mass Flow Rate (g/s)')
    ax2.set_title('Propellant Mass Flow Rates')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    return fig

def plot_air_exit_conditions(flight_data, phases):
    """Plot air and water exit conditions and internal bottle air properties."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9))

    # Time masks
    air_phase_mask = (flight_data.time >= phases['water_end']) & (flight_data.time <= phases['air_end'])
    water_phase_mask = (flight_data.time >= 0) & (flight_data.time <= phases['water_end'])
    combine_mask = air_phase_mask | water_phase_mask

    if not np.any(air_phase_mask):
        ax1.text(0.5, 0.5, 'No air phase detected', ha='center', va='center', transform=ax1.transAxes)
        ax2.text(0.5, 0.5, 'No air phase detected', ha='center', va='center', transform=ax2.transAxes)
        ax3.text(0.5, 0.5, 'No air phase detected', ha='center', va='center', transform=ax3.transAxes)
    else:
        thrust_time = flight_data.time[combine_mask]

        # === 1. PRESSURE ===
        air_exit_pressure = np.nan_to_num(flight_data.air_exit_pressure[combine_mask], ATMOSPHERIC_PRESSURE) / 1e5
        internal_pressure = flight_data.pressure[combine_mask] / 1e5

        ax1.plot(thrust_time, air_exit_pressure, color='purple', linewidth=2, label='Air exit pressure')
        ax1.plot(thrust_time, internal_pressure, color='blue', linestyle='--', linewidth=2, label='Internal pressure')
        ax1.axhline(ATMOSPHERIC_PRESSURE / 1e5, color='gray', linestyle=':', alpha=0.7, label='Atmospheric pressure')
        ax1.set_ylabel('Pressure (bar)')
        ax1.set_title('Air Exit and Internal Conditions')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # === 2. TEMPERATURE ===
        air_exit_temp = np.nan_to_num(flight_data.air_exit_temperature[combine_mask], INITIAL_TEMPERATURE)
        internal_temp = flight_data.air_temperature[combine_mask]

        ax2.plot(thrust_time, air_exit_temp, color='orange', linewidth=2, label='Air exit temperature')
        ax2.plot(thrust_time, internal_temp, color='red', linestyle='--', linewidth=2, label='Internal temperature')
        ax2.axhline(INITIAL_TEMPERATURE, color='gray', linestyle=':', alpha=0.7, label='Initial temperature')
        ax2.set_ylabel('Temperature (K)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # === 3. EXHAUST VELOCITY ===
        water_velocity = np.nan_to_num(flight_data.water_exhaust_speed[combine_mask], 0.0)
        air_velocity = np.nan_to_num(flight_data.air_exhaust_speed[combine_mask], 0.0)

        ax3.plot(thrust_time, water_velocity, color='blue', linewidth=2, label='Water exhaust velocity')
        ax3.plot(thrust_time, air_velocity, color='green', linewidth=2, label='Air exhaust velocity')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Exhaust Velocity (m/s)')
        ax3.grid(True, alpha=0.3)
        ax3.legend()

    plt.tight_layout()
    return fig


def create_summary_table(flight_data, phases):
    """Create a summary table of key flight parameters."""
    summary_data = {
        'Flight Performance': {
            'Maximum Altitude': f"{flight_data.max_altitude:.2f} m",
            'Maximum Velocity': f"{flight_data.max_velocity:.2f} m/s",
            'Total Flight Time': f"{flight_data.flight_time:.2f} s",
            'Time to Apogee': f"{phases['apogee_time']:.2f} s"
        },
        'Phase Durations': {
            'Water Phase': f"{phases['water_end']:.2f} s",
            'Air Phase': f"{phases['air_end'] - phases['water_end']:.2f} s" if phases['air_end'] > phases['water_end'] else "0.00 s",
            'Coasting Phase': f"{phases['flight_end'] - phases['air_end']:.2f} s" if phases['flight_end'] > phases['air_end'] else f"{phases['flight_end'] - phases['water_end']:.2f} s"
        },
        'Initial Conditions': {
            'Initial Water Mass': f"{flight_data.water_mass[0]*1000:.1f} g",
            'Initial Air Mass': f"{flight_data.air_mass[0]*1000:.1f} g",
            'Initial Pressure': f"{flight_data.pressure[0]/1e5:.2f} bar",
            'Initial Temperature': f"{flight_data.air_temperature[0]:.1f} K"
        }
    }
    
    return summary_data


def print_flight_summary(flight_data, phases):
    """Print a comprehensive flight summary."""
    print("\n" + "="*60)
    print("WATER ROCKET FLIGHT ANALYSIS SUMMARY")
    print("="*60)
    
    summary = create_summary_table(flight_data, phases)
    
    for category, values in summary.items():
        print(f"\n{category}:")
        print("-" * len(category))
        for key, value in values.items():
            print(f"  {key:<25}: {value}")
    
    print("\n" + "="*60)


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