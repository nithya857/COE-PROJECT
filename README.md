# Multi-Location Balancing Recommender for a Manufacturer Managing Components Supplied in Variable Pack Sizes

> **CoE Growth Project - Review 3 Production Release**

---

## 📌 Problem Statement
Manufacturing networks operating multiple plants or regional warehouses frequently experience localized inventory imbalances. A plant may face an imminent stockout due to short-term demand surges while a nearby plant holds excess usable surplus stock above its safety stock threshold. Traditional supply chain systems automatically trigger high-cost external supplier purchases for every shortage, ignoring internal network balance and ignoring the constraint that industrial components are shipped in fixed, variable pack sizes (e.g. 25, 50, 100, 200 units).

---

## 🚀 Key Technical Enhancements (Review 1 -> Review 3)
1. **Relational Schema & Transactional Integrity (SQLite + SQLAlchemy 2.0 ORM)**: Storage migrated from flat CSV files to an embedded SQLite database (`data/inventory.db`) with thread-safe scoped sessions and ACID transactional stock allocation (`execute_transfer_transaction`) preventing concurrent allocation race conditions.
2. **Dynamic Distance- & Transport-Weighted Carbon Footprint Model**: Transport modeling expanded with route distance (km), vehicle mode (`EV_TRUCK`, `DIESEL_TRUCK`, `EXPRESS_AIR`), and component weight (kg) calculations ($\text{CO}_2 \text{ kg} = \text{distance} \times \text{weight} \times \text{emission rate}$). Integrated sustainability into decision scoring ($0.4\times\text{Service} + 0.3\times\text{Cost} + 0.15\times\text{Emissions} + 0.15\times\text{Reliability}$).
3. **Property-Based Automated Testing Suite (`Hypothesis`)**: Added property-based invariant testing (`tests/test_property_based.py`) testing whole-pack quantization, safety stock preservation, and extreme demand surge resilience ($5\times 10^6$ units) under randomized input distributions.
4. **Error Boundaries & Granular Testing Suite**: Added dedicated error boundary tests (`tests/test_error_boundaries.py`) and granular technical documentation (`docs/testing_and_error_boundaries.md`).

---

## 🗄️ RELATIONAL DATABASE SCHEMA & DATA DICTIONARY

Database Engine: **SQLite3** via **SQLAlchemy 2.0 ORM** (`data/inventory.db`).

### 1. `components` Table
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `component_id` | `VARCHAR(50)` | Primary Key | Unique component code (e.g. C001) |
| `component_name` | `VARCHAR(100)` | NOT NULL | Descriptive component name |
| `pack_size` | `INTEGER` | NOT NULL (> 0) | Fixed integer pack size (25, 50, 100, 200) |
| `unit_cost` | `FLOAT` | NOT NULL (> 0) | Procurement unit cost in INR (₹) |
| `unit_weight_kg` | `FLOAT` | NOT NULL (> 0) | Weight per unit in kilograms |
| `criticality` | `VARCHAR(20)` | NOT NULL | Criticality rating (CRITICAL, HIGH, MEDIUM, LOW) |

### 2. `locations` Table
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `location_id` | `VARCHAR(50)` | Primary Key | Unique location code (e.g. L001) |
| `location_name` | `VARCHAR(100)` | UNIQUE, NOT NULL | Facility location name (Chennai, Bangalore, Pune) |

### 3. `inventory` Table
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key Auto-Inc | Unique row ID |
| `component_id` | `VARCHAR(50)` | Foreign Key -> components | Associated component ID |
| `location` | `VARCHAR(100)` | NOT NULL | Warehouse location name |
| `batch` | `VARCHAR(20)` | NOT NULL | Production batch code (B1, B2) |
| `current_stock` | `INTEGER` | NOT NULL (>= 0) | Warehouse physical current stock |
| `safety_stock` | `INTEGER` | NOT NULL (>= 0) | Minimum mandatory safety stock threshold |
| `reserved_stock` | `INTEGER` | NOT NULL (>= 0) | Stock reserved for active production |

### 4. `forecasts` Table
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key Auto-Inc | Unique row ID |
| `component_id` | `VARCHAR(50)` | Foreign Key -> components | Associated component ID |
| `location` | `VARCHAR(100)` | NOT NULL | Target location name |
| `batch` | `VARCHAR(20)` | NOT NULL | Production batch code |
| `forecast_7_days` | `FLOAT` | NOT NULL (>= 0) | 7-day predicted consumption demand |
| `uncertainty_percent` | `FLOAT` | NOT NULL | Forecast error percentage (+/- %) |
| `urgency` | `VARCHAR(20)` | NOT NULL | SLA Urgency rating (CRITICAL, HIGH, MEDIUM, LOW) |

