# waterrocketpy/main.py

from core.simulation import WaterRocketSimulator
from core.physics_engine import PhysicsEngine
import matplotlib.pyplot as plt

# Sample rocket configuration
rocket_params = {
    'V_bottle': 0.002,          # m³ (2 liters)
    'water_fraction': 0.4,      # 40% water
    'P0': 5e5,                  # Initial pressure 5 bar
    'A_nozzle': 0.0005,         # m²
    'C_d': 0.8,                 # Discharge coefficient
    'C_drag': 0.5,              # Drag coefficient
    'A_rocket': 0.01,           # Frontal area in m²
    'm_empty': 0.15,            # kg (empty rocket)
    'liquid_gas_mass': 0.0      # No liquid gas in this test
}

# Optional simulation parameters
sim_params = {
    'time_step': 0.01,
    'max_time': 5.0,
    'solver': 'RK45'
}

simulator = WaterRocketSimulator(physics_engine=PhysicsEngine())
flight_data = simulator.simulate(rocket_params, sim_params)

# Plot altitude over time
plt.plot(flight_data.time, flight_data.altitude)
plt.xlabel("Time (s)")
plt.ylabel("Altitude (m)")
plt.title("Rocket Flight Simulation")
plt.grid()
plt.show()
