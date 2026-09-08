# Algorithm Specification: Decision-Support Engine

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

## 4. Transfer Feasibility Rules

For a destination shortage $d$ and candidate source $s$:

1. **Surplus Rule**: Usable surplus $U_s \ge P$.
2. **Safety Stock Rule**: $(\text{Available Stock}_s - Q) \ge \text{Safety Stock}_s$.
3. **Service Urgency Rule**: $\text{Lead Time}_{s,d} \le \text{Max Urgency Days}(\text{Urgency}_d)$.
   - CRITICAL: $\le 1$ day
   - HIGH: $\le 3$ days
   - MEDIUM: $\le 7$ days
   - LOW: $\le 14$ days

## 5. Explainable Decision-Support Score

If multiple candidate sources satisfy all feasibility conditions, they are ranked using:

$$\text{Service Score} = \max\left(0, 1.0 - \frac{\text{Lead Time}_{s,d}}{\text{Max Urgency Days}}\right)$$

$$\text{Cost Score} = \max\left(0, 1.0 - \frac{\text{Transfer Cost Unit}_{s,d}}{\text{Unit Purchase Cost}_c}\right)$$

$$\text{Reliability Score} = \text{Reliability}_{s,d} \quad (0.0 \text{ to } 1.0)$$

$$\text{Score} = 0.5 \times \text{Service Score} + 0.3 \times \text{Cost Score} + 0.2 \times \text{Reliability Score}$$

The feasible candidate with the highest decision-support score is recommended for inter-location transfer. If zero feasible sources exist, the engine falls back to direct supplier purchase.