### 5. `transfer_routes` Table
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key Auto-Inc | Unique route ID |
| `source` | `VARCHAR(100)` | NOT NULL | Origin location name |
| `destination` | `VARCHAR(100)` | NOT NULL | Target location name |
| `distance_km` | `FLOAT` | NOT NULL (> 0) | Transport distance in kilometers |
| `transfer_time_days`| `INTEGER` | NOT NULL (> 0) | Transport lead time in days |
| `transfer_cost_per_unit`| `FLOAT` | NOT NULL (>= 0) | Freight cost per unit in INR (₹) |
| `transport_mode` | `VARCHAR(50)` | NOT NULL | Vehicle mode (EV_TRUCK, DIESEL_TRUCK, EXPRESS_AIR) |
| `vehicle_emission_rate`| `FLOAT` | NOT NULL | Emission factor (kg CO2 / ton-km) |
| `reliability` | `FLOAT` | NOT NULL (0.0 to 1.0) | Route reliability rating |

### 6. `override_log` Table
| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key Auto-Inc | Unique log ID |
| `recommendation_id`| `VARCHAR(50)` | NOT NULL | Target recommendation code (REC-001) |
| `decision` | `VARCHAR(20)` | NOT NULL | Action status (APPROVED, REJECTED, OVERRIDE) |
| `reason` | `TEXT` | NOT NULL | Operational justification reason |
| `timestamp` | `DATETIME` | DEFAULT NOW | Timestamp of action execution |

---

## 🌐 FLASK REST API ENDPOINT CONTRACTS

### 1. `GET /`
- **Description**: Renders main interactive glassmorphism dashboard UI.
- **Response**: `200 OK` HTML text.

### 2. `GET /recommendations`
- **Description**: Renders full recommendation center list UI.
- **Response**: `200 OK` HTML text.

### 3. `GET /recommendation/<rec_id>`
- **Description**: Renders single recommendation detailed view UI.
- **URL Parameter**: `rec_id` (string, e.g. `REC-001`).
- **Response**: `200 OK` HTML text.

### 4. `GET /api/dashboard`
- **Description**: Returns canonical validation summary metrics, data quality warnings, and shortage monitor records.
- **Response**: `200 OK` JSON Payload:
```json
{
  "summary": {
    "total_components": 10,
    "total_locations": 5,
    "active_shortages": 72,
    "transfer_recommendations": 53,
    "purchase_recommendations": 19,
    "total_units_transferred": 6800,
    "baseline_purchase": 1968000.0,
    "recommender_purchase": 812750.0,
    "recommender_transfer": 58962.5,
    "recommender_total_cost": 871712.5,
    "purchase_avoided": 1155250.0,
    "net_financial_savings": 1096287.5,
    "shortages_avoided": 53,
    "baseline_emissions_kg": 3658.32,
    "recommender_emissions_kg": 2285.95,
    "emissions_avoided_kg": 1372.37
  },
  "warnings": [],
  "shortages": [...]
}
```

### 5. `GET /api/recommendations`
- **Description**: Returns complete list of inter-location transfer and procurement recommendations.
- **Response**: `200 OK` JSON Array.

### 6. `GET /api/recommendation/<rec_id>`
- **Description**: Returns detailed breakdown for a single recommendation.
- **Response**: `200 OK` JSON Object / `404 Not Found`.

### 7. `POST /api/recommendation/<rec_id>/approve`
- **Description**: Executes transactional ACID stock reallocation in SQLite database for inter-location transfers.
- **Response**: `200 OK` JSON:
```json
{
  "status": "success",
  "message": "Recommendation REC-001 approved. Successfully executed transaction: Transferred 100 units from Coimbatore to Chennai."
}
```

### 8. `POST /api/recommendation/<rec_id>/override`
- **Description**: Logs planner manual override decision and justification reason text.
- **Request Body**: `{"reason": "Local store emergency buffer available"}`
- **Response**: `200 OK` JSON payload with logged record.

---

## 🧪 TESTING & ERROR BOUNDARIES

```bash
# 1. Run Unit Tests
python -m pytest tests/test_recommender.py -v

# 2. Run Hypothesis Property-Based Invariant Tests
python -m pytest tests/test_property_based.py -v

# 3. Run Error Boundaries Tests
python -m pytest tests/test_error_boundaries.py -v
```

See [docs/testing_and_error_boundaries.md](file:///d:/COE%20PROJECT/docs/testing_and_error_boundaries.md) for full taxonomy details.

---

## 🚀 How to Run the Project

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Generate Datasets & Seed SQLite DB
python data_generator.py

# 3. Run Validation Experiment
python metrics.py

# 4. Start Flask Application
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000/`
