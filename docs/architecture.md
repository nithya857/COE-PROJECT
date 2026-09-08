# Architecture Specification: System Data Flow

```
+-------------------------------------------------------------+
|                      CSV DATA FILES                         |
|  components.csv | locations.csv | inventory.csv             |
|  forecast.csv   | transfers.csv                             |
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
|  - Whole Pack Rounding (Q = ceil(S/P)*P)                    |
|  - Source Safety Stock Protection                           |
|  - Service Urgency Lead-Time Check                          |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 RECOMMENDATION & SCORING                    |
|  - Rule 1: No Surplus -> Direct Supplier Purchase           |
|  - Rule 2: Feasible Surplus -> Inter-Location Transfer      |
|  - Score = 0.5*Service + 0.3*Cost + 0.2*Reliability          |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                UNCERTAINTY & HUMAN APPROVAL                 |
|  - Forecast Uncertainty Interval calculation                 |
|  - High Criticality / Qty > 200 / Low Conf Flagging        |
+-------------------------------------------------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
+-----------------------------+ +-----------------------------+
|       FLASK REST API        | |     INTERACTIVE DASHBOARD   |
|  /api/dashboard             | |  Summary Metrics Cards      |
|  /api/recommendations       | |  3 Chart.js Visualizations  |
|  /api/recommendation/approve| |  Shortage & Rec Tables      |
|  /api/recommendation/override | |  Override Reason Modal     |
+-----------------------------+ +-----------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     VALIDATION & METRICS                    |
|  - Baseline Purchase vs Recommender Cost Comparison         |
|  - Purchase Avoided & Shortages Avoided calculations        |
|  - Output: data/validation_cases.csv                        |
+-------------------------------------------------------------+
```
