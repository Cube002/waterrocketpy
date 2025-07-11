#!/usr/bin/env python3
"""
Energy breakdown plotter for water rocket simulation.

This module provides physics-based energy analysis tools for understanding
how energy flows through the water rocket system during flight.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

from ..core.simulation import FlightData
from ..core.constants import (
    WATER_DENSITY, ATMOSPHERIC_PRESSURE, GRAVITY, 
    AIR_SPECIFIC_HEAT_RATIO, GAS_CONSTANT_AIR
)


@dataclass
class EnergyComponents:
    """Container for energy breakdown components."""
    time: np.ndarray
    initial_stored_energy: float
    kinetic_energy_rocket: np.ndarray
    potential_energy_rocket: np.ndarray
    kinetic_energy_expelled_water: np.ndarray
    energy_lost_to_drag: np.ndarray
    internal_energy_change: np.ndarray
    total_energy_accounted: np.ndarray
    energy_balance_error: np.ndarray


class EnergyAnalyzer:
    """Physics-based energy analysis for water rocket flight."""
    
    def __init__(self):
        self.gamma = AIR_SPECIFIC_HEAT_RATIO  # Specific heat ratio for air
        self.R = GAS_CONSTANT_AIR  # Gas constant for air
        self.g = GRAVITY
        self.rho_water = WATER_DENSITY
        self.P_atm = ATMOSPHERIC_PRESSURE
    
    def calculate_initial_stored_energy(self, rocket_params: Dict[str, Any]) -> float:
        """
        Calculate initial energy stored in pressurized air.
        
        Uses the formula for internal energy of an ideal gas:
        U = (P * V) / (gamma - 1)
        
        Args:
            rocket_params: Rocket configuration parameters
            
        Returns:
            Initial stored energy in Joules
        """
        P0 = rocket_params['P0']  # Initial pressure
        V_bottle = rocket_params['V_bottle']  # Total bottle volume
        water_fraction = rocket_params['water_fraction']
        
        # Initial air volume (volume not occupied by water)
        V_air_initial = V_bottle * (1 - water_fraction)
        
        # Initial internal energy of compressed air
        # For ideal gas: U = (P * V) / (gamma - 1)
        U_initial = (P0 * V_air_initial) / (self.gamma - 1)
        
        # Also account for the work potential relative to atmospheric pressure
        # Work available = (P0 - P_atm) * V_air_initial / (gamma - 1)
        work_potential = ((P0 - self.P_atm) * V_air_initial) / (self.gamma - 1)
        
        return U_initial + work_potential
    
    def calculate_kinetic_energy_rocket(self, flight_data: FlightData, 
                                      rocket_params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate kinetic energy of the rocket (remaining mass).
        
        KE = 0.5 * m * v^2
        """
        m_empty = rocket_params['m_empty']
        
        # Current mass of rocket = empty mass + remaining water mass
        current_mass = m_empty + flight_data.water_mass
        
        # Kinetic energy of rocket
        kinetic_energy = 0.5 * current_mass * flight_data.velocity**2
        
        return kinetic_energy
    
    def calculate_potential_energy_rocket(self, flight_data: FlightData, 
                                        rocket_params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate gravitational potential energy of the rocket.
        
        PE = m * g * h
        """
        m_empty = rocket_params['m_empty']
        
        # Current mass of rocket = empty mass + remaining water mass
        current_mass = m_empty + flight_data.water_mass
        
        # Potential energy of rocket
        potential_energy = current_mass * self.g * flight_data.altitude
        
        return potential_energy
    
    def calculate_expelled_water_energy(self, flight_data: FlightData, 
                                      rocket_params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate kinetic energy of expelled water.
        
        This is more complex as we need to track the velocity of expelled water
        and integrate over time.
        """
        # Initial water mass
        V_water_initial = rocket_params['V_bottle'] * rocket_params['water_fraction']
        m_water_initial = self.rho_water * V_water_initial
        
        # Mass of expelled water at each time step
        expelled_water_mass = m_water_initial - flight_data.water_mass
        
        # Estimate expelled water velocity using nozzle exit velocity
        # For simplicity, we'll use thrust and pressure data
        expelled_water_energy = np.zeros_like(flight_data.time)
        
        for i in range(1, len(flight_data.time)):
            dt = flight_data.time[i] - flight_data.time[i-1]
            
            # Mass flow rate
            dm_dt = -(flight_data.water_mass[i] - flight_data.water_mass[i-1]) / dt
            
            if dm_dt > 0 and flight_data.pressure[i] > self.P_atm:
                # Estimate nozzle exit velocity using Torricelli's equation
                # v_exit = sqrt(2 * (P - P_atm) / rho_water)
                pressure_diff = flight_data.pressure[i] - self.P_atm
                v_exit = np.sqrt(2 * pressure_diff / self.rho_water)
                
                # Energy of expelled water in this time step
                dE_expelled = 0.5 * dm_dt * dt * v_exit**2
                
                # Accumulate energy
                expelled_water_energy[i] = expelled_water_energy[i-1] + dE_expelled
            else:
                expelled_water_energy[i] = expelled_water_energy[i-1]
        
        return expelled_water_energy
    
    def calculate_drag_energy_loss(self, flight_data: FlightData) -> np.ndarray:
        """
        Calculate energy lost to drag.
        
        Work done against drag = F_drag * distance
        """
        drag_energy_loss = np.zeros_like(flight_data.time)
        
        for i in range(1, len(flight_data.time)):
            dt = flight_data.time[i] - flight_data.time[i-1]
            
            # Distance traveled in this time step
            distance = flight_data.velocity[i] * dt
            
            # Work done against drag
            work_drag = flight_data.drag[i] * distance
            
            # Accumulate energy loss
            drag_energy_loss[i] = drag_energy_loss[i-1] + work_drag
        
        return drag_energy_loss
    
    def calculate_internal_energy_change(self, flight_data: FlightData, 
                                       rocket_params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate change in internal energy of the air due to expansion and cooling.
        
        For adiabatic process: dU = (1/(gamma-1)) * (P_final * V_final - P_initial * V_initial)
        """
        P0 = rocket_params['P0']
        V_bottle = rocket_params['V_bottle']
        water_fraction = rocket_params['water_fraction']
        
        # Initial air volume
        V_air_initial = V_bottle * (1 - water_fraction)
        
        # Initial internal energy
        U_initial = (P0 * V_air_initial) / (self.gamma - 1)
        
        # Current air volume (increases as water is expelled)
        V_air_current = V_bottle - flight_data.water_mass / self.rho_water
        
        # Current internal energy
        U_current = (flight_data.pressure * V_air_current) / (self.gamma - 1)
        
        # Change in internal energy (negative means energy released)
        internal_energy_change = U_current - U_initial
        
        return internal_energy_change
    
    def analyze_energy_breakdown(self, flight_data: FlightData, 
                               rocket_params: Dict[str, Any]) -> EnergyComponents:
        """
        Perform complete energy breakdown analysis.
        
        Args:
            flight_data: Flight simulation results
            rocket_params: Rocket configuration parameters
            
        Returns:
            EnergyComponents with all energy terms
        """
        # Calculate initial stored energy
        E_initial = self.calculate_initial_stored_energy(rocket_params)
        
        # Calculate energy components
        KE_rocket = self.calculate_kinetic_energy_rocket(flight_data, rocket_params)
        PE_rocket = self.calculate_potential_energy_rocket(flight_data, rocket_params)
        KE_expelled = self.calculate_expelled_water_energy(flight_data, rocket_params)
        E_drag_loss = self.calculate_drag_energy_loss(flight_data)
        dU_internal = self.calculate_internal_energy_change(flight_data, rocket_params)
        
        # Total energy accounted for
        E_total_accounted = KE_rocket + PE_rocket + KE_expelled + E_drag_loss + dU_internal
        
        # Energy balance error
        E_balance_error = E_initial - E_total_accounted
        
        return EnergyComponents(
            time=flight_data.time,
            initial_stored_energy=E_initial,
            kinetic_energy_rocket=KE_rocket,
            potential_energy_rocket=PE_rocket,
            kinetic_energy_expelled_water=KE_expelled,
            energy_lost_to_drag=E_drag_loss,
            internal_energy_change=dU_internal,
            total_energy_accounted=E_total_accounted,
            energy_balance_error=E_balance_error
        )


def plot_energy_breakdown(flight_data: FlightData, rocket_params: Dict[str, Any] = None, 
                         save_path: Optional[str] = None, show_plot: bool = True):
    """
    Create comprehensive energy breakdown plot for water rocket flight.
    
    This function analyzes and visualizes how energy flows through the water rocket
    system, showing the conversion from initial stored energy in pressurized air
    to various forms of kinetic, potential, and dissipated energy.
    
    Args:
        flight_data: Flight simulation results
        rocket_params: Rocket configuration parameters (required for energy analysis)
        save_path: Optional path to save the plot
        show_plot: Whether to display the plot
    """
    if rocket_params is None:
        raise ValueError("rocket_params is required for energy analysis")
    
    # Perform energy analysis
    analyzer = EnergyAnalyzer()
    energy_components = analyzer.analyze_energy_breakdown(flight_data, rocket_params)
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('Water Rocket Energy Breakdown Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Energy components over time
    ax1.plot(energy_components.time, energy_components.kinetic_energy_rocket, 
             'b-', linewidth=2, label='Rocket Kinetic Energy')
    ax1.plot(energy_components.time, energy_components.potential_energy_rocket, 
             'g-', linewidth=2, label='Rocket Potential Energy')
    ax1.plot(energy_components.time, energy_components.kinetic_energy_expelled_water, 
             'r-', linewidth=2, label='Expelled Water Kinetic Energy')
    ax1.plot(energy_components.time, energy_components.energy_lost_to_drag, 
             'orange', linewidth=2, label='Energy Lost to Drag')
    ax1.plot(energy_components.time, -energy_components.internal_energy_change, 
             'purple', linewidth=2, label='Internal Energy Released')
    
    # Add initial energy reference line
    ax1.axhline(y=energy_components.initial_stored_energy, color='black', 
                linestyle='--', linewidth=1, alpha=0.7, 
                label=f'Initial Stored Energy ({energy_components.initial_stored_energy:.1f} J)')
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Energy (J)')
    ax1.set_title('Energy Components vs Time')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Energy balance and cumulative energy
    ax2.plot(energy_components.time, energy_components.total_energy_accounted, 
             'navy', linewidth=2, label='Total Energy Accounted')
    ax2.plot(energy_components.time, energy_components.energy_balance_error, 
             'red', linewidth=2, label='Energy Balance Error')
    ax2.axhline(y=energy_components.initial_stored_energy, color='black', 
                linestyle='--', linewidth=1, alpha=0.7, 
                label=f'Initial Stored Energy')
    ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Energy (J)')
    ax2.set_title('Energy Balance Check')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # Add text box with energy summary
    initial_energy = energy_components.initial_stored_energy
    final_ke = energy_components.kinetic_energy_rocket[-1]
    final_pe = energy_components.potential_energy_rocket[-1]
    final_expelled = energy_components.kinetic_energy_expelled_water[-1]
    final_drag = energy_components.energy_lost_to_drag[-1]
    final_internal = -energy_components.internal_energy_change[-1]
    
    energy_summary = f"""Energy Summary:
Initial Stored: {initial_energy:.1f} J
Final Rocket KE: {final_ke:.1f} J ({final_ke/initial_energy*100:.1f}%)
Final Rocket PE: {final_pe:.1f} J ({final_pe/initial_energy*100:.1f}%)
Expelled Water KE: {final_expelled:.1f} J ({final_expelled/initial_energy*100:.1f}%)
Lost to Drag: {final_drag:.1f} J ({final_drag/initial_energy*100:.1f}%)
Internal Energy Released: {final_internal:.1f} J ({final_internal/initial_energy*100:.1f}%)
Balance Error: {energy_components.energy_balance_error[-1]:.1f} J"""
    
    ax2.text(0.02, 0.98, energy_summary, transform=ax2.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
             fontsize=9, family='monospace')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Energy breakdown plot saved to: {save_path}")
    
    if show_plot:
        plt.show()
    
    # Print energy analysis summary
    print("\n=== Energy Analysis Summary ===")
    print(f"Initial stored energy: {initial_energy:.2f} J")
    print(f"Energy conversion efficiency: {(final_ke + final_pe)/initial_energy*100:.1f}%")
    print(f"Energy lost to drag: {final_drag/initial_energy*100:.1f}%")
    print(f"Energy in expelled water: {final_expelled/initial_energy*100:.1f}%")
    print(f"Internal energy change: {final_internal/initial_energy*100:.1f}%")
    print(f"Energy balance error: {abs(energy_components.energy_balance_error[-1])/initial_energy*100:.2f}%")
    
    return energy_components


def plot_energy_pie_chart(energy_components: EnergyComponents, 
                         save_path: Optional[str] = None, show_plot: bool = True):
    """
    Create a pie chart showing final energy distribution.
    
    Args:
        energy_components: Energy breakdown results
        save_path: Optional path to save the plot
        show_plot: Whether to display the plot
    """
    # Get final energy values
    final_ke_rocket = energy_components.kinetic_energy_rocket[-1]
    final_pe_rocket = energy_components.potential_energy_rocket[-1]
    final_ke_expelled = energy_components.kinetic_energy_expelled_water[-1]
    final_drag_loss = energy_components.energy_lost_to_drag[-1]
    final_internal = -energy_components.internal_energy_change[-1]
    
    # Prepare data for pie chart
    labels = ['Rocket KE', 'Rocket PE', 'Expelled Water KE', 'Drag Loss', 'Internal Energy']
    sizes = [final_ke_rocket, final_pe_rocket, final_ke_expelled, final_drag_loss, final_internal]
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                     startangle=90, textprops={'fontsize': 10})
    
    ax.set_title(f'Final Energy Distribution\n(Total: {sum(sizes):.1f} J)', 
                 fontsize=14, fontweight='bold')
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Energy pie chart saved to: {save_path}")
    
    if show_plot:
        plt.show()