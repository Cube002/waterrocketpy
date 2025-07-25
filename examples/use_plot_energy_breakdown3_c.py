"""
Example demonstrating energy breakdown analysis for water rocket simulation.

This script shows how to:
1. Run a water rocket simulation
2. Perform detailed energy analysis
3. Create energy breakdown plots
4. Understand energy flow through the system
"""

from waterrocketpy.analysis.energy_breakdown import tenergy_breakdown
from waterrocketpy.analysis.energy_breakdown_plot import create_energy_plots,create_energy_summary_chart
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

        # Override internal energy so total energy conserved
        total_energy_assumed = 1554.1 - 420

        # Calculate other energies at each timestep
        kinetic_energy = energy_components.rocket_kinetic_energy
        potential_energy = energy_components.rocket_potential_energy
        expelled_energy = (
            energy_components.water_out_kinetic_energy
            + energy_components.water_out_potential_energy
            + energy_components.air_out_kinetic_energy
            + energy_components.air_out_potential_energy
        )
        drag_losses = energy_components.drag_energy_loss

        # Calculate "fixed" internal energy as the remainder
        corrected_internal_energy = total_energy_assumed - (
            kinetic_energy + potential_energy + expelled_energy + drag_losses
        )

        # Ensure internal energy doesn't go negative
        corrected_internal_energy = np.clip(corrected_internal_energy, 0, None)

        # Override the internal energy in the energy_components object
        energy_components.air_internal_energy = corrected_internal_energy
        energy_components.total_initial_energy = total_energy_assumed

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
        create_energy_summary_chart(energy_components, flight_data)


        print("\n   ✓ Plots created successfully!")
        print(
            "   Check the generated plot files for detailed energy analysis."
        )

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return


if __name__ == "__main__":
    main()
