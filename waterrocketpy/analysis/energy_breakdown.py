import numpy as np
from typing import Dict, Any
from dataclasses import dataclass

# Constants (these should match your simulation constants)
WATER_DENSITY = 1000.0  # kg/m³
ATMOSPHERIC_PRESSURE = 101325.0  # Pa
INITIAL_TEMPERATURE = 293.15  # K (20°C)
GRAVITY = 9.81  # m/s²
AIR_SPECIFIC_HEAT_CV = 717.0  # J/(kg·K) for air at constant volume
AIR_SPECIFIC_HEAT_CP = 1004.0  # J/(kg·K) for air at constant pressure
ADIABATIC_INDEX_AIR = 1.4


@dataclass
class EnergyComponents:
    """Container for energy breakdown results."""

    time: np.ndarray

    # Internal energy
    air_internal_energy: np.ndarray

    # Rocket system energy
    rocket_kinetic_energy: np.ndarray
    rocket_potential_energy: np.ndarray
    water_in_kinetic_energy: np.ndarray
    water_in_potential_energy: np.ndarray

    # Expelled fluid energy (cumulative)
    water_out_kinetic_energy: np.ndarray
    water_out_potential_energy: np.ndarray
    air_out_kinetic_energy: np.ndarray
    air_out_potential_energy: np.ndarray

    # Energy losses (cumulative)
    drag_energy_loss: np.ndarray

    # Total energy accounting
    total_initial_energy: float
    total_final_energy: np.ndarray
    energy_conservation_error: np.ndarray

    # Summary values
    max_kinetic_energy: float
    max_potential_energy: float
    total_drag_loss: float
    total_expelled_energy: float


