# Multi-Location Balancing Recommender for a Manufacturer Managing Components Supplied in Variable Pack Sizes

> **CoE Growth Project - 45% Review 1 Prototype**

---

## 📌 Problem Statement
Manufacturing networks operating multiple plants or regional warehouses frequently experience localized inventory imbalances. A plant may face an imminent stockout due to short-term demand surges while a nearby plant holds excess usable surplus stock above its safety stock threshold. Traditional supply chain systems automatically trigger high-cost external supplier purchases for every shortage, ignoring internal network balance and ignoring the constraint that industrial components are shipped in fixed, variable pack sizes (e.g. 25, 50, 100, 200 units).

---

## 🎯 Project Objective
To develop a simple, explainable, rule-based decision-support system that:
1. Detects localized component shortages across manufacturing facilities.
2. Identifies facilities with usable surplus stock above safety thresholds.
3. Enforces integer variable pack-size transfer constraints.
4. Evaluates inter-location transport lead times against service urgency deadlines.
5. Quantifies baseline vs recommender cost savings, purchase avoidance, and shortage resolution metrics.
6. Provides an interactive web dashboard with human approval and override audit logging.

---

## ⚡ 45% Prototype Features (Review 1 Scope)
- **Dataset Generator**: Reproducible synthetic dataset generator (`data_generator.py`) for 10 components and 5 locations.
- **Data Validation Engine**: Checks for missing values, negative inventory, invalid pack sizes, and missing routes.
- **Shortage & Surplus Calculation**: Formulates available stock, projected stock, shortage quantity, and usable surplus.
- **Variable Pack-Size Handling**: Adjusts shortage quantities to complete pack integer multiples ($Q = \lceil S / P \rceil \times P$).
- **Transfer Feasibility Engine**: Evaluates source surplus, safety stock preservation, and service urgency lead-time rules.
- **Explainable Decision-Support Score**: Ranks candidate sources using $0.5 \times \text{service} + 0.3 \times \text{cost} + 0.2 \times \text{reliability}$.
- **Uncertainty & Confidence Communicator**: Displays forecast uncertainty intervals and assigns HIGH/MEDIUM/LOW confidence ratings.
- **Baseline Comparison & Metrics**: Computes purchase cost avoided and shortages avoided against the purchase-all baseline.
- **Four Core Edge Cases**: Demonstrates Edge Cases 1-4 with explicit status messages and rejection evidence.
- **Human Approval & Override Audit Log**: Enables planners to approve, reject, or override recommendations with mandatory reason logging saved to `data/override_log.csv`.
- **Interactive Flask Dashboard**: Modern, glassmorphism dashboard with 3 primary Chart.js visualizations.
- **Automated Pytest Suite**: Full automated testing in `tests/test_recommender.py`.

---

## 🛠️ Technology Stack
- **Backend**: Python 3, Flask
- **Data Processing**: Pandas, NumPy, CSV
- **Frontend**: HTML5, CSS3 (Vanilla CSS with CSS Variables & Glassmorphism), JavaScript (ES6)
- **Visualizations**: Chart.js (via CDN)
- **Testing**: Pytest

---

## 📁 Project Structure
```
inventory-balancing-recommender/
├── app.py
├── recommender.py
├── data_generator.py
├── metrics.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── components.csv
│   ├── locations.csv
│   ├── inventory.csv
│   ├── forecast.csv
│   ├── transfers.csv
│   ├── validation_cases.csv
│   └── override_log.csv
│
├── templates/
│   ├── index.html
│   ├── recommendations.html
│   └── details.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── tests/
│   └── test_recommender.py
│
└── docs/
    ├── requirements.md
    ├── algorithm.md
    ├── architecture.md
    ├── validation.md
    ├── limitations.md
    └── demo_script.md
```

---

## 🧮 Algorithm & Formulas

### 1. Shortage & Surplus Detection
$$\text{Available Stock} = \text{Current Stock} - \text{Reserved Stock}$$
$$\text{Projected Stock} = \text{Available Stock} - \text{Forecast}_{7\text{d}}$$
$$\text{Shortage} = \max(0, \text{Safety Stock} - \text{Projected Stock})$$
$$\text{Usable Surplus} = \max(0, \text{Available Stock} - \text{Safety Stock})$$

### 2. Variable Pack-Size Adjustment
$$\text{Packs Required } N = \left\lceil \frac{\text{Shortage}}{\text{Pack Size}} \right\rceil$$
$$\text{Recommended Quantity } Q = N \times \text{Pack Size}$$

### 3. Decision-Support Score
$$\text{Score} = 0.5 \times \left(1.0 - \frac{\text{Lead Time}}{\text{Max Urgency Days}}\right) + 0.3 \times \left(1.0 - \frac{\text{Transfer Cost Unit}}{\text{Unit Cost}}\right) + 0.2 \times \text{Reliability}$$

---

## 📊 Baseline Comparison
- **Baseline Strategy**: If shortage exists $\rightarrow$ Purchase full shortage from external supplier.
- **Recommender Strategy**: Transfer internal surplus first $\rightarrow$ Direct supplier purchase only if internal surplus is unavailable.
- **Key Metrics Tracked**:
  - Baseline Purchase Cost
  - Recommender Purchase Cost
  - Recommender Transfer Cost
  - Purchase Avoided ($= \text{Baseline Purchase} - \text{Recommender Purchase}$)
  - Shortages Avoided ($= \text{Shortages resolved via transfer}$)

---

## 🚀 How to Run the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Dataset
```bash
python data_generator.py
```

### 3. Run Automated Tests
```bash
pytest tests/test_recommender.py
```

### 4. Execute Validation Experiment
```bash
python metrics.py
```

### 5. Start Flask Web Server
```bash
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000/`

---

## 🧪 Testing & Edge Cases
The test suite in `tests/test_recommender.py` verifies:
1. Shortage calculation correctness.
2. Surplus calculation correctness.
3. Variable pack-size rounding logic.
4. Safety stock protection at source locations.
5. Transfer lead-time rejection against service urgency deadlines.
6. No-surplus supplier purchase fallback.

---

## 📝 Limitations (Review 1 Scope Boundary)
- Uses python-generated synthetic supply chain datasets (`data_generator.py`).
- Persistent storage handled via Pandas CSV files without external database servers.
- Static transport matrices without live logistics API streaming.
- Rule-based decision-support recommendations rather than stochastic optimization models.

---

## 🔮 Future Work (Post-Review 1)
- **55%+**: Advanced demand forecasting (ARIMA / Prophet integration).
- **65%+**: Multi-echelon linear optimization (MILP solvers).
- **75%+**: Live streaming data pipelines & WebSockets.
- **85%+**: Enterprise ERP REST API connectors (SAP / NetSuite).
- **100%**: Production cloud deployment & OAuth2 security.
