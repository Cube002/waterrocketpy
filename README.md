# WaterRocketPy 🚀
![Logo](docs/assets/logo.png)

[![PyPI Version](https://img.shields.io/pypi/v/waterrocketpy.svg)](https://pypi.python.org/pypi/waterrocketpy)
[![Build Status](https://github.com/Cube002/waterrocketpy/actions/workflows/windows.yml/badge.svg)](https://github.com/Cube002/waterrocketpy/actions)
[![Python Versions](https://img.shields.io/pypi/pyversions/waterrocketpy.svg)](https://pypi.org/project/waterrocketpy/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The Python package for water rocket simulation, analysis, and optimization.**

WaterRocketPy provides a complete toolkit for modeling the physics of water rockets, from initial pressurization through thrust phase, ballistic flight, and landing. Whether you're an educator, student, hobbyist, or researcher, this package offers both simple interfaces for quick simulations and advanced tools for detailed analysis.

## Key Features

### Core Simulation Engine
- **Physics-Based Modeling**: Accurate simulation of water rocket flight dynamics including:
  - Water and air mass flow through nozzle
  - Pressure dynamics during thrust phase
  - Aerodynamic drag during ballistic phase
  - Temperature effects on air expansion
- **Multiple Integration Methods**: Support for various numerical solvers (RK45, RK23, etc.)
- **Complete Data Output**: Time series data for altitude, velocity, acceleration, pressure, temperature, mass flow rates, and more

### Rocket Configuration & Building
- **Flexible Rocket Builder**: Create custom rocket configurations with various bottle sizes, nozzle designs, and materials
- **Material Database**: Built-in material properties for common bottle materials (PET, HDPE, etc.)
- **Standard Configurations**: Pre-defined rocket configurations for quick prototyping

### Advanced Analysis Tools
- **Parameter Explorer**: Multi-dimensional parameter sensitivity analysis
- **Energy Breakdown**: Detailed energy flow analysis throughout flight phases to see where energy gets lost
- **Flight Phase Detection**: Automatic identification of water/air thrust, ballistic, and descent phases

### Optimization Capabilities
- **Multi-Objective Optimization**: Optimize for maximum altitude, velocity, or flight time
- **Constraint Handling**: Physical and practical constraints on rocket parameters
- **Multiple Algorithms**: Support for differential evolution, minimization methods, and custom optimization strategies

### Rich Visualization
- **Comprehensive Plotting**: Pre-built plotting functions for all flight parameters
- **Flight Animation**: Animated trajectory visualization (for education)
- **Batch Analysis**: Compare multiple simulation runs with organized plot outputs, 3D apogee landscapes and more

## Installation

### From PyPI (Recommended)
```bash
pip install waterrocketpy
```

### From Source
```bash
git clone https://github.com/Cube002/waterrocketpy.git
cd waterrocketpy
pip install -e .
```

### Dependencies
- Python ≥ 3.8
- NumPy: Numerical computations
- SciPy: ODE solving and optimization
- Matplotlib: Visualization and plotting

## Quick Start

### Basic Simulation
```python
from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.core.physics_engine import PhysicsEngine
import matplotlib.pyplot as plt

# Define rocket parameters
rocket_params = {
    "V_bottle": 0.002,        # 2L bottle volume (m³)
    "water_fraction": 0.4,    # 40% filled with water
    "P0": 5e5,                # 5 bar initial pressure (Pa)
    "A_nozzle": 0.0005,       # Nozzle area (m²)
    "C_d": 0.8,               # Discharge coefficient
    "C_drag": 0.5,            # Drag coefficient
    "A_rocket": 0.01,         # Frontal area (m²)
    "m_empty": 0.15,          # Empty rocket mass (kg)
}

# Simulation settings
sim_params = {"time_step": 0.01, "max_time": 10.0, "solver": "RK45"}

# Run simulation
simulator = WaterRocketSimulator(physics_engine=PhysicsEngine())
flight_data = simulator.simulate(rocket_params, sim_params)

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(flight_data.time, flight_data.altitude)
plt.xlabel("Time (s)")
plt.ylabel("Altitude (m)")
plt.title("Water Rocket Flight Simulation")
plt.grid(True)
plt.show()

print(f"Maximum altitude: {flight_data.max_altitude:.2f} m")
print(f"Flight time: {flight_data.flight_time:.2f} s")
```

### Using the Rocket Builder
```python
from waterrocketpy.rocket.builder import RocketBuilder, create_standard_rocket
from waterrocketpy.core.simulation import WaterRocketSimulator

# Create a standard rocket configuration
rocket = create_standard_rocket()

# Convert to simulation parameters
builder = RocketBuilder.from_dict(rocket.__dict__)
sim_params = builder.to_simulation_params()

# Run simulation
simulator = WaterRocketSimulator()
flight_data = simulator.simulate(sim_params, {"max_time": 100.0})

print(f"Max altitude: {flight_data.max_altitude:.2f} m")
print(f"Max velocity: {flight_data.max_velocity:.2f} m/s")
```

### Parameter Optimization
```python
from waterrocketpy.optimization.water_rocket_optimizer import optimize_for_altitude

# Optimize rocket design for maximum altitude
result = optimize_for_altitude(
    method="differential_evolution",
    maxiter=50,
    popsize=15
)

print(f"Optimized altitude: {result['best_value']:.2f} m")
print("Optimal parameters:")
for param, value in result['best_params'].items():
    print(f"  {param}: {value:.4f}")
```

## Advanced Examples

### Detailed Flight Analysis
```python
from waterrocketpy.visualization.plot_flight_data import (
    plot_trajectory_and_velocity,
    plot_forces_and_acceleration,
    plot_propellant_and_pressure,
    identify_flight_phases
)

# Run simulation (as above)
flight_data = simulator.simulate(sim_params, {"max_time": 100.0})

# Identify flight phases
phases = identify_flight_phases(flight_data)

# Create detailed plots
fig1 = plot_trajectory_and_velocity(flight_data, phases)
fig2 = plot_forces_and_acceleration(flight_data, phases)
fig3 = plot_propellant_and_pressure(flight_data, phases)

plt.show()
```

### Parameter Sensitivity Analysis
```python
from waterrocketpy.visualization.parameter_explorer import ParameterExplorer

explorer = ParameterExplorer()

# Define parameter ranges
param_ranges = {
    'water_fraction': [0.2, 0.6],     # 20-60% water
    'P0': [3e5, 8e5],                 # 3-8 bar pressure
    'A_nozzle': [0.0003, 0.001]       # Nozzle size range
}

# Run parameter sweep
results = explorer.explore_parameters(
    base_rocket=create_standard_rocket(),
    param_ranges=param_ranges,
    target_metric='max_altitude'
)

explorer.plot_sensitivity_analysis(results)
```

### Batch Processing & Comparison
The package includes utilities for running multiple simulations and comparing results:

```python
# Example: Compare different pressure settings
pressures = [3e5, 4e5, 5e5, 6e5, 7e5]  # 3-7 bar
results = []

for P in pressures:
    params = rocket_params.copy()
    params['P0'] = P
    flight_data = simulator.simulate(params, sim_params)
    results.append({
        'pressure_bar': P/1e5,
        'max_altitude': flight_data.max_altitude,
        'max_velocity': flight_data.max_velocity,
        'flight_time': flight_data.flight_time
    })

# Plot comparison
import pandas as pd
df = pd.DataFrame(results)
df.plot(x='pressure_bar', y=['max_altitude', 'max_velocity'], 
        subplots=True, figsize=(10, 8))
```

## Package Structure

```
waterrocketpy/
├── core/                    # Core simulation engine
│   ├── physics_engine.py    # Physics calculations
│   ├── simulation.py        # Main simulator
│   ├── constants.py         # Physical constants
│   └── validation.py        # Parameter validation
├── rocket/                  # Rocket configuration tools  
│   ├── builder.py           # Rocket builder classes
│   ├── geometry.py          # Geometric calculations
│   └── materials.py         # Material properties
├── optimization/            # Optimization algorithms
│   └── water_rocket_optimizer.py
├── visualization/           # Plotting and visualization
│   ├── plot_flight_data.py  # Flight data plots
│   ├── parameter_explorer.py # Parameter analysis
│   └── flight_animation.py  # Animated visualizations
├── analysis/                # Advanced analysis tools
│   ├── energy_breakdown.py  # Energy flow analysis
│   └── energy_breakdown_plot.py
└── utils/                   # Utilities
    ├── loader.py            # Data loading
    └── saver.py             # Data saving
```
![Package structure Diagram](docs/images/package_structure.jpg)

## Included Examples

The package includes numerous example scripts in the `examples/` directory:

### Core Examples
- `use_basic_functionality.py` - Basic simulation setup and execution
- `main.py` - Simple example with plotting

### Visualization Examples  
- `use_plot_flight_data.py` - Comprehensive flight data visualization
- `use_basic_functionality_animate.py` - Animated flight trajectories

### Analysis Examples
- `use_parameter_explorer_simple.py` - Parameter sensitivity analysis
- `use_parameter_explorer_multiple_Parameters.py` - Multi-parameter exploration

### Optimization Examples
- `use_water_rocket_optimizer.py` - Rocket design optimization

## Physics Model

The simulation engine models the complete water rocket flight profile:

1. **Water Thrust Phase**: Water expulsion under pressure
   - Bernoulli's equation for flow rate
   - Adiabatic expansion of compressed air
   - Temperature effects on gas properties

2. **Air Thrust Phase**: Water expulsion under pressure
   - Time step wise Bernoulli's equation for flow rate
   - (Sonic) exhaust of compressed air through a Converging or Converging Diverging Nozzle

3. **Ballistic Phase**: Unpowered flight
   - Gravitational acceleration
   - Aerodynamic drag (quadratic)
   - Air density variation with altitude

4. **Landing Phase**: Impact detection and final state

Key physical relationships implemented:
- Implicit Conservation of mass energy and momentum
- Ideal gas law with temperature corrections
- Compressible flow through nozzles
- Standard atmosphere model
- Aerodynamik drag based on modelrocket data

## Output Data

Each simulation provides comprehensive time-series data:

- **Trajectory**: altitude, velocity, acceleration
- **Propulsion**: thrust, mass flow rates (water/air), exhaust velocities
- **Thermodynamics**: pressure, temperature, gas masses
- **Forces**: drag force, net force
- **Performance**: phase identification, peak values, flight time

## Educational Use

WaterRocketPy is designed for educational applications:
- **Classroom Demonstrations**: Quick simulations with immediate visual feedback
- **Student Projects**: Tools for hypothesis testing and design optimization
- **Research Applications**: Detailed physics modeling for advanced studies
- **Competition Preparation**: Optimization tools for rocket competitions

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details on:
- Bug reports and feature requests
- Code contributions and pull requests  
- Documentation improvements
- Example submissions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Physics models based on established fluid dynamics principles from the book to the lecture Fluidmechanik (Aachener Beiträge zur Strömungsmechanik) ISBN 978-3-95886-221-0

## Links

- **Documentation**: https://Cube002.github.io/waterrocketpy
- **PyPI Package**: https://pypi.org/project/waterrocketpy/
- **Source Code**: https://github.com/Cube002/waterrocketpy
- **Issue Tracker**: https://github.com/Cube002/waterrocketpy/issues

---

*Ready to launch your water rocket simulations? Install WaterRocketPy today and start exploring the physics of water propulsion before building your own PET-Bottle Waterrocket and becomming as fascinated as me :D*
