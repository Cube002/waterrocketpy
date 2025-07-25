"""
# Energy Breakdown Analysis Module
This module provides functions to plot the energy breakdown of water rocket flights.
The calculations are done in energy_breakdown.py, and the plotting is handled in energy_breakdown_plot.py.


1. Create energy breakdown plots
2. Understand energy flow through the system
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches


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


def create_energy_summary_chart(energy_components, flight_data):
    """Create pie charts showing energy distribution at key time points."""

    # Time series data
    time = energy_components.time

    # Find indices of interest
    max_altitude_index = np.argmax(flight_data.altitude)
    max_velocity_index = np.argmax(flight_data.velocity)
    final_index = -1  # Last value

    # Helper function to extract energy components at a given index
    def get_energy_distribution_at(index):
        ke = energy_components.rocket_kinetic_energy[index]
        pe = energy_components.rocket_potential_energy[index]
        ie = energy_components.air_internal_energy[index]
        expelled = (
            energy_components.water_out_kinetic_energy[index]
            + energy_components.water_out_potential_energy[index]
            + energy_components.air_out_kinetic_energy[index]
            + energy_components.air_out_potential_energy[index]
        )
        losses = energy_components.drag_energy_loss[index]
        return ke, pe, ie, expelled, losses

    # Collect energy values at each key time
    snapshots = {
        "At Max Altitude": get_energy_distribution_at(max_altitude_index),
        "At Max Velocity": get_energy_distribution_at(max_velocity_index),
        "Final State": get_energy_distribution_at(final_index),
    }

    # Set up pie chart layout
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    for ax, (title, (ke, pe, ie, expelled, losses)) in zip(
        axes, snapshots.items()
    ):
        energies = []
        labels = []
        colors = []

        if ke > 1.0:
            energies.append(ke)
            labels.append(f"Kinetic\n{ke:.1f} J")
            colors.append("#4ECDC4")
        if pe > 1.0:
            energies.append(pe)
            labels.append(f"Potential\n{pe:.1f} J")
            colors.append("#45B7D1")
        if ie > 1.0:
            energies.append(ie)
            labels.append(f"Internal\n{ie:.1f} J")
            colors.append("#FF6B6B")
        if expelled > 1.0:
            energies.append(expelled)
            labels.append(f"Expelled\n{expelled:.1f} J")
            colors.append("#96CEB4")
        if losses > 1.0:
            energies.append(losses)
            labels.append(f"Drag Losses\n{losses:.1f} J")
            colors.append("#FFEAA7")

        ax.pie(
            energies,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title(title)

    plt.suptitle(
        f"Energy Distribution at Key Points (Total: {energy_components.total_initial_energy:.0f} J)",
        fontsize=16,
        fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("energy_snapshots.png", dpi=300, bbox_inches="tight")
    plt.show()
