# waterrocketpy/core/constants.py
"""
Physical constants and default values for water rocket simulations.
"""

# Physical Constants
GRAVITY = 9.81  # gravitational acceleration (m/s^2)
WATER_DENSITY = 1000  # density of water (kg/m^3)
AIR_DENSITY_SL = 1.225  # air density at sea level (kg/m^3)
ATMOSPHERIC_PRESSURE = 101325  # atmospheric pressure (Pa)
ADIABATIC_INDEX_AIR = 1.4  # adiabatic index for air
INITIAL_TEMPERATURE = 300  # Initial temperature of air (K)

#New:
GAS_CONSTANT_AIR = 287.05  # specific gas constant for dry air (J/kg·K)
AIR_SPECIFIC_HEAT_RATIO = 1.4  # ratio of specific heats for dry air (Cp/Cv)
WATER_SPECIFIC_HEAT_RATIO = 1.01  # approximate Cp/Cv ratio for liquid water

# Material Properties
PET_DENSITY = 1380  # kg/m^3
PET_TENSILE_STRENGTH = 75e6  # Pa (75 MPa)

ALUMINUM_DENSITY = 2700  # kg/m^3
ALUMINUM_TENSILE_STRENGTH = 310e6  # Pa (310 MPa for 6061-T6)

STEEL_DENSITY = 7850  # kg/m^3
STEEL_TENSILE_STRENGTH = 400e6  # Pa (mild steel)

CARBONFIBER_DENSITY = 1600  # kg/m^3
CARBONFIBER_TENSILE_STRENGTH = 600e6  # Pa (depends on weave, avg ~600 MPa)

# Default Simulation Parameters
DEFAULT_TIME_STEP = 0.01  # seconds
DEFAULT_MAX_TIME = 10.0  # seconds
DEFAULT_SOLVER = 'RK45'

# Default Rocket Parameters
DEFAULT_DISCHARGE_COEFFICIENT = 0.97
DEFAULT_DRAG_COEFFICIENT = 0.5
DEFAULT_NOZZLE_DIAMETER = 0.020  # meters
DEFAULT_ROCKET_DIAMETER = 0.100  # meters
DEFAULT_BOTTLE_VOLUME = 0.001  # cubic meters (1 liter)
DEFAULT_WATER_FRACTION = 0.33
DEFAULT_EMPTY_MASS = 0.2  # kg

# Conversion Factors
BAR_TO_PA = 100000  # 1 bar = 100,000 Pa
LITER_TO_M3 = 0.001  # 1 liter = 0.001 m³
MM_TO_M = 0.001  # 1 mm = 0.001 m