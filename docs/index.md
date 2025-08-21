# Welcome to WaterRocketPy

[![PyPI Version](https://img.shields.io/pypi/v/waterrocketpy.svg)](https://pypi.python.org/pypi/waterrocketpy)
[![Build Status](https://github.com/Cube002/waterrocketpy/actions/workflows/windows.yml/badge.svg)](https://github.com/Cube002/waterrocketpy/actions)
[![Python Versions](https://img.shields.io/pypi/pyversions/waterrocketpy.svg)](https://pypi.org/project/waterrocketpy/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The comprehensive Python toolkit for water rocket simulation, analysis, and optimization.**

WaterRocketPy brings the fascinating physics of water rockets to your fingertips. Whether you're an educator demonstrating physics principles, a student conducting research, or an enthusiast optimizing your next launch, this package provides everything you need to understand and predict water rocket performance.

---

## Quick Start

Get up and running in minutes:

```bash
pip install waterrocketpy
```

```python
from waterrocketpy.core.simulation import WaterRocketSimulator
from waterrocketpy.rocket.builder import RocketBuilder,create_standard_rocket

rocket = create_standard_rocket()
builder = RocketBuilder.from_dict(rocket.__dict__)
sim_params = builder.to_simulation_params()

simulator = WaterRocketSimulator()
flight_data = simulator.simulate(sim_params)

print(f"Maximum altitude: {flight_data.max_altitude:.2f} m")
print(f"Flight time: {flight_data.flight_time:.1f} s")
```

**That's it!** You've just simulated your first water rocket.
---

## Key Capabilities

### Physics-Based Simulation Engine (Core)
- **Complete Flight Modeling**: From water thrust through air thrust to ballistic flight and landing
- **Thermodynamic Accuracy**: Temperature-dependent air expansion, pressure dynamics, and compressible flow
- **Multiple Solver Support**: Runge-Kutta methods (RK45, RK23) with adaptive time stepping
- **Detailed Output**: 20+ time-series parameters including forces, pressures, temperatures, and flow rates

### Rocket Design & Configuration (Rocket)
- **Flexible Builder System**: Create custom rockets with different bottle sizes, nozzles, and materials
- **Material Database**: Built-in properties for PET, HDPE, and other common bottle materials
- **Standard Configurations**: Pre-built rocket templates for quick prototyping
- **Validation System**: Automatic parameter checking for physical constraints

### Advanced Analysis Tools (Analysis)
- **Parameter Explorer**: Multi-dimensional sensitivity analysis with interactive visualizations
- **Energy Breakdown**: Detailed tracking of energy flow and losses throughout flight
- **Phase Detection**: Automatic identification of water thrust, air thrust, ballistic, and descent phases
- **Statistical Analysis**: Batch processing for Monte Carlo simulations and uncertainty quantification

### Optimization Capabilities (Optimization)
- **Multi-Objective Optimization**: Simultaneously optimize for altitude, velocity, and flight time
- **Constraint Handling**: Physical limits on pressure, geometry, and materials
- **Algorithm Selection**: Differential evolution, Nelder-Mead, and custom optimization strategies
- **Design Exploration**: Automated parameter sweeps and design space visualization

### Visualization Suite (Visualization)
- **Flight Visualization**: Plotting of all flight parameters with phase highlighting
- **2D Trajectory Animation**: Real-time flight path visualization for presentations
- **Batch Comparison**: Multi-run analysis with statistical summaries
- **Energy Flow Diagrams**: Sankey diagrams showing energy distribution and losses
---

## Package Architecture

WaterRocketPy is organized into six main modules, each serving a specific purpose:

```
waterrocketpy/
├── core/          # Simulation engine and physics calculations
├── rocket/        # Rocket design and configuration tools
├── optimization/  # Parameter optimization algorithms  
├── visualization/ # Plotting, animation, and data exploration
├── analysis/      # Advanced analysis and energy breakdowns
└── utils/         # Data I/O, validation, and utilities
```

![Package Structure](images/package_structure.jpg)

### Core Module
The heart of WaterRocketPy, containing the physics engine and main simulator:
- `simulation.py` - Main simulation controller and data management
- `physics_engine.py` - All physics calculations and equations of motion  
- `constants.py` - Physical constants and default parameters
- `validation.py` - Parameter validation and error checking

### Rocket Module
Tools for defining and building rocket configurations:
- `builder.py` - Rocket builder classes and standard configurations
- `geometry.py` - Geometric calculations for bottles and nozzles
- `materials.py` - Material properties database and calculations

### Optimization Module
Advanced optimization capabilities for rocket design:
- `water_rocket_optimizer.py` - Multi-objective optimization with various algorithms

### Visualization Module
Comprehensive plotting and animation tools:
- `plot_flight_data.py` - Standard flight data visualization
- `parameter_explorer.py` - Interactive parameter exploration
- `flight_animation.py` - 3D trajectory animations

### Analysis Module  
Advanced analysis tools for deeper insights:
- `energy_breakdown.py` - Energy flow analysis throughout flight
- `energy_breakdown_plot.py` - Visualization of energy distributions

### Utils Module
Supporting utilities for data management:
- `saver.py` - Save simulation results in multiple formats
- `loader.py` - Load and process simulation data

---

## Getting Started

### Installation

**From PyPI (Recommended):**
```bash
pip install waterrocketpy
```

**From Source:**
```bash
git clone https://github.com/Cube002/waterrocketpy.git
cd waterrocketpy
pip install -e .
```

### Your First Simulation

Try our interactive examples:

- **[Bare Minimum Example](examples/bare_minimum.ipynb)** - Get started in 30 seconds
- **[Getting Started Guide](examples/getting_started.ipynb)** - Complete walkthrough with explanations  
- **[Introduction Notebook](examples/intro.ipynb)** - Comprehensive introduction to all features

### Example Gallery

Explore real-world applications:

```python
# Parameter optimization
from waterrocketpy.optimization import optimize_for_altitude
result = optimize_for_altitude(maxiter=50)

# Energy analysis  
from waterrocketpy.analysis import plot_energy_breakdown
plot_energy_breakdown(flight_data)

# Parameter exploration
from waterrocketpy.visualization import ParameterExplorer
explorer = ParameterExplorer()
explorer.explore_parameters(param_ranges)
```

---

## Educational Applications

WaterRocketPy is designed with education in mind:

- **Physics Demonstrations**: Instantly visualize complex physics concepts
- **Student Research Projects**: Tools for hypothesis testing and experimental design
- **Competition Preparation**: Optimize designs for maximum performance
- **Curriculum Integration**: Ready-made examples for classroom use

### Physics Concepts Covered
- Fluid dynamics and Bernoulli's principle
- Thermodynamics and adiabatic processes  
- Conservation of mass, energy, and momentum
- Aerodynamics and drag modeling
- Optimization and engineering design

---

## Community & Support

- **Documentation**: Comprehensive guides and API reference
- **Examples**: 10+ detailed example scripts and Jupyter notebooks
- **GitHub**: Source code, issues, and discussions
- **PyPI**: Easy installation and version management

### Contributing

We welcome contributions of all kinds:
- Bug reports and feature requests
- Code improvements and new features
- Documentation enhancements
- Example scripts and use cases

See our [Contributing Guidelines](contributing.md) for details.

---

## License & Credits

- **License**: MIT License - Free for academic and commercial use
- **Author**: Pablo M (pablo.marg8@gmail.com)
- **Physics Models**: Based on established fluid dynamics principles
- **Dependencies**: NumPy, SciPy, Matplotlib

---

Ready to explore the physics of water rockets? **[Get started now →](usage.md)**

