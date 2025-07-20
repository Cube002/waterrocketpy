#!/usr/bin/env python3

import sys
import os
from pathlib import Path
from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder
from waterrocketpy.core.constants import ATMOSPHERIC_PRESSURE
from waterrocketpy.utils.saver import save_flight_data

# For local development: add package root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    # Build a custom rocket configuration
    rocket = (RocketBuilder()
              .set_bottle(volume=0.002, diameter=0.1)
              .set_nozzle(diameter=0.015)
              .set_mass(empty_mass=0.25, water_fraction=0.33)
              .set_initial_conditions(pressure=8 * ATMOSPHERIC_PRESSURE)
              .set_metadata("Test Rocket", "Simulation test rocket")
              .build())

    # Get simulation parameters
    sim_params = RocketBuilder.from_dict(rocket.__dict__).to_simulation_params()

    # Run simulation
    simulator = WaterRocketSimulator()
    flight_data = simulator.simulate(sim_params, {
        'max_time': 0.5,
        'time_step': 0.01,
        'solver': 'RK45'
    })

    # Attach config for metadata saving
    flight_data.config = rocket

    # Save to outputs/
    output_path = Path(__file__).parent / "outputs" / "test_sim_result"
    output_path.parent.mkdir(exist_ok=True)
    save_flight_data(flight_data, output_path)

    print("Simulation completed and data saved.")

if __name__ == "__main__":
    main()
