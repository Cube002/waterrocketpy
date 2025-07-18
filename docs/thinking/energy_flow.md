
---

### **Energy Flow in a PET Water Rocket**

At launch, all **available energy** is stored as **internal energy** in the **pressurized air** inside the rocket. As the rocket launches and the nozzle opens, this energy is transformed and distributed among various components:

---

#### **1. Internal Energy of the Pressurized Air**

* **Stored Energy Source**

  * Comprised of **pressure** and **temperature** (i.e., enthalpy).
  * Can be estimated via:

    $$
    U_{\text{air}} = m_{\text{air}} \cdot c_v \cdot T
    $$
  * Or for enthalpy:

    $$
    H_{\text{air}} = m_{\text{air}} \cdot c_p \cdot T
    $$

#### **2. Kinetic & Potential Energy of the Rocket**

* Energy transferred to the **empty rocket body** and remaining internal fluid.

  * Kinetic:

    $$
    E_{\text{kin, rocket}} = \frac{1}{2} m_{\text{rocket}} v^2
    $$
  * Potential:

    $$
    E_{\text{pot, rocket}} = m_{\text{rocket}} g h
    $$
  * Where:

    * $m_{\text{rocket}} = m_{\text{empty}} + m_{\text{air}} + m_{\text{water}}$

#### **3. Kinetic & Potential Energy of the Remaining Water Inside the Rocket**

* Similar to the rocket, since the water is moving with the same velocity:

  $$
  E_{\text{kin, water-in}} = \frac{1}{2} m_{\text{water}} v^2, \quad
  E_{\text{pot, water-in}} = m_{\text{water}} g h
  $$

#### **4. Kinetic & Potential Energy of Expelled Water**

* Represents the **integral** of kinetic and potential energy carried by water as it exits the nozzle:

  $$
  E_{\text{water-out}}(t) = \int_0^t \left( \frac{1}{2} \dot{m}_{\text{water}}(t') v_{\text{ex}}(t')^2 + \dot{m}_{\text{water}}(t') g h(t') \right) dt'
  $$

* The values can be **approximated** using:

  * `water_mass(t)` (to find $\dot{m}_{\text{water}}$)
  * `velocity(t)` (if water exhaust speed is approximated)
  * Nozzle model for exhaust velocity

#### **5. Kinetic & Potential Energy of Expelled Air**

* Same principle as with water:

  $$
  E_{\text{air-out}}(t) = \int_0^t \left( \frac{1}{2} \dot{m}_{\text{air}}(t') v_{\text{ex}}(t')^2 + \dot{m}_{\text{air}}(t') g h(t') \right) dt'
  $$

#### **6. Energy Losses**

* **Drag**:

  $$
  E_{\text{drag}} = \int_0^t D(t') \cdot v(t') \, dt'
  $$

  Where `D(t')` is `drag(t')`

* **Friction in Nozzle** (if modeled separately)

  * Can be represented as a percentage loss in thrust or internal pressure drop.

---

### **Mapping to `FlightData`**

Use the following from the `FlightData` object:

| Quantity                              | Related Energy                                                        |
| ------------------------------------- | --------------------------------------------------------------------- |
| `pressure`, `temperature`, `air_mass` | Internal energy / enthalpy of air                                     |
| `altitude`, `velocity`                | Kinetic and potential of rocket and water                             |
| `water_mass`                          | Time evolution of remaining water (to compute expelled water)         |
| `air_mass`                            | Time evolution of air loss                                            |
| `drag`                                | Work done against drag                                                |
| `thrust`                              | Related to momentum flux (especially for estimating exhaust velocity) |

---

### Summary

You can express total energy flow as:

$$
\boxed{
E_{\text{air-in}}(0) = E_{\text{rocket}}(t) + E_{\text{water-in}}(t) + E_{\text{water-out}}(t) + E_{\text{air-out}}(t) + E_{\text{drag}} + E_{\text{friction}} + \text{(losses)}
}
$$

Where each term represents the energy in various parts of the system at time $t$. The water/air "as it left the rocket" terms **do** represent the integral over the energy that exits the system — i.e., the total **carried-away energy**.
