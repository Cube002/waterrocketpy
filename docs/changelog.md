# Changelog

I will try to keep this changelog complete so that all notable changes to WaterRocketPy will be documented in this file. Otherwise I refer to the git-repo for the most up to date changes.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-07-27

### Added
- **Brand Identity**: Added logo and favicon for documentation ([b71f0c2](../../commit/b71f0c2))
- **Documentation Examples**: Added `bare_minimum.ipynb` example for quick start ([3dca9f0](../../commit/3dca9f0))
- **Development Tools**: Enhanced `fix_typos.py` script for better spell checking ([1e7a378](../../commit/1e7a378))
- **Documentation Structure**: Improved documentation index and navigation ([e5a9e38](../../commit/e5a9e38))

### Changed
- **Testing Framework**: Switched from unittest to pytest for better testing experience ([a24b478](../../commit/a24b478))
- **Code Cleanup**: Removed legacy code and cleaned up file structure ([e5a9e38](../../commit/e5a9e38))
- **Documentation**: Improved getting started guide and examples ([3dca9f0](../../commit/3dca9f0))
- **Spell Checking**: Jupyter notebooks now excluded from automatic spell checking ([a9b3326](../../commit/a9b3326))

### Fixed
- **Development Setup**: Fixed testing issues and improved CI/CD pipeline ([3dca9f0](../../commit/3dca9f0))
- **File Organization**: Better organization of documentation assets ([6e16e4a](../../commit/6e16e4a))

## [0.2.0] - 2024

### Major Features Added
- **Advanced Optimization Module**: Complete rocket design optimization system ([598d68b](../../commit/598d68b))
  - Multi-objective optimization (altitude, velocity, flight time)
  - Support for differential evolution and minimization algorithms
  - Constraint handling for physical limitations
  - Comprehensive example scripts and tests
- **Parameter Explorer**: Multi-dimensional parameter sensitivity analysis ([51be841](../../commit/51be841))
  - Visual sensitivity analysis plots
  - Batch parameter sweeps
  - Statistical analysis of parameter effects
- **Data Management System**: Flight data saving and loading utilities ([9436114](../../commit/9436114))
  - JSON and NPZ format support
  - Comprehensive data persistence
  - Test coverage for data operations
- **Advanced Visualization**: Flight data plotting and animation ([407e1c3](../../commit/407e1c3))
  - Comprehensive flight phase visualization
  - Animated trajectory plots
  - Multi-plot dashboard for complete analysis
- **Performance Improvements**: Enhanced simulation engine ([e6b0b7e](../../commit/e6b0b7e))
  - Fixed divide-by-zero errors in time series concatenation
  - Improved numerical stability
  - Better memory management

### Infrastructure & Quality
- **Testing Suite**: Comprehensive test coverage ([60caad4](../../commit/60caad4))
  - Tests for simulator, optimizer, and parameter explorer
  - CI/CD integration with pytest and pytest-cov
  - Automated code linting and quality checks
- **Documentation System**: MkDocs-based documentation ([6e16e4a](../../commit/6e16e4a))
  - Automated API documentation generation ([2f4444a](../../commit/2f4444a))
  - Interactive Jupyter notebook examples
  - Literature references and theoretical background
- **Development Workflow**: Enhanced development experience ([4fac3f3](../../commit/4fac3f3))
  - Restructured dependencies and requirements
  - GitHub Actions for automated testing
  - Cross-platform compatibility (Windows, Ubuntu, macOS)

### Package Structure
- **Modular Architecture**: Organized codebase into logical modules
  - `waterrocketpy/optimization/` - Optimization algorithms
  - `waterrocketpy/visualization/` - Plotting and animation tools
  - `waterrocketpy/utils/` - Data management utilities
  - Enhanced `waterrocketpy/rocket/` - Rocket configuration tools

## [0.1.0] - 2024

### Physics Engine Enhancements
- **Temperature Modeling**: Fixed air temperature calculations during expansion ([a494d89](../../commit/a494d89))
- **Energy Analysis**: Complete energy breakdown analysis system ([321cfd5](../../commit/321cfd5))
  - Energy flow tracking throughout flight phases
  - Detailed energy distribution plots
  - Thermodynamic efficiency calculations
- **Performance Optimization**: ([7a3f076](../../commit/7a3f076))
  - Combined derived data collection with ODE calculations
  - Reduced computational overhead by calculating once instead of twice
  - Improved simulation consistency and accuracy

### Documentation & Literature
- **Literature Integration**: Added comprehensive literature sources ([321cfd5](../../commit/321cfd5))
- **Theoretical Foundation**: Energy flow documentation and physics explanations ([bf37bfd](../../commit/bf37bfd))
- **Reference Runs**: Baseline simulation results for validation

### Code Quality
- **Enhanced Attributes**: Better data structure organization ([bf37bfd](../../commit/bf37bfd))
- **Bug Fixes**: Resolved pressure calculation issues
- **Data Consistency**: Improved data handling and validation

## [0.0.2] - 2024

### Critical Fixes
- **Pressure Calculations**: Fixed fundamental pressure calculation errors ([7207ac3](../../commit/7207ac3))
- **Requirements**: Updated package dependencies for better compatibility ([1c85346](../../commit/1c85346))

### System Improvements
- **Core Updates**: Various system-level improvements and optimizations ([716223a](../../commit/716223a))

## [0.0.1] - 2024

### Initial Release
- **Core Simulation Engine**: Complete water rocket physics simulation ([11880e3](../../commit/11880e3))
  - Water and air mass flow modeling
  - Pressure dynamics during thrust phase
  - Aerodynamic drag modeling
  - Multi-phase flight simulation (thrust, ballistic, landing)
- **Rocket Builder**: Flexible rocket configuration system
  - Standard bottle configurations (2L PET bottles)
  - Custom nozzle designs
  - Material property database
- **Basic Visualization**: Essential plotting capabilities
- **Example Scripts**: Demonstration of core functionality
- **Package Infrastructure**: 
  - PyPI packaging setup
  - MIT License
  - Basic documentation structure

### Foundation Architecture
- **Physics Engine**: Accurate fluid dynamics and thermodynamics modeling
- **Builder System**: Object-oriented rocket configuration
- **Data Output**: Comprehensive time-series flight data
- **Validation**: Parameter validation and error handling

---

## Development Notes

### Version Numbering
- According to the standards of Semantic Versioning 2.0.0
- **Major** versions (X.0.0): Significant API changes or major feature additions
- **Minor** versions (0.X.0): New features, backward-compatible improvements
- **Patch** versions (0.0.X): Bug fixes, documentation updates, minor stuff

### Key Contributors
- **Primary Development**: Pablo
- **Legacy Physics Engine**: Pablo, Jonathan
- **License**: MIT License

### Roadmap Highlights
- Core simulation engine (v0.0.1)
- Physics accuracy improvements (v0.0.2)
- Energy analysis system (v0.1.0) 
- Optimization and advanced analysis (v0.2.0)
- Documentation and tooling (v0.2.1)

- Future: GUI interface, 2.5D visualization, multi-stage rockets, Heatreanfer through the rocket walls, propane and other gases, parashute deployment and affect on decent, rocket spin about the vertical axis.

## TODO´s
- Still working on the sonic air exhaust. This part is still not perfekt as it does not cover pressure spikes.
- More experimental data needed for a perfekt drag model.
- Speed dependent aerodynamik model based on modelrockets.
