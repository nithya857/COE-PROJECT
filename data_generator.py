import os
import pandas as pd
import numpy as np

def generate_datasets():
    os.makedirs('data', exist_ok=True)

    # 1. Components Data (10 components)
    components = [
        {"component_id": "C001", "component_name": "Motor Bearing", "pack_size": 50, "unit_cost": 120, "emission_factor": 0.5, "criticality": "HIGH"},
        {"component_id": "C002", "component_name": "Hydraulic Cylinder", "pack_size": 25, "unit_cost": 450, "emission_factor": 1.2, "criticality": "HIGH"},
        {"component_id": "C003", "component_name": "Stepper Motor", "pack_size": 50, "unit_cost": 200, "emission_factor": 0.8, "criticality": "MEDIUM"},
        {"component_id": "C004", "component_name": "Control Valve", "pack_size": 100, "unit_cost": 85, "emission_factor": 0.3, "criticality": "LOW"},
        {"component_id": "C005", "component_name": "Circuit Board", "pack_size": 100, "unit_cost": 310, "emission_factor": 0.4, "criticality": "CRITICAL"},
        {"component_id": "C006", "component_name": "Cooling Fan", "pack_size": 200, "unit_cost": 45, "emission_factor": 0.2, "criticality": "LOW"},
        {"component_id": "C007", "component_name": "Pressure Sensor", "pack_size": 25, "unit_cost": 160, "emission_factor": 0.3, "criticality": "CRITICAL"},
        {"component_id": "C008", "component_name": "Power Inverter", "pack_size": 50, "unit_cost": 520, "emission_factor": 1.5, "criticality": "HIGH"},
        {"component_id": "C009", "component_name": "Cable Assembly", "pack_size": 200, "unit_cost": 30, "emission_factor": 0.1, "criticality": "LOW"},
        {"component_id": "C010", "component_name": "Gearbox Seal", "pack_size": 100, "unit_cost": 75, "emission_factor": 0.2, "criticality": "MEDIUM"}
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

    # 3. Transfers Data (Pairwise inter-location transport details)
    # 5 locations -> 20 directed pairs
    loc_names = [l["location_name"] for l in locations]
    transfers = []
    
    # Distance matrix mapping approximate lead times (days) and cost per unit
    # Chennai (L001), Bangalore (L002), Coimbatore (L003), Hyderabad (L004), Pune (L005)
    lead_times = {
        ("Chennai", "Bangalore"): (1, 8.5, 0.95),
        ("Chennai", "Coimbatore"): (1, 7.0, 0.92),
        ("Chennai", "Hyderabad"): (2, 12.0, 0.90),
        ("Chennai", "Pune"): (4, 18.0, 0.88),
        ("Bangalore", "Chennai"): (1, 8.5, 0.95),
        ("Bangalore", "Coimbatore"): (1, 6.0, 0.94),
        ("Bangalore", "Hyderabad"): (2, 10.0, 0.92),
        ("Bangalore", "Pune"): (3, 15.0, 0.89),
        ("Coimbatore", "Chennai"): (1, 7.0, 0.92),
        ("Coimbatore", "Bangalore"): (1, 6.0, 0.94),
        ("Coimbatore", "Hyderabad"): (3, 14.0, 0.88),
        ("Coimbatore", "Pune"): (4, 19.0, 0.85),
        ("Hyderabad", "Chennai"): (2, 12.0, 0.90),
        ("Hyderabad", "Bangalore"): (2, 10.0, 0.92),
        ("Hyderabad", "Coimbatore"): (3, 14.0, 0.88),
        ("Hyderabad", "Pune"): (2, 11.0, 0.91),
        ("Pune", "Chennai"): (4, 18.0, 0.88),
        ("Pune", "Bangalore"): (3, 15.0, 0.89),
        ("Pune", "Coimbatore"): (4, 19.0, 0.85),
        ("Pune", "Hyderabad"): (2, 11.0, 0.91),
    }

    for (src, dst), (days, cost, rel) in lead_times.items():
        transfers.append({
            "source": src,
            "destination": dst,
            "transfer_time_days": days,
            "transfer_cost_per_unit": cost,
            "reliability": rel
        })
    df_transfers = pd.DataFrame(transfers)
    df_transfers.to_csv('data/transfers.csv', index=False)

    # 4. Inventory and Forecast Datasets (100+ records each)
    # We will generate 2 records per component per location (Batch 1 & Batch 2 / Warehouse zones) to hit 100+ records
    np.random.seed(42)
    
    inventory_records = []
    forecast_records = []

    urgencies = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    for comp in components:
        comp_id = comp["component_id"]
        pack_sz = comp["pack_size"]
        
        for loc in loc_names:
            # Deterministic scenario crafting for key edge cases & realistic network behavior
            for batch_id in [1, 2]:
                tag = f"B{batch_id}"
                
                # Base inventory figures
                curr = np.random.randint(50, 400)
                safe = np.random.randint(30, 100)
                res = np.random.randint(0, 30)
                f_7 = np.random.randint(40, 350)
                unc = np.random.choice([5.0, 10.0, 15.0, 20.0, 25.0])
                urg = np.random.choice(urgencies)

                # Explicit Edge Case Injection:
                # -------------------------------------------------------------
                # Edge Case 1: No surplus anywhere for C005 (Circuit Board) in Batch 1
                if comp_id == "C005" and batch_id == 1:
                    curr = 40
                    safe = 50
                    res = 10
                    f_7 = 120 # Heavy shortage at all locations, available stock < safety stock

                # Edge Case 2: Surplus exists, but transfer is too slow
                # C001 at Chennai Batch 1 has CRITICAL urgency (max 1 day), surplus at Pune (lead time 4 days)
                elif comp_id == "C001" and loc == "Chennai" and batch_id == 1:
                    curr = 50
                    safe = 100
                    res = 10
                    f_7 = 200 # Shortage = 100 - (50 - 10 - 200) = 260
                    urg = "CRITICAL"
                elif comp_id == "C001" and loc == "Pune" and batch_id == 1:
                    curr = 500
                    safe = 50
                    res = 10
                    f_7 = 20 # High usable surplus = (500 - 10 - 50) = 440

                # Edge Case 3: Transfer would reduce source stock below safety stock
                # C003 at Bangalore Batch 1 has shortage, Coimbatore has small stock that would drop below safety stock
                elif comp_id == "C003" and loc == "Coimbatore" and batch_id == 1:
                    curr = 60
                    safe = 40
                    res = 0
                    f_7 = 10 # Usable surplus = 60 - 40 = 20 < pack_size (50)

                # Edge Case 4: Shortage does not match pack size
                # C001 at Bangalore Batch 1 has shortage = 120, Pack Size = 50. Recommended = 150 (3 packs)
                elif comp_id == "C001" and loc == "Bangalore" and batch_id == 1:
                    curr = 100
                    safe = 80
                    res = 10
                    f_7 = 190 # Projected stock = 100 - 10 - 190 = -100. Shortage = 80 - (-100) = 180 (not multiple of 50 -> 200)
                    urg = "HIGH"
                elif comp_id == "C001" and loc == "Hyderabad" and batch_id == 1:
                    curr = 600
                    safe = 50
                    res = 0
                    f_7 = 50 # Usable surplus = 550

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

    # 5. Empty Override Log with header
    df_override = pd.DataFrame(columns=["recommendation_id", "decision", "reason", "timestamp"])
    df_override.to_csv('data/override_log.csv', index=False)

    print(f"Generated Datasets successfully:")
    print(f" - Components: {len(df_components)} rows")
    print(f" - Locations: {len(df_locations)} rows")
    print(f" - Transfers: {len(df_transfers)} rows")
    print(f" - Inventory Records: {len(df_inv)} rows")
    print(f" - Forecast Records: {len(df_fc)} rows")

if __name__ == '__main__':
    generate_datasets()
