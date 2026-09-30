# Architecture Specification: System Data Flow (Review 2 Release)

```
+-------------------------------------------------------------+
|               SQLITE RELATIONAL DATABASE                    |
|                   data/inventory.db                         |
|  Components | Locations | Inventory | Forecasts             |
|  TransferRoutes | OverrideLogs | ValidationCases            |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     SQLALCHEMY 2.0 ORM                      |
|  - Object Relational Mapping & Thread-Safe Scoped Session   |
|  - ACID Transactional Stock Allocation (database.py)        |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                    DATA VALIDATION MODULE                   |
|  - Validates missing values, negative stock, pack size      |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     INVENTORY PROCESSING                    |
|  - Available Stock = Current - Reserved                     |
|  - Projected Stock = Available - Forecast 7-Days            |
+-------------------------------------------------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
+-----------------------------+ +-----------------------------+
|     SHORTAGE DETECTION      | |      SURPLUS DETECTION      |
| max(0, Safety - Projected)  | | max(0, Available - Safety)  |
+-----------------------------+ +-----------------------------+
               |                               |
               +---------------+---------------+
                               |
                               v
+-------------------------------------------------------------+
|              VARIABLE PACK-SIZE & FEASIBILITY               |
|  - Whole Pack Quantization (Q = ceil(S/P)*P)                |
|  - Source Safety Stock Protection Guard                     |
|  - Service Urgency Lead-Time & SLA Check                    |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|            DYNAMIC CARBON EMISSIONS & SCORING               |
|  - CO2 (kg) = Distance * Weight (Tons) * Vehicle Emission   |
|  - Vehicle Modes: EV_TRUCK, DIESEL_TRUCK, EXPRESS_AIR       |
|  - Score = 0.4*Service + 0.3*Cost + 0.15*CO2 + 0.15*Rel     |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                UNCERTAINTY & HUMAN APPROVAL                 |
|  - Forecast Uncertainty Interval calculation                 |
|  - Transactional Approval Action (SQLite Stock Allocation)  |
+-------------------------------------------------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
+-----------------------------+ +-----------------------------+
|       FLASK REST API        | |     INTERACTIVE DASHBOARD   |
|  /api/dashboard             | |  7 Metric Summary Cards     |
|  /api/recommendations       | |  3 Chart.js Visualizations  |
|  /api/recommendation/approve| |  Shortage & Rec Tables      |
|  /api/recommendation/override | |  ACID Stock Reallocation   |
+-----------------------------+ +-----------------------------+
                               |
                               v
+-------------------------------------------------------------+
|            HYPOTHESIS PROPERTY-BASED TESTING                |
|  - Whole-Pack Quantization Invariants (Q >= S, Q % P == 0)  |
|  - Safety Stock Preservation Invariant                      |
|  - 10^6 Extreme Demand Surge Resilience                     |
+-------------------------------------------------------------+
```
