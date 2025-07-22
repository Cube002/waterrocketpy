"""
Example demonstrating energy breakdown analysis for water rocket simulation.

This script shows how to:
1. Run a water rocket simulation
2. Perform detailed energy analysis
3. Create energy breakdown plots
4. Understand energy flow through the system
"""

from waterrocketpy.analysis.energy_breakdown import tenergy_breakdown
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE
from waterrocketpy.rocket.builder import RocketBuilder
from waterrocketpy.core.simulation import WaterRocketSimulator
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Add the package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    """Run energy analysis example."""

    print("=== Water Rocket Energy Analysis Example ===\n")

    # Create a rocket configuration
    print("1. Creating rocket configuration...")
    rocket_config = (
        RocketBuilder()
        .set_bottle(volume=0.002, diameter=0.1)  # 2L bottle
        .set_nozzle(diameter=0.015)  # 15mm nozzle
        .set_mass(empty_mass=0.25, water_fraction=0.4)  # 250g empty, 40% water
        .set_initial_conditions(pressure=10 * ATMOSPHERIC_PRESSURE)  # 10 bar
        .set_metadata("Energy Analysis Rocket", "Rocket for energy analysis")
        .build()
    )

    print(f"   Rocket: {rocket_config.name}")
    print(
        f"   Initial pressure: {rocket_config.initial_pressure/ATMOSPHERIC_PRESSURE:.1f} bar"
    )
    print(f"   Water fraction: {rocket_config.water_fraction:.1%}")
    print(f"   Water mass: {rocket_config.water_mass:.3f} kg")

    # Convert to simulation parameters
    print("\n2. Converting to simulation parameters...")
    builder = RocketBuilder.from_dict(rocket_config.__dict__)
    rocket_params = builder.to_simulation_params()

    # Create simulator and run simulation
    print("\n3. Running simulation...")
    simulator = WaterRocketSimulator()

    sim_settings = {"max_time": 15.0, "time_step": 0.01, "solver": "RK45"}

    try:
        # Run simulation
        flight_data = simulator.simulate(rocket_params, sim_settings)

        print(f"   ✓ Simulation completed successfully!")
        print(f"   Maximum altitude: {flight_data.max_altitude:.2f} m")
        print(f"   Maximum velocity: {flight_data.max_velocity:.2f} m/s")
        print(f"   Flight time: {flight_data.flight_time:.2f} s")
        print(
            f"   Water depletion time: {flight_data.water_depletion_time:.2f} s"
        )

        # Perform energy analysis
        print("\n4. Performing energy breakdown analysis...")
        energy_components = tenergy_breakdown(flight_data, rocket_params)

        print(f"   ✓ Energy analysis completed!")
        print(
            f"   Initial total energy: {energy_components.total_initial_energy:.2f} J"
        )
        print(
            f"   Maximum kinetic energy: {energy_components.max_kinetic_energy:.2f} J"
        )
        print(
            f"   Maximum potential energy: {energy_components.max_potential_energy:.2f} J"
        )
        print(f"   Total drag loss: {energy_components.total_drag_loss:.2f} J")
        print(
            f"   Total expelled energy: {energy_components.total_expelled_energy:.2f} J"
        )  # somehow not printing
        print(
            f"   Final energy conservation error: {energy_components.energy_conservation_error[-1]:.2f}%"
        )  # somehow not printing

        # Create comprehensive energy plots
        print("\n5. Creating energy breakdown plots...")
        create_energy_plots(energy_components, flight_data)

        print("\n   ✓ Plots created successfully!")
        print(
            "   Check the generated plot files for detailed energy analysis."
        )

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return


