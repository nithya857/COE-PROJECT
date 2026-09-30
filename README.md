# Multi-Location Balancing Recommender for a Manufacturer Managing Components Supplied in Variable Pack Sizes

> **CoE Growth Project - Review 2 Release Milestone**

---

## 📌 Problem Statement
Manufacturing networks operating multiple plants or regional warehouses frequently experience localized inventory imbalances. A plant may face an imminent stockout due to short-term demand surges while a nearby plant holds excess usable surplus stock above its safety stock threshold. Traditional supply chain systems automatically trigger high-cost external supplier purchases for every shortage, ignoring internal network balance and ignoring the constraint that industrial components are shipped in fixed, variable pack sizes (e.g. 25, 50, 100, 200 units).

---

## 🚀 Key Review 2 Engineering Enhancements
1. **Relational Schema & Transactional Integrity (SQLite + SQLAlchemy 2.0 ORM)**: Transitioned storage from flat CSV files to an embedded SQLite database (`data/inventory.db`) with thread-safe scoped sessions and ACID transactional stock allocation functions (`execute_transfer_transaction`) to prevent race conditions during human approval/override.
2. **Dynamic Distance- & Transport-Weighted Carbon Emissions Model**: Expanded carbon footprint modeling from static factors to dynamic route distance (km), vehicle mode (`EV_TRUCK`, `DIESEL_TRUCK`, `EXPRESS_AIR`), and component weight (kg) calculations ($\text{CO}_2 \text{ kg} = \text{distance} \times \text{weight} \times \text{emission rate}$). Integrated sustainability into decision scoring ($0.4\times\text{Service} + 0.3\times\text{Cost} + 0.15\times\text{Emissions} + 0.15\times\text{Reliability}$).
3. **Property-Based Automated Testing Suite (`Hypothesis`)**: Added property-based invariant testing (`tests/test_property_based.py`) testing whole-pack quantization, safety stock preservation, and extreme demand surge resilience ($10^6$ units) under randomized input distributions.

---

## ⚡ Review 2 Features & System Architecture
- **SQLite Database & SQLAlchemy ORM**: Relational schema models (`Component`, `Location`, `Inventory`, `Forecast`, `TransferRoute`, `OverrideLog`, `ValidationCase`).
- **Dataset Generator & Database Seeder**: Generates synthetic supply chain records and seeds SQLite database `data/inventory.db`.
- **Data Validation Engine**: Checks for missing values, negative inventory, invalid pack sizes, and missing routes.
- **Shortage & Surplus Calculation**: Formulates available stock, projected stock, shortage quantity, and usable surplus.
- **Variable Pack-Size Handling**: Adjusts shortage quantities to complete pack integer multiples ($Q = \lceil S / P \rceil \times P$).
- **Transfer Feasibility Engine**: Evaluates source surplus, safety stock preservation, and service urgency lead-time rules.
- **Multi-Criteria Decision Score**: Ranks candidate sources using $0.4\times\text{Service} + 0.3\times\text{Cost} + 0.15\times\text{Emissions} + 0.15\times\text{Reliability}$.
- **Uncertainty & Confidence Communicator**: Displays forecast uncertainty intervals and assigns HIGH/MEDIUM/LOW confidence ratings.
- **Baseline Comparison & Metrics**: Computes purchase cost avoided (₹ INR) and CO2 emissions avoided (kg) against the purchase-all baseline.
- **Four Core Edge Cases**: Demonstrates Edge Cases 1-4 with explicit status messages and rejection evidence.
- **ACID Transactional Stock Reallocation**: Approving a transfer recommendation atomically decrements source available stock and increments destination stock in SQLite.
- **Interactive Flask Dashboard**: Modern, glassmorphism dashboard with 7 summary metric cards and 3 primary Chart.js visualizations.
- **Automated Pytest & Hypothesis Test Suite**: Full coverage across unit tests and property-based invariant tests.

---

## 🛠️ Technology Stack
- **Backend**: Python 3, Flask, SQLAlchemy 2.0 ORM, SQLite3
- **Data Processing**: Pandas, NumPy
- **Frontend**: HTML5, CSS3 (Vanilla CSS with CSS Variables & Glassmorphism), JavaScript (ES6)
- **Visualizations**: Chart.js (via CDN)
- **Testing**: Pytest, Hypothesis (Property-Based Testing)

---

## 📁 Project Structure
```
inventory-balancing-recommender/
├── app.py
├── recommender.py
├── database.py
├── data_generator.py
├── metrics.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── inventory.db
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
│   ├── test_recommender.py
│   └── test_property_based.py
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

## 🚀 How to Run the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Datasets & Seed SQLite Database
```bash
python data_generator.py
```

### 3. Run Unit Tests & Property-Based Tests
```bash
python -m pytest tests/test_recommender.py -v
python -m pytest tests/test_property_based.py -v
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
