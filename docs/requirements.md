# Requirements Specification: Multi-Location Balancing Recommender

## 1. Problem Statement
Manufacturing supply chains managing component inventory across multiple manufacturing plants or regional distribution centers frequently encounter localized inventory imbalances. A single facility may experience an acute stockout threat for a critical component due to short-term demand spikes, while a neighboring facility maintains usable surplus above its safety stock threshold. 

Traditional procurement systems automatically place high-cost supplier purchases for every shortage, ignoring internal network balance and ignoring the constraint that components are shipped in fixed, variable pack sizes (e.g. 25, 50, 100, 200 units).

## 2. Project Objective
To develop a lightweight, rule-based, explainable decision-support prototype (45% Review 1 Boundary) that:
1. Detects localized component shortages across multi-location manufacturing networks.
2. Identifies locations with usable surplus inventory above mandatory safety stock.
3. Enforces integer variable pack-size transfer constraints.
4. Evaluates inter-location transport lead times against service urgency deadlines.
5. Quantifies baseline vs recommender cost savings, purchase avoidance, and shortage resolution metrics.
6. Provides an interactive web dashboard with human approval and override audit logging.

## 3. System Users
- **Supply Chain Planners / Analysts**: Review automated transfer and purchase recommendations, inspect explainable decision evidence, and approve/override actions.
- **Plant Operations Managers**: Monitor local stock health, forecast consumption, and shortage alerts.
- **Academic Evaluators / Viva Examiners**: Verify algorithmic logic, pack-size compliance, baseline metrics, and reproducible edge case behaviors.

## 4. Functional Requirements
- **FR-1 Inventory Processing**: Compute available stock (`current_stock - reserved_stock`), projected stock (`available_stock - forecast_7_days`), and shortage quantity (`max(0, safety_stock - projected_stock)`).
- **FR-2 Surplus Detection**: Compute usable surplus (`max(0, available_stock - safety_stock)`). Never allow stock transfers that violate source safety stock.
- **FR-3 Pack-Size Handling**: Convert required shortage quantities to integer multiples of the component's pack size ($Q = \lceil S / P \rceil \times P$). Bounded by source surplus if partial surplus is available.
- **FR-4 Service Urgency Feasibility**: Reject candidate sources whose transfer lead time exceeds the service urgency threshold (CRITICAL $\le 1$d, HIGH $\le 3$d, MEDIUM $\le 7$d, LOW $\le 14$d).
- **FR-5 Decision-Support Score**: Rank candidate sources using $0.5 \times \text{service\_score} + 0.3 \times \text{cost\_score} + 0.2 \times \text{reliability\_score}$.
- **FR-6 Uncertainty & Confidence**: Calculate forecast uncertainty ranges and assign HIGH/MEDIUM/LOW confidence ratings.
- **FR-7 Human Approval & Override**: Flag high criticality, large quantity ($>200$), or low confidence recommendations for human approval. Store override reasons in `override_log.csv`.
- **FR-8 Dashboard & Visualizations**: Provide responsive Flask dashboard with 3 primary Chart.js charts and active shortage/recommendation tables.

## 5. System Constraints
- Python 3 + Flask backend.
- Pandas + CSV files for persistent data storage.
- Vanilla HTML/CSS/JavaScript with Chart.js CDN for UI.
- No heavy ML libraries, external APIs, or database servers.
