`constants.py`

```python
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
```

---

### 📚 Sources:

* **Air Specific Heat Ratio**:
  [NASA Glenn Research Center – Air Properties](https://www.grc.nasa.gov/www/k-12/airplane/airprop.html)

* **Water Specific Heat Ratio**:
  Water has $C_p \approx 4.18 \, \text{kJ/kg·K}$, $C_v \approx 4.14 \, \text{kJ/kg·K}$,
  ⇒ $\gamma = C_p / C_v \approx 1.01$

* **PET (Polyethylene Terephthalate)**:

  * Density: \~1380 kg/m³
  * Tensile strength: \~75 MPa
    Source: [MatWeb - PET](https://www.matweb.com/search/datasheet.aspx?matguid=d4b25e3bdbb04951a1e3e50425b9a1e5)

* **Aluminum (6061-T6)**:

  * Density: 2700 kg/m³
  * Tensile strength: 310 MPa
    Source: [MatWeb - 6061-T6](https://www.matweb.com/search/datasheet.aspx?matguid=af5c8f5a6fcd4d0f8e8b7b68e6ff3c15)

* **Steel (Mild/Low Carbon)**:

  * Density: 7850 kg/m³
  * Tensile strength: 400 MPa (can range widely)
    Source: [AZO Materials - Mild Steel](https://www.azom.com/article.aspx?ArticleID=6115)

* **Carbon Fiber (Average)**:

  * Density: \~1600 kg/m³
  * Tensile strength: \~600 MPa (varies by type and orientation)
    Source: [Matmatch - Carbon Fiber](https://matmatch.com/materials/mamtc005-carbon-fiber)

---

Let me know if you'd like to make these values configurable or include additional materials.
