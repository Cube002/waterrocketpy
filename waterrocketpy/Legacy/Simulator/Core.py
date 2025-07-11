#%%
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Constants
g = 9.81  # gravitational acceleration (m/s^2)
rho_water = 1000  # density of water (kg/m^3)
Pa = 101325  # atmospheric pressure (Pa)
gamma = 1.4  # adiabatic index for air
T0_initial = 300  # Initial temperature of air (K)

# Define the ODE system
def rocket_ode(t, state, params):
    altitude, velocity, water_mass, liquid_gas_mass = state

    # Rocket parameters
    P0 = params['P0']
    A_nozzle = params['A_nozzle']
    V_bottle = params['V_bottle']
    C_d = params['C_d']
    m_empty = params['m_empty']
    C_drag = params['C_drag']
    A_rocket = params['A_rocket']

    # Air volume and pressure
    V_air_initial = V_bottle * (1 - params['water_fraction'])
    V_air = V_bottle - (water_mass / rho_water)
    if V_air <= 0:
        V_air = 1e-10  # Avoid division by zero

    if water_mass > 0 and liquid_gas_mass > 0:
        # Pressure from vaporizing liquid gas
        pressure = 10e5  # 10 bar in Pa (constant while liquid remains)
        dm_dt_liquid_gas = 0  # Vaporization rate (depends on heat transfer)
    else:
        dm_dt_liquid_gas = 0
        # Adiabatic expansion after liquid gas depletes        
        if water_mass > 0:
            # Adiabatic pressure formula
            pressure = P0 * (V_air_initial / V_air) ** gamma
        else:
            pressure = Pa  # Coasting phase

    # Thrust calculation
    if water_mass > 0:
        u_e = C_d * np.sqrt(2 * max((pressure - Pa), 0) / rho_water)
        thrust = rho_water * A_nozzle * u_e**2
        dm_dt = -rho_water * A_nozzle * u_e
    else:
        thrust = 0
        dm_dt = 0

    # Drag calculation
    rho_air = 1.225  # air density at sea level (kg/m^3)
    drag = 0.5 * rho_air * velocity**2 * C_drag * A_rocket * np.sign(velocity)

    # Mass and acceleration
    mass = m_empty + water_mass
    acceleration = (thrust - drag) / mass - g

    # Derivatives
    return [velocity, acceleration, dm_dt, dm_dt_liquid_gas]

# Event function to detect water depletion
def water_depletion(t, state, params):
    return state[2]  # water_mass
water_depletion.terminal = True  # Stop integration when water is depleted
water_depletion.direction = -1  # Trigger when water_mass crosses zero from above

# Simulate the rocket
def simulate_rocket(params, plotflight=False):
    # Initial conditions
    V_water_initial = params['V_bottle'] * params['water_fraction']
    water_mass_initial = rho_water * V_water_initial
    liquid_gas_mass_initial = params['V_bottle']*0.0 #liquid_gas #Propan Option
    y0 = [0.0, 0.0, water_mass_initial,liquid_gas_mass_initial]  # Start at rest (0 altitude, 0 velocity)

    # Time span for integration
    t_span = (0, 10)  # Adjust if needed

    # Solve ODE for thrust phase
    sol_thrust = solve_ivp(
        rocket_ode, t_span, y0, args=(params,),
        events=water_depletion, max_step=0.01
    )

    # If water depletes, simulate coasting phase
    if sol_thrust.t_events[0].size > 0:
        t_deplete = sol_thrust.t_events[0][0]
        y_end_thrust = sol_thrust.y[:, -1]
        y0_coasting = [y_end_thrust[0], y_end_thrust[1], 0.0,0.0]  # No water left
        sol_coasting = solve_ivp(
            rocket_ode, (t_deplete, t_span[1]), y0_coasting, args=(params,),
            max_step=0.01
        )
        # Combine results
        t = np.concatenate((sol_thrust.t, sol_coasting.t))
        y = np.hstack((sol_thrust.y, sol_coasting.y))
    else:
        t = sol_thrust.t
        y = sol_thrust.y

    # Extract states
    altitudes = y[0, :]
    max_altitude = np.max(altitudes)
    
    # Compute pressure and temperature over time
    pressure = []
    temperature = []
    V_air_initial = params['V_bottle'] * (1 - params['water_fraction'])
    for i in range(len(t)):
        water_mass_i = y[2, i]
        liquid_gas_mass_i = y[3, i]
        V_air_i = params['V_bottle'] - (water_mass_i / rho_water)
        if V_air_i <= 0:
            V_air_i = 1e-10
        # Compute pressure
        if liquid_gas_mass_i > 0:
            p_i = 10e5
        elif water_mass_i > 0:
            p_i = params['P0'] * (V_air_initial / V_air_i) ** gamma
        else:
            p_i = Pa
        pressure.append(p_i)
        # Compute temperature
        if liquid_gas_mass_i > 0:
            temp_i = T0_initial  # Placeholder for vaporization phase (not adiabatic)
        elif water_mass_i > 0:
            temp_i = T0_initial * (p_i / params['P0']) ** ((gamma - 1)/gamma)
        else:
            temp_i = T0_initial * (Pa / params['P0']) ** ((gamma - 1)/gamma)
        temperature.append(temp_i)
    
    if plotflight:
        # Plot altitude, pressure, and temperature
        plt.figure(figsize=(15, 5))
        
        # Altitude
        plt.subplot(1, 3, 1)
        plt.plot(t, altitudes)
        plt.xlabel('Time (s)')
        plt.ylabel('Altitude (m)')
        plt.title('Altitude vs Time')
        plt.grid(True)
        
        # Pressure
        plt.subplot(1, 3, 2)
        plt.plot(t, pressure)
        plt.xlabel('Time (s)')
        plt.ylabel('Pressure (Pa)')
        plt.title('Pressure in Rocket vs Time')
        plt.grid(True)
        
        # Temperature
        plt.subplot(1, 3, 3)
        plt.plot(t, temperature)
        plt.xlabel('Time (s)')
        plt.ylabel('Temperature (K)')
        plt.title('Air Temperature vs Time')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

    return max_altitude

# Example parameters
params2 = {
    'P0': 101325 * 10,  # initial pressure (Pa)
    'A_nozzle': np.pi * (0.020 / 2)**2,  # nozzle area (m^2)
    'V_bottle': 0.001,  # bottle volume (m^3)
    'water_fraction': 0.33,  # water fraction
    'C_d': 0.97,  # discharge coefficient
    'm_empty': 0.2,  # empty mass (kg)
    'C_drag': 0.5,  # drag coefficient
    'A_rocket': np.pi * (0.100 / 2)**2  # rocket cross-sectional area (m^2)
}

# Run simulation and plot results
max_altitude = simulate_rocket(params2, plotflight=True)
print(f"Maximum altitude: {max_altitude:.2f} m")