import os
import pandas as pd
import numpy as np
from database import (
    init_db, SessionLocal, Component, Location, Inventory, Forecast, TransferRoute, OverrideLog
)

def generate_datasets():
    os.makedirs('data', exist_ok=True)
    init_db()

    # 1. Components Data (10 components) with unit weight in kg
    components = [
        {"component_id": "C001", "component_name": "Motor Bearing", "pack_size": 50, "unit_cost": 120, "unit_weight_kg": 1.5, "emission_factor": 0.5, "criticality": "HIGH"},
        {"component_id": "C002", "component_name": "Hydraulic Cylinder", "pack_size": 25, "unit_cost": 450, "unit_weight_kg": 12.0, "emission_factor": 1.2, "criticality": "HIGH"},
        {"component_id": "C003", "component_name": "Stepper Motor", "pack_size": 50, "unit_cost": 200, "unit_weight_kg": 3.0, "emission_factor": 0.8, "criticality": "MEDIUM"},
        {"component_id": "C004", "component_name": "Control Valve", "pack_size": 100, "unit_cost": 85, "unit_weight_kg": 2.0, "emission_factor": 0.3, "criticality": "LOW"},
        {"component_id": "C005", "component_name": "Circuit Board", "pack_size": 100, "unit_cost": 310, "unit_weight_kg": 0.4, "emission_factor": 0.4, "criticality": "CRITICAL"},
        {"component_id": "C006", "component_name": "Cooling Fan", "pack_size": 200, "unit_cost": 45, "unit_weight_kg": 0.8, "emission_factor": 0.2, "criticality": "LOW"},
        {"component_id": "C007", "component_name": "Pressure Sensor", "pack_size": 25, "unit_cost": 160, "unit_weight_kg": 0.2, "emission_factor": 0.3, "criticality": "CRITICAL"},
        {"component_id": "C008", "component_name": "Power Inverter", "pack_size": 50, "unit_cost": 520, "unit_weight_kg": 8.5, "emission_factor": 1.5, "criticality": "HIGH"},
        {"component_id": "C009", "component_name": "Cable Assembly", "pack_size": 200, "unit_cost": 30, "unit_weight_kg": 1.0, "emission_factor": 0.1, "criticality": "LOW"},
        {"component_id": "C010", "component_name": "Gearbox Seal", "pack_size": 100, "unit_cost": 75, "unit_weight_kg": 0.5, "emission_factor": 0.2, "criticality": "MEDIUM"}
    ]
    df_components = pd.DataFrame(components)
    df_components.to_csv('data/components.csv', index=False)

    # 2. Locations Data (5 locations)
    locations = [
        {"location_id": "L001", "location_name": "Chennai"},
        {"location_id": "L002", "location_name": "Bangalore"},
        {"location_id": "L003", "location_name": "Coimbatore"},
        {"location_id": "L004", "location_name": "Hyderabad"},
        {"location_id": "L005", "location_name": "Pune"}
    ]
    df_locations = pd.DataFrame(locations)
    df_locations.to_csv('data/locations.csv', index=False)

    # 3. Transfers Data (Pairwise inter-location transport details with distance & vehicle modes)
    # (distance_km, lead_time_days, cost_per_unit, transport_mode, vehicle_emission_rate, reliability)
    # vehicle_emission_rate in kg CO2 / ton-km: EV_TRUCK=0.05, DIESEL_TRUCK=0.18, EXPRESS_AIR=0.95
    route_details = {
        ("Chennai", "Bangalore"): (350, 1, 8.5, "EV_TRUCK", 0.05, 0.95),
        ("Chennai", "Coimbatore"): (500, 1, 7.0, "DIESEL_TRUCK", 0.18, 0.92),
        ("Chennai", "Hyderabad"): (630, 2, 12.0, "DIESEL_TRUCK", 0.18, 0.90),
        ("Chennai", "Pune"): (1150, 4, 18.0, "EXPRESS_AIR", 0.95, 0.88),
        ("Bangalore", "Chennai"): (350, 1, 8.5, "EV_TRUCK", 0.05, 0.95),
        ("Bangalore", "Coimbatore"): (360, 1, 6.0, "EV_TRUCK", 0.05, 0.94),
        ("Bangalore", "Hyderabad"): (570, 2, 10.0, "DIESEL_TRUCK", 0.18, 0.92),
        ("Bangalore", "Pune"): (840, 3, 15.0, "DIESEL_TRUCK", 0.18, 0.89),
        ("Coimbatore", "Chennai"): (500, 1, 7.0, "DIESEL_TRUCK", 0.18, 0.92),
        ("Coimbatore", "Bangalore"): (360, 1, 6.0, "EV_TRUCK", 0.05, 0.94),
        ("Coimbatore", "Hyderabad"): (910, 3, 14.0, "DIESEL_TRUCK", 0.18, 0.88),
        ("Coimbatore", "Pune"): (1180, 4, 19.0, "EXPRESS_AIR", 0.95, 0.85),
        ("Hyderabad", "Chennai"): (630, 2, 12.0, "DIESEL_TRUCK", 0.18, 0.90),
        ("Hyderabad", "Bangalore"): (570, 2, 10.0, "DIESEL_TRUCK", 0.18, 0.92),
        ("Hyderabad", "Coimbatore"): (910, 3, 14.0, "DIESEL_TRUCK", 0.18, 0.88),
        ("Hyderabad", "Pune"): (560, 2, 11.0, "DIESEL_TRUCK", 0.18, 0.91),
        ("Pune", "Chennai"): (1150, 4, 18.0, "EXPRESS_AIR", 0.95, 0.88),
        ("Pune", "Bangalore"): (840, 3, 15.0, "DIESEL_TRUCK", 0.18, 0.89),
        ("Pune", "Coimbatore"): (1180, 4, 19.0, "EXPRESS_AIR", 0.95, 0.85),
        ("Pune", "Hyderabad"): (560, 2, 11.0, "DIESEL_TRUCK", 0.18, 0.91),
    }

    transfers = []
    for (src, dst), (dist, days, cost, mode, rate, rel) in route_details.items():
        transfers.append({
            "source": src,
            "destination": dst,
            "distance_km": dist,
            "transfer_time_days": days,
            "transfer_cost_per_unit": cost,
            "transport_mode": mode,
            "vehicle_emission_rate": rate,
            "reliability": rel
        })
    df_transfers = pd.DataFrame(transfers)
    df_transfers.to_csv('data/transfers.csv', index=False)

    # 4. Inventory and Forecast Datasets (100 records each)
    np.random.seed(42)
    loc_names = [l["location_name"] for l in locations]
    inventory_records = []
    forecast_records = []
    urgencies = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    for comp in components:
        comp_id = comp["component_id"]
        
        for loc in loc_names:
            for batch_id in [1, 2]:
                tag = f"B{batch_id}"
                
                curr = np.random.randint(50, 400)
                safe = np.random.randint(30, 100)
                res = np.random.randint(0, 30)
                f_7 = np.random.randint(40, 350)
                unc = np.random.choice([5.0, 10.0, 15.0, 20.0, 25.0])
                urg = np.random.choice(urgencies)

                # Edge Case Injections
                if comp_id == "C005" and batch_id == 1:
                    curr, safe, res, f_7 = 40, 50, 10, 120
                elif comp_id == "C001" and loc == "Chennai" and batch_id == 1:
                    curr, safe, res, f_7, urg = 50, 100, 10, 200, "CRITICAL"
                elif comp_id == "C001" and loc == "Pune" and batch_id == 1:
                    curr, safe, res, f_7 = 500, 50, 10, 20
                elif comp_id == "C003" and loc == "Coimbatore" and batch_id == 1:
                    curr, safe, res, f_7 = 60, 40, 0, 10
                elif comp_id == "C001" and loc == "Bangalore" and batch_id == 1:
                    curr, safe, res, f_7, urg = 100, 80, 10, 190, "HIGH"
                elif comp_id == "C001" and loc == "Hyderabad" and batch_id == 1:
                    curr, safe, res, f_7 = 600, 50, 0, 50

                inventory_records.append({
                    "component_id": comp_id,
                    "location": loc,
                    "batch": tag,
                    "current_stock": curr,
                    "safety_stock": safe,
                    "reserved_stock": res
                })

                forecast_records.append({
                    "component_id": comp_id,
                    "location": loc,
                    "batch": tag,
                    "forecast_7_days": f_7,
                    "uncertainty_percent": unc,
                    "urgency": urg
                })

    df_inv = pd.DataFrame(inventory_records)
    df_fc = pd.DataFrame(forecast_records)
    
    df_inv.to_csv('data/inventory.csv', index=False)
    df_fc.to_csv('data/forecast.csv', index=False)

    df_override = pd.DataFrame(columns=["recommendation_id", "decision", "reason", "timestamp"])
    df_override.to_csv('data/override_log.csv', index=False)

    # 5. Populate SQLite Database via SQLAlchemy ORM
    session = SessionLocal()
    try:
        # Clear existing tables
        session.query(Inventory).delete()
        session.query(Forecast).delete()
        session.query(TransferRoute).delete()
        session.query(Component).delete()
        session.query(Location).delete()
        session.query(OverrideLog).delete()
        session.commit()

        # Seed Components
        for c in components:
            session.add(Component(
                component_id=c['component_id'],
                component_name=c['component_name'],
                pack_size=c['pack_size'],
                unit_cost=c['unit_cost'],
                unit_weight_kg=c['unit_weight_kg'],
                criticality=c['criticality']
            ))

        # Seed Locations
        for l in locations:
            session.add(Location(
                location_id=l['location_id'],
                location_name=l['location_name']
            ))

        # Seed Transfer Routes
        for t in transfers:
            session.add(TransferRoute(
                source=t['source'],
                destination=t['destination'],
                distance_km=t['distance_km'],
                transfer_time_days=t['transfer_time_days'],
                transfer_cost_per_unit=t['transfer_cost_per_unit'],
                transport_mode=t['transport_mode'],
                vehicle_emission_rate=t['vehicle_emission_rate'],
                reliability=t['reliability']
            ))

        # Seed Inventory
        for r in inventory_records:
            session.add(Inventory(
                component_id=r['component_id'],
                location=r['location'],
                batch=r['batch'],
                current_stock=r['current_stock'],
                safety_stock=r['safety_stock'],
                reserved_stock=r['reserved_stock']
            ))

        # Seed Forecasts
        for f in forecast_records:
            session.add(Forecast(
                component_id=f['component_id'],
                location=f['location'],
                batch=f['batch'],
                forecast_7_days=f['forecast_7_days'],
                uncertainty_percent=f['uncertainty_percent'],
                urgency=f['urgency']
            ))

        session.commit()
        print("Successfully seeded SQLite Database data/inventory.db via SQLAlchemy ORM.")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

    print(f"Generated Datasets successfully:")
    print(f" - Components: {len(df_components)} rows")
    print(f" - Locations: {len(df_locations)} rows")
    print(f" - Transfers: {len(df_transfers)} rows")
    print(f" - Inventory Records: {len(df_inv)} rows")
    print(f" - Forecast Records: {len(df_fc)} rows")

if __name__ == '__main__':
    generate_datasets()
