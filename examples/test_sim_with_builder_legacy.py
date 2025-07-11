# examples/test_sim_with_builder.py

from rocket.builder import create_standard_rocket
from core.simulation import WaterRocketSimulator
from core.physics_engine import PhysicsEngine
import matplotlib.pyplot as plt

def run_test_simulation():
    # Step 1: Create rocket configuration using the builder
    config = create_standard_rocket()
    rocket_params = RocketBuilder.from_dict(config.__dict__).to_simulation_params()
    
    # Step 2: Optional simulation parameters
    sim_params = {
        'time_step': 0.01,
        'max_time': 6.0,
        'solver': 'RK45'
    }

    # Step 3: Run simulation
    simulator = WaterRocketSimulator(physics_engine=PhysicsEngine())
    flight_data = simulator.simulate(rocket_params, sim_params)

    # Step 4: Plot altitude
    plt.figure(figsize=(10, 5))
    plt.plot(flight_data.time, flight_data.altitude, label="Altitude")
    plt.plot(flight_data.time, flight_data.velocity, label="Velocity")
    plt.xlabel("Time (s)")
    plt.ylabel("Altitude (m) / Velocity (m/s)")
    plt.title(f"Simulation: {config.name}")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Step 5: Print key results
    print(f"Max Altitude: {flight_data.max_altitude:.2f} m")
    print(f"Max Velocity: {flight_data.max_velocity:.2f} m/s")
    print(f"Total Flight Time: {flight_data.flight_time:.2f} s")
    print(f"Water Depletion Time: {flight_data.water_depletion_time:.2f} s")

if __name__ == "__main__":
    run_test_simulation()