def tenergy_breakdown(
    flight_data, rocket_params: Dict[str, Any]
) -> EnergyComponents:
    """
    Perform comprehensive energy breakdown analysis of water rocket flight.

    Args:
        flight_data: FlightData object from simulation
        rocket_params: Rocket configuration parameters

    Returns:
        EnergyComponents object with detailed energy analysis
    """

    # Extract data arrays
    time = flight_data.time
    altitude = flight_data.altitude
    velocity = flight_data.velocity
    water_mass = flight_data.water_mass
    air_mass = flight_data.air_mass
    pressure = flight_data.pressure
    air_temperature = flight_data.air_temperature
    drag = flight_data.drag
    thrust = flight_data.thrust

    # Calculate rocket mass components
    m_empty = rocket_params["m_empty"]
    total_mass = m_empty + water_mass + air_mass

    # 1. Internal Energy of Pressurized Air
    # Using U = m * cv * T for internal energy
    air_internal_energy = air_mass * AIR_SPECIFIC_HEAT_CV * air_temperature

    # 2. Kinetic Energy of Rocket System
    rocket_kinetic_energy = 0.5 * total_mass * velocity**2

    # 3. Potential Energy of Rocket System
    rocket_potential_energy = total_mass * GRAVITY * altitude

    # 4. Kinetic Energy of Water Inside Rocket
    water_in_kinetic_energy = 0.5 * water_mass * velocity**2

    # 5. Potential Energy of Water Inside Rocket
    water_in_potential_energy = water_mass * GRAVITY * altitude

    # 6. Energy of Expelled Water (cumulative integration)
    water_out_kinetic_energy = np.zeros_like(time)
    water_out_potential_energy = np.zeros_like(time)

    # Calculate expelled water energy by integrating over time
    for i in range(1, len(time)):
        dt = time[i] - time[i - 1]

        # Water mass flow rate (negative since mass is decreasing) NOOOO its
        # the other way around! leaving water / air is defined as positive in
        # the simulation
        if i < len(flight_data.water_mass_flow_rate):
            dm_water_dt = flight_data.water_mass_flow_rate[i]
        else:
            dm_water_dt = 0.0

        if dm_water_dt > 0:  # Water is being expelled
            # Estimate water exhaust velocity
            if flight_data.water_exhaust_speed[i] is not None:
                v_exhaust = flight_data.water_exhaust_speed[i]
            else:
                # Fallback: estimate from thrust and mass flow rate
                if dm_water_dt > 0:
                    v_exhaust = (
                        thrust[i] / dm_water_dt if dm_water_dt > 1e-10 else 0.0
                    )
                else:
                    v_exhaust = 0.0

            # Energy carried away by expelled water
            dE_kin_water = 0.5 * dm_water_dt * v_exhaust**2 * dt
            dE_pot_water = dm_water_dt * GRAVITY * altitude[i] * dt

            water_out_kinetic_energy[i] = (
                water_out_kinetic_energy[i - 1] + dE_kin_water
            )
            water_out_potential_energy[i] = (
                water_out_potential_energy[i - 1] + dE_pot_water
            )
        else:
            water_out_kinetic_energy[i] = water_out_kinetic_energy[i - 1]
            water_out_potential_energy[i] = water_out_potential_energy[i - 1]

    # 7. Energy of Expelled Air (cumulative integration)
    air_out_kinetic_energy = np.zeros_like(time)
    air_out_potential_energy = np.zeros_like(time)

    for i in range(1, len(time)):
        dt = time[i] - time[i - 1]

        # Air mass flow rate
        if i < len(flight_data.air_mass_flow_rate):
            dm_air_dt = flight_data.air_mass_flow_rate[i]
        else:
            dm_air_dt = 0.0

        if dm_air_dt > 0:  # Air is being expelled
            # Estimate air exhaust velocity -> leaving water / air is defined
            # as positive in the simulation
            if flight_data.air_exhaust_speed[i] is not None:
                v_exhaust_air = flight_data.air_exhaust_speed[i]
            else:
                # Fallback: estimate from thrust and mass flow rate
                if dm_air_dt > 0:
                    v_exhaust_air = (
                        thrust[i] / dm_air_dt if dm_air_dt > 1e-10 else 0.0
                    )
                else:
                    v_exhaust_air = 0.0

            # Energy carried away by expelled air
            dE_kin_air = 0.5 * dm_air_dt * v_exhaust_air**2 * dt
            dE_pot_air = dm_air_dt * GRAVITY * altitude[i] * dt

            air_out_kinetic_energy[i] = (
                air_out_kinetic_energy[i - 1] + dE_kin_air
            )
            air_out_potential_energy[i] = (
                air_out_potential_energy[i - 1] + dE_pot_air
            )
        else:
            air_out_kinetic_energy[i] = air_out_kinetic_energy[i - 1]
            air_out_potential_energy[i] = air_out_potential_energy[i - 1]

    # 8. Energy Loss Due to Drag (cumulative)
    drag_energy_loss = np.zeros_like(time)
    for i in range(1, len(time)):
        dt = time[i] - time[i - 1]
        # Energy lost to drag = drag force * distance = drag * velocity * dt
        dE_drag = abs(drag[i]) * abs(velocity[i]) * dt
        drag_energy_loss[i] = drag_energy_loss[i - 1] + dE_drag

    # 9. Calculate Initial Total Energy
    # Initial energy is stored as internal energy in pressurized air
    initial_air_volume = rocket_params["V_bottle"] * (
        1 - rocket_params["water_fraction"]
    )
    initial_air_mass = (rocket_params["P0"] * initial_air_volume) / (
        287.0 * INITIAL_TEMPERATURE
    )  # Using ideal gas law
    total_initial_energy = (
        initial_air_mass * AIR_SPECIFIC_HEAT_CV * INITIAL_TEMPERATURE
    )

    # 10. Energy Conservation Check
    # Total energy at time t should equal:
    # Internal + Kinetic + Potential + Expelled + Losses
    total_final_energy = (
        air_internal_energy
        + rocket_kinetic_energy
        + rocket_potential_energy
        + water_out_kinetic_energy
        + water_out_potential_energy
        + air_out_kinetic_energy
        + air_out_potential_energy
        + drag_energy_loss
    )

    energy_conservation_error = (
        abs(total_final_energy - total_initial_energy)
        / total_initial_energy
        * 100
    )

    # Calculate summary values
    max_kinetic_energy = np.max(rocket_kinetic_energy)
    max_potential_energy = np.max(rocket_potential_energy)
    total_drag_loss = drag_energy_loss[-1]
    total_expelled_energy = (
        water_out_kinetic_energy[-1]
        + water_out_potential_energy[-1]
        + air_out_kinetic_energy[-1]
        + air_out_potential_energy[-1]
    )

    return EnergyComponents(
        time=time,
        air_internal_energy=air_internal_energy,
        rocket_kinetic_energy=rocket_kinetic_energy,
        rocket_potential_energy=rocket_potential_energy,
        water_in_kinetic_energy=water_in_kinetic_energy,
        water_in_potential_energy=water_in_potential_energy,
        water_out_kinetic_energy=water_out_kinetic_energy,
        water_out_potential_energy=water_out_potential_energy,
        air_out_kinetic_energy=air_out_kinetic_energy,
        air_out_potential_energy=air_out_potential_energy,
        drag_energy_loss=drag_energy_loss,
        total_initial_energy=total_initial_energy,
        total_final_energy=total_final_energy,
        energy_conservation_error=energy_conservation_error,
        max_kinetic_energy=max_kinetic_energy,
        max_potential_energy=max_potential_energy,
        total_drag_loss=total_drag_loss,
        total_expelled_energy=total_expelled_energy,
    )
