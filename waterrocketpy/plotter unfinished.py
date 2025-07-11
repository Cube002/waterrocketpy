# waterrocketpy/analysis/plotter.py
"""
Plotting and visualization tools for water rocket flight data.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import List, Dict, Any, Optional, Union, Tuple
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class FlightDataPlotter:
    """Plotting class for flight data visualization."""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        self.figsize = figsize
        self.colors = sns.color_palette("husl", 8)
    
    def plot_flight_trajectory(self, flight_data, title: str = "Flight Trajectory") -> Figure:
        """
        Plot basic flight trajectory (altitude vs time).
        
        Args:
            flight_data: FlightData object
            title: Plot title
            
        Returns:
            Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.plot(flight_data.time, flight_data.altitude, 
                color=self.colors[0], linewidth=2, label='Altitude')
        
        # Mark maximum altitude
        max_idx = np.argmax(flight_data.altitude)
        ax.plot(flight_data.time[max_idx], flight_data.altitude[max_idx], 
                'ro', markersize=8, label=f'Max: {flight_data.max_altitude:.1f}m')
        
        # Mark water depletion
        if flight_data.water_depletion_time > 0:
            ax.axvline(x=flight_data.water_depletion_time, color='orange', 
                      linestyle='--', alpha=0.7, label='Water Depletion')
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Altitude (m)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_multi_variable(self, flight_data, variables: List[str] = None,
                          title: str = "Flight Data") -> Figure:
        """
        Plot multiple variables on subplots.
        
        Args:
            flight_data: FlightData object
            variables: List of variables to plot
            title: Overall title
            
        Returns:
            Figure object
        """
        if variables is None:
            variables = ['altitude', 'velocity', 'acceleration', 'pressure']
        
        n_vars = len(variables)
        n_cols = 2
        n_rows = (n_vars + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
        if n_rows == 1:
            axes = [axes]
        axes = np.array(axes).flatten()
        
        var_configs = {
            'altitude': {'data': flight_data.altitude, 'ylabel': 'Altitude (m)', 'color': 0},
            'velocity': {'data': flight_data.velocity, 'ylabel': 'Velocity (m/s)', 'color': 1},
            'acceleration': {'data': flight_data.acceleration, 'ylabel': 'Acceleration (m/s²)', 'color': 2},
            'pressure': {'data': flight_data.pressure / 1000, 'ylabel': 'Pressure (kPa)', 'color': 3},
            'temperature': {'data': flight_data.temperature, 'ylabel': 'Temperature (K)', 'color': 4},
            'water_mass': {'data': flight_data.water_mass, 'ylabel': 'Water Mass (kg)', 'color': 5},
            'thrust': {'data': flight_data.thrust, 'ylabel': 'Thrust (N)', 'color': 6},
            'drag': {'data': flight_data.drag, 'ylabel': 'Drag (N)', 'color': 7}
        }
        
        for i, var in enumerate(variables):
            if i >= len(axes):
                break
                
            ax = axes[i]
            config = var_configs.get(var, {})
            
            if config:
                ax.plot(flight_data.time, config['data'], 
                       color=self.colors[config['color']], linewidth=2)
                ax.set_ylabel(config['ylabel'])
                ax.set_xlabel('Time (s)')
                ax.set_title(var.replace('_', ' ').title())
                ax.grid(True, alpha=0.3)
                
                # Mark water depletion
                if flight_data.water_depletion_time > 0:
                    ax.axvline(x=flight