def create_energy_plots(energy_components, flight_data):
    """Create comprehensive energy breakdown plots."""

    # Set up the plotting style
    plt.style.use("seaborn-v0_8")
    colors = {
        "internal": "#FF6B6B",
        "kinetic": "#4ECDC4",
        "potential": "#45B7D1",
        "expelled": "#96CEB4",
        "losses": "#FFEAA7",
        "total": "#2D3436",
    }

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # Main energy breakdown plot (large, spanning top row)
    ax1 = fig.add_subplot(gs[0, :])

    # Calculate combined energy components for stacked plot
    time = energy_components.time

    # Energy stored in the system
    internal_energy = energy_components.air_internal_energy
    kinetic_energy = energy_components.rocket_kinetic_energy
    potential_energy = energy_components.rocket_potential_energy

    # Energy that left the system
    expelled_kinetic = (
        energy_components.water_out_kinetic_energy
        + energy_components.air_out_kinetic_energy
    )
    expelled_potential = (
        energy_components.water_out_potential_energy
        + energy_components.air_out_potential_energy
    )
    expelled_total = expelled_kinetic + expelled_potential

    # Energy losses
    drag_losses = energy_components.drag_energy_loss

    # Create stacked area plot
    ax1.fill_between(
        time,
        0,
        internal_energy,
        color=colors["internal"],
        alpha=0.8,
        label="Internal Energy (Air)",
    )
    ax1.fill_between(
        time,
        internal_energy,
        internal_energy + kinetic_energy,
        color=colors["kinetic"],
        alpha=0.8,
        label="Kinetic Energy (Rocket)",
    )
    ax1.fill_between(
        time,
        internal_energy + kinetic_energy,
        internal_energy + kinetic_energy + potential_energy,
        color=colors["potential"],
        alpha=0.8,
        label="Potential Energy (Rocket)",
    )
    ax1.fill_between(
        time,
        internal_energy + kinetic_energy + potential_energy,
        internal_energy + kinetic_energy + potential_energy + expelled_total,
        color=colors["expelled"],
        alpha=0.8,
        label="Expelled Energy (Water + Air)",
    )
    ax1.fill_between(
        time,
        internal_energy + kinetic_energy + potential_energy + expelled_total,
        internal_energy
        + kinetic_energy
        + potential_energy
        + expelled_total
        + drag_losses,
        color=colors["losses"],
        alpha=0.8,
        label="Energy Losses (Drag)",
    )

    # Add total energy line
    total_energy = (
        internal_energy
        + kinetic_energy
        + potential_energy
        + expelled_total
        + drag_losses
    )
    ax1.plot(
        time,
        total_energy,
        color=colors["total"],
        linewidth=2,
        label=f"Total Energy (Initial: {energy_components.total_initial_energy:.0f} J)",
    )

    # Add vertical lines for phase transitions
    if flight_data.water_depletion_time > 0:
        ax1.axvline(
            flight_data.water_depletion_time,
            color="red",
            linestyle="--",
            alpha=0.7,
            label="Water Depletion",
        )
    if flight_data.air_depletion_time > 0:
        ax1.axvline(
            flight_data.air_depletion_time,
            color="orange",
            linestyle="--",
            alpha=0.7,
            label="Air Depletion",
        )

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Energy (J)")
    ax1.set_title(
        "Complete Energy Breakdown Over Time", fontsize=14, fontweight="bold"
    )
    ax1.legend(loc="upper right", bbox_to_anchor=(1.02, 1))
    ax1.grid(True, alpha=0.3)

    # Detailed kinetic energy breakdown
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(
        time,
        energy_components.rocket_kinetic_energy,
        color=colors["kinetic"],
        linewidth=2,
        label="Rocket Kinetic",
    )
    ax2.plot(
        time,
        energy_components.water_out_kinetic_energy,
        color="#74b9ff",
        linewidth=2,
        label="Expelled Water Kinetic",
    )
    ax2.plot(
        time,
        energy_components.air_out_kinetic_energy,
        color="#a29bfe",
        linewidth=2,
        label="Expelled Air Kinetic",
    )
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Kinetic Energy (J)")
    ax2.set_title("Kinetic Energy Components")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Detailed potential energy breakdown
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(
        time,
        energy_components.rocket_potential_energy,
        color=colors["potential"],
        linewidth=2,
        label="Rocket Potential",
    )
    ax3.plot(
        time,
        energy_components.water_out_potential_energy,
        color="#00b894",
        linewidth=2,
        label="Expelled Water Potential",
    )
    ax3.plot(
        time,
        energy_components.air_out_potential_energy,
        color="#00cec9",
        linewidth=2,
        label="Expelled Air Potential",
    )
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Potential Energy (J)")
    ax3.set_title("Potential Energy Components")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Energy conservation check
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(
        time,
        energy_components.energy_conservation_error,
        color="red",
        linewidth=2,
    )
    ax4.set_xlabel("Time (s)")
    ax4.set_ylabel("Conservation Error (%)")
    ax4.set_title("Energy Conservation Error")
    ax4.grid(True, alpha=0.3)

    # Energy flow rates
    ax5 = fig.add_subplot(gs[2, 1])

    # Calculate energy flow rates (derivatives)
    dt = np.diff(time)
    expelled_rate = np.diff(expelled_total) / dt
    drag_rate = np.diff(drag_losses) / dt

    # Pad with zeros to match time array length
    expelled_rate = np.append(expelled_rate, 0)
    drag_rate = np.append(drag_rate, 0)

    ax5.plot(
        time,
        expelled_rate,
        color=colors["expelled"],
        linewidth=2,
        label="Expelled Energy Rate",
    )
    ax5.plot(
        time,
        drag_rate,
        color=colors["losses"],
        linewidth=2,
        label="Drag Loss Rate",
    )
    ax5.set_xlabel("Time (s)")
    ax5.set_ylabel("Energy Rate (J/s)")
    ax5.set_title("Energy Flow Rates")
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("energy_breakdown_analysis.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Create a summary pie chart of final energy distribution
    create_energy_summary_chart(energy_components)


def create_energy_summary_chart(energy_components):
    """Create a pie chart showing final energy distribution."""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Final energy distribution
    final_kinetic = energy_components.rocket_kinetic_energy[-1]
    final_potential = energy_components.rocket_potential_energy[-1]
    final_internal = energy_components.air_internal_energy[-1]
    final_expelled = (
        energy_components.water_out_kinetic_energy[-1]
        + energy_components.water_out_potential_energy[-1]
        + energy_components.air_out_kinetic_energy[-1]
        + energy_components.air_out_potential_energy[-1]
    )
    final_losses = energy_components.drag_energy_loss[-1]

    # Filter out very small values
    threshold = 0.01 * energy_components.total_initial_energy

    energies = []
    labels = []
    colors = []

    if final_kinetic > threshold:
        energies.append(final_kinetic)
        labels.append(f"Kinetic\n{final_kinetic:.1f} J")
        colors.append("#4ECDC4")

    if final_potential > threshold:
        energies.append(final_potential)
        labels.append(f"Potential\n{final_potential:.1f} J")
        colors.append("#45B7D1")

    if final_internal > threshold:
        energies.append(final_internal)
        labels.append(f"Internal\n{final_internal:.1f} J")
        colors.append("#FF6B6B")

    if final_expelled > threshold:
        energies.append(final_expelled)
        labels.append(f"Expelled\n{final_expelled:.1f} J")
        colors.append("#96CEB4")

    if final_losses > threshold:
        energies.append(final_losses)
        labels.append(f"Drag Losses\n{final_losses:.1f} J")
        colors.append("#FFEAA7")

    # Create pie chart
    wedges, texts, autotexts = ax1.pie(
        energies,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
    )
    ax1.set_title(
        f"Final Energy Distribution\n(Total Initial: {energy_components.total_initial_energy:.0f} J)"
    )

    # Energy efficiency analysis
    efficiency_data = {
        "Useful Energy\n(Kinetic + Potential)": final_kinetic
        + final_potential,
        "Expelled Energy\n(Carried Away)": final_expelled,
        "Energy Losses\n(Drag)": final_losses,
        "Remaining Internal\n(Unused)": final_internal,
    }

    ax2.bar(
        range(len(efficiency_data)),
        list(efficiency_data.values()),
        color=["#00b894", "#74b9ff", "#fd79a8", "#fdcb6e"],
    )
    ax2.set_xticks(range(len(efficiency_data)))
    ax2.set_xticklabels(efficiency_data.keys(), rotation=45, ha="right")
    ax2.set_ylabel("Energy (J)")
    ax2.set_title("Energy Efficiency Analysis")
    ax2.grid(True, alpha=0.3)

    # Add efficiency percentages
    total_energy = energy_components.total_initial_energy
    for i, (key, value) in enumerate(efficiency_data.items()):
        percentage = (value / total_energy) * 100
        ax2.text(
            i,
            value + 0.5,
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig("energy_summary.png", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
