# Algorithm Specification: Decision-Support Engine (Review 2 Release)

## 1. Inventory & Shortage Mathematical Formulation

For each component $c$ at location $l$ for operational horizon $t$:

$$\text{Available Stock} = \text{Current Stock}_{c,l} - \text{Reserved Stock}_{c,l}$$

$$\text{Projected Stock} = \text{Available Stock}_{c,l} - \text{Forecast}_{c,l,7\text{d}}$$

$$\text{Shortage}_{c,l} = \max(0, \text{Safety Stock}_{c,l} - \text{Projected Stock}_{c,l})$$

If $\text{Shortage}_{c,l} > 0$, the location is classified as **SHORTAGE**.

## 2. Usable Surplus Formulation

$$\text{Usable Surplus}_{c,l} = \max(0, \text{Available Stock}_{c,l} - \text{Safety Stock}_{c,l})$$

A candidate location $s$ can act as a source only if $\text{Usable Surplus}_{c,s} \ge \text{Pack Size}_c$.

## 3. Variable Pack-Size Adjustment Logic

Let $S$ be the required shortage and $P$ be the component pack size.

1. Unbounded Complete Pack Requirement:
   $$N_{\text{req}} = \left\lceil \frac{S}{P} \right\rceil, \quad Q_{\text{req}} = N_{\text{req}} \times P$$

2. If candidate source usable surplus $U \ge Q_{\text{req}}$:
   $$\text{Transfer Quantity } Q = Q_{\text{req}}, \quad \text{Packs } N = N_{\text{req}}$$

3. If $P \le U < Q_{\text{req}}$ (Source surplus covers partial packs):
   $$N_{\text{max}} = \left\lfloor \frac{U}{P} \right\rfloor, \quad Q = N_{\text{max}} \times P, \quad N = N_{\text{max}}$$

4. Partial pack transfers are strictly prohibited ($Q \bmod P = 0$).

## 4. Dynamic Distance & Vehicle-Weighted Carbon Emissions Model

For transport route $(s, d)$ carrying quantity $Q$ of component $c$ with unit weight $W_c$ (kg):

$$\text{Weight (Tons)} = \frac{Q \times W_c}{1000}$$

$$\text{Transfer Emissions (kg CO}_2\text{)} = \text{Distance}_{s,d} \times \text{Weight (Tons)} \times \text{Vehicle Rate}_m$$

Where vehicle emission rates $\text{Vehicle Rate}_m$ (kg CO2 / ton-km) are:
- `EV_TRUCK`: $0.05$ kg CO2 / ton-km
- `DIESEL_TRUCK`: $0.18$ kg CO2 / ton-km
- `EXPRESS_AIR`: $0.95$ kg CO2 / ton-km

Baseline Supplier Procurement Emissions are calculated assuming an 800 km supplier freight haul via `DIESEL_TRUCK`:

$$\text{Emissions Avoided (kg CO}_2\text{)} = \max(0, \text{Baseline Emissions} - \text{Transfer Emissions})$$

## 5. Multi-Criteria Explainable Decision-Support Score

If multiple candidate sources satisfy all feasibility conditions, they are ranked using:

$$\text{Service Score} = \max\left(0, 1.0 - \frac{\text{Lead Time}_{s,d}}{\text{Max Urgency Days}}\right)$$

$$\text{Cost Score} = \max\left(0, 1.0 - \frac{\text{Transfer Cost Unit}_{s,d}}{\text{Unit Purchase Cost}_c}\right)$$

$$\text{Emissions Score} = \max\left(0, 1.0 - \frac{\text{Transfer Emissions per Unit}}{\text{Baseline Emissions per Unit}}\right)$$

$$\text{Reliability Score} = \text{Reliability}_{s,d} \quad (0.0 \text{ to } 1.0)$$

$$\text{Score} = 0.40 \times \text{Service Score} + 0.30 \times \text{Cost Score} + 0.15 \times \text{Emissions Score} + 0.15 \times \text{Reliability Score}$$

The feasible candidate with the highest decision-support score is recommended for inter-location transfer.
