# Usage Guide
---

## Quick Start

### Installation

```bash
pip install waterrocketpy
```

### 30-Second Example
```python
from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder,create_standard_rocket

rocket = create_standard_rocket()
builder = RocketBuilder.from_dict(rocket.__dict__)
sim_params = builder.to_simulation_params()

simulator = WaterRocketSimulator()
flight_data = simulator.simulate(sim_params)

print(f"Maximum altitude: {flight_data.max_altitude:.2f} m")
```



### Custom Rocket
```python
"""
Minimal test script to verify the water rocket simulation works.
"""

import sys
import os

from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder,create_standard_rocket

print("✓ All imports successful")

# Create a simple rocket
print("\n1. Creating standard rocket...")
rocket = create_standard_rocket()

print(f"   Rocket created: {rocket.name}")
print(f"   Total mass: {rocket.total_mass:.3f} kg")

# Convert to simulation parameters
print("\n2. Converting to simulation parameters...")
builder = RocketBuilder.from_dict(rocket.__dict__)
sim_params = builder.to_simulation_params()
print(f"   Parameters ready: {len(sim_params)} parameters")

# Run simulation
print("\n3. Running simulation...")
simulator = WaterRocketSimulator()

# Short simulation for testing
sim_settings = {"max_time": 100.0, "time_step": 0.01, "solver": "RK45"}

flight_data = simulator.simulate(sim_params, sim_settings)


print(f"   ✓ Simulation completed successfully!")
print(f"   Maximum altitude: {flight_data.max_altitude:.2f} m")
print(f"   Maximum velocity: {flight_data.max_velocity:.2f} m/s")
print(f"   Flight time: {flight_data.flight_time:.2f} s")
print(f"   Data points: {len(flight_data.time)}")

print("\n✓ Your simulation is working correctly.")
```

This guide covers the simple examples for WaterRocketPy. For additional examples and detailed API documentation, refer to the [API Reference](api/main.md) and [Example Notebooks](examples/).


## Future Contents

1. [Quick Start](#quick-start)
2. [Basic Simulation](#basic-simulation)
3. [Rocket Configuration](#rocket-configuration)
4. [Advanced Analysis](#advanced-analysis)
5. [Optimization](#optimization)
6. [Visualization](#visualization)
7. [Data Management](#data-management)
8. [Batch Processing](#batch-processing)
9. [Common Use Cases](#common-use-cases)
10. [Tips & Best Practices](#tips--best-practices)
