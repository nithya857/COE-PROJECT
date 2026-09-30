# Comprehensive Testing Strategy & Error Boundaries Architecture

---

## 1. Automated Test Taxonomy

The **Multi-Location Balancing Recommender** utilizes a three-tiered automated testing architecture to ensure high software reliability, mathematical correctness, and fault tolerance:

```text
+-----------------------------------------------------------------------+
|                    AUTOMATED TESTING ARCHITECTURE                     |
+-----------------------------------------------------------------------+
| 1. Pytest Unit Test Suite (tests/test_recommender.py)                 |
|    - Evaluates core formulas: Shortage, Usable Surplus, SLA Lead Time |
|    - Validates Edge Cases 1-4 deterministic outputs                   |
+-----------------------------------------------------------------------+
| 2. Hypothesis Property-Based Suite (tests/test_property_based.py)     |
|    - Validates invariants across random inputs (1 to 10^6 units)      |
|    - Verifies whole-pack quantization & 5M demand spike stability     |
+-----------------------------------------------------------------------+
| 3. Error Boundaries Test Suite (tests/test_error_boundaries.py)       |
|    - Tests input data quality validation guards                       |
|    - Verifies SQLite ACID transaction rollback on invariant breach    |
|    - Validates fallback behavior under missing routes or empty datasets|
+-----------------------------------------------------------------------+
```

---

## 2. Test Suite Breakdown & Command Execution

### Tier 1: Unit Test Suite (`tests/test_recommender.py`)
Verifies individual formula logic and deterministic business rules:
- `test_shortage_calculation`: Verifies $\text{projected\_stock} = \text{available} - \text{forecast}$ and $\text{shortage} = \max(0, \text{safety} - \text{projected})$.
- `test_surplus_calculation`: Verifies $\text{usable\_surplus} = \max(0, \text{available} - \text{safety})$.
- `test_pack_size_handling`: Verifies whole pack rounding ($Q = \lceil S / P \rceil \times P$).
- `test_safety_stock_protection`: Verifies candidate source rejection when transfer would breach source safety stock.
- `test_transfer_time_rejection`: Verifies candidate source rejection when transfer lead time exceeds SLA urgency deadline.
- `test_no_surplus_purchase_recommendation`: Verifies fallback to direct supplier procurement when zero network surplus exists.

**Run Command**:
```bash
python -m pytest tests/test_recommender.py -v
```

---

### Tier 2: Hypothesis Property-Based Invariant Suite (`tests/test_property_based.py`)
Uses the `Hypothesis` property-based testing framework (`@given(st.integers(...))`) to test invariants across $10^6$ randomized inputs:
- `test_unbounded_pack_size_rounding_properties`: Asserts $Q \ge S$, $Q \pmod P = 0$, $Q - S < P$, and $N = Q / P$.
- `test_surplus_bounded_transfer_properties`: Asserts $Q \le U$, $Q \pmod P = 0$, and $Q = 0$ if $U < P$.
- `test_extreme_demand_surge_resilience`: Asserts system stability under $5,000,000$-unit demand surges without raising unhandled exceptions.

**Run Command**:
```bash
python -m pytest tests/test_property_based.py -v
```

---

### Tier 3: Error Boundaries Test Suite (`tests/test_error_boundaries.py`)
Tests fault tolerance, input validation guards, database rollbacks, and disconnected graph route fallbacks:
- `test_invalid_negative_stock_validation`: Verifies `validate_data()` returns error warnings for negative current/safety stock.
- `test_zero_or_negative_pack_size_error_guard`: Verifies `validate_data()` returns error warnings for non-positive pack sizes ($\le 0$).
- `test_missing_transfer_route_fallback`: Verifies rejection of candidate sources when no logistics route exists between location pairs.
- `test_database_transaction_rollback`: Verifies `execute_transfer_transaction()` rolls back changes cleanly in SQLite when safety stock is threatened.
- `test_corrupt_or_empty_dataset_graceful_handling`: Verifies `generate_recommendations()` handles zero-shortage or empty inventory data gracefully.

**Run Command**:
```bash
python -m pytest tests/test_error_boundaries.py -v
```

---

## 3. System Error Boundaries & Fault Tolerance Mechanisms

```text
+------------------------+------------------------------------+---------------------------------------+
| ERROR BOUNDARY LAYER   | FAULT CONDITION TRIGGERED          | GRACEFUL SYSTEM DEFENSE MECHANISM     |
+------------------------+------------------------------------+---------------------------------------+
| Data Quality Boundary  | Negative stock / non-positive pack  | validate_data() emits quality warnings|
|                        | size in input records.             | without crashing web application.     |
+------------------------+------------------------------------+---------------------------------------+
| ACID Transaction Guard | User approves transfer that would  | SQLite transaction rolls back state   |
|                        | breach source safety stock.        | atomically and returns error message. |
+------------------------+------------------------------------+---------------------------------------+
| Routing Graph Boundary | No active transport route configured| Rejection recorded ("No active route")|
|                        | between source and destination.   | and falls back to supplier purchase.  |
+------------------------+------------------------------------+---------------------------------------+
| Pack-Size Rounding     | Shortage quantity does not align   | Quantization algorithm rounds up to   |
| Boundary               | with component pack size.          | complete pack integer multiples.      |
+------------------------+------------------------------------+---------------------------------------+
| Demand Spike Boundary  | Sudden 100x demand spike           | Quantized transfer capped at surplus; |
|                        | exceeding network surplus.         | unfulfilled shortage bought from vendor|
+------------------------+------------------------------------+---------------------------------------+
```

---

## 4. Full Test Suite Execution

Run all test tiers sequentially:
```bash
python -m pytest tests/test_recommender.py tests/test_property_based.py tests/test_error_boundaries.py -v
```
