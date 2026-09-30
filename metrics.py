import os
import pandas as pd
import numpy as np
from database import init_db, SessionLocal, ValidationCase
from recommender import (
    load_data_from_db,
    generate_recommendations,
    calculate_inventory_metrics
)

def run_validation_experiment():
    """
    Executes reproducible validation experiment comparing Baseline Strategy (Purchase All)
    against the Multi-Location Balancing Recommender.
    Evaluates both financial costs (INR) and dynamic carbon emissions (kg CO2).
    Generates data/validation_cases.csv and seeds SQLite ValidationCase table.
    """
    df_components, df_locations, df_inventory, df_forecast, df_transfers = load_data_from_db()

    recs = generate_recommendations(df_inventory, df_forecast, df_components, df_locations, df_transfers)
    
    validation_records = []
    
    total_shortage_cases = len(recs)
    transfer_recs_count = 0
    purchase_recs_count = 0
    
    total_baseline_purchase_cost = 0.0
    total_recommender_purchase_cost = 0.0
    total_recommender_transfer_cost = 0.0
    total_units_transferred = 0
    
    total_baseline_emissions_kg = 0.0
    total_recommender_emissions_kg = 0.0
    
    for r in recs:
        comp_id = r['component_id']
        dest = r['destination']
        shortage = r['required_quantity']
        rec_qty = r['recommended_quantity']
        unit_cost = r['purchase_cost'] / rec_qty if rec_qty > 0 else 0
        
        baseline_qty = rec_qty
        baseline_purchase_cost = baseline_qty * unit_cost
        
        # Baseline emissions (800 km procurement freight via DIESEL_TRUCK)
        baseline_emissions = float(r.get('baseline_emissions_kg', 0.0))
        recommender_emissions = float(r.get('transfer_emissions_kg', 0.0))
        
        if r['type'] == 'TRANSFER':
            transfer_recs_count += 1
            recommender_purchase_cost = 0.0
            recommender_transfer_cost = r['transfer_cost']
            total_units_transferred += rec_qty
        else:
            purchase_recs_count += 1
            recommender_purchase_cost = r['purchase_cost']
            recommender_transfer_cost = 0.0
            
        purchase_avoided = baseline_purchase_cost - recommender_purchase_cost
        net_savings = baseline_purchase_cost - (recommender_purchase_cost + recommender_transfer_cost)
        emissions_avoided = baseline_emissions - recommender_emissions if r['type'] == 'TRANSFER' else 0.0

        total_baseline_purchase_cost += baseline_purchase_cost
        total_recommender_purchase_cost += recommender_purchase_cost
        total_recommender_transfer_cost += recommender_transfer_cost
        
        total_baseline_emissions_kg += baseline_emissions
        total_recommender_emissions_kg += recommender_emissions
        
        validation_records.append({
            "recommendation_id": r['recommendation_id'],
            "component_id": comp_id,
            "component_name": r['component_name'],
            "destination": dest,
            "shortage_quantity": shortage,
            "pack_size": r['pack_size'],
            "baseline_action": "PURCHASE",
            "baseline_purchase_cost": baseline_purchase_cost,
            "recommender_action": r['type'],
            "selected_source": r['source'],
            "recommender_quantity": rec_qty,
            "recommender_transfer_cost": recommender_transfer_cost,
            "recommender_purchase_cost": recommender_purchase_cost,
            "baseline_emissions_kg": round(baseline_emissions, 2),
            "recommender_emissions_kg": round(recommender_emissions, 2),
            "emissions_avoided_kg": round(emissions_avoided, 2),
            "purchase_avoided": purchase_avoided,
            "net_financial_savings": net_savings,
            "confidence": r['confidence'],
            "edge_case_flag": r['edge_case_flag']
        })
        
    df_val = pd.DataFrame(validation_records)
    df_val.to_csv('data/validation_cases.csv', index=False)

    # Seed SQLite ValidationCase table
    session = SessionLocal()
    try:
        session.query(ValidationCase).delete()
        for v in validation_records:
            session.add(ValidationCase(
                recommendation_id=v['recommendation_id'],
                component_id=v['component_id'],
                component_name=v['component_name'],
                destination=v['destination'],
                shortage_quantity=v['shortage_quantity'],
                pack_size=v['pack_size'],
                baseline_action=v['baseline_action'],
                baseline_purchase_cost=v['baseline_purchase_cost'],
                recommender_action=v['recommender_action'],
                selected_source=v['selected_source'],
                recommender_quantity=v['recommender_quantity'],
                recommender_transfer_cost=v['recommender_transfer_cost'],
                recommender_purchase_cost=v['recommender_purchase_cost'],
                baseline_emissions_kg=v['baseline_emissions_kg'],
                recommender_emissions_kg=v['recommender_emissions_kg'],
                emissions_avoided_kg=v['emissions_avoided_kg'],
                purchase_avoided=v['purchase_avoided'],
                net_financial_savings=v['net_financial_savings'],
                confidence=v['confidence'],
                edge_case_flag=v['edge_case_flag']
            ))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error seeding ValidationCase table: {e}")
    finally:
        session.close()

    total_recommender_cost = total_recommender_purchase_cost + total_recommender_transfer_cost
    total_purchase_avoided = total_baseline_purchase_cost - total_recommender_purchase_cost
    total_net_savings = total_baseline_purchase_cost - total_recommender_cost
    total_emissions_avoided_kg = total_baseline_emissions_kg - total_recommender_emissions_kg
    shortages_avoided = transfer_recs_count
    
    summary = {
        "total_shortage_cases": total_shortage_cases,
        "transfer_recommendations": transfer_recs_count,
        "purchase_recommendations": purchase_recs_count,
        "total_units_transferred": total_units_transferred,
        "total_baseline_purchase_cost": round(total_baseline_purchase_cost, 2),
        "total_recommender_purchase_cost": round(total_recommender_purchase_cost, 2),
        "total_recommender_transfer_cost": round(total_recommender_transfer_cost, 2),
        "total_recommender_cost": round(total_recommender_cost, 2),
        "purchase_avoided": round(total_purchase_avoided, 2),
        "net_financial_savings": round(total_net_savings, 2),
        "shortages_avoided": shortages_avoided,
        "total_baseline_emissions_kg": round(total_baseline_emissions_kg, 2),
        "total_recommender_emissions_kg": round(total_recommender_emissions_kg, 2),
        "total_emissions_avoided_kg": round(total_emissions_avoided_kg, 2)
    }
    
    return summary, df_val

if __name__ == '__main__':
    summary, _ = run_validation_experiment()
    print("=== VALIDATION EXPERIMENT SUMMARY ===")
    for k, v in summary.items():
        print(f" {k}: {v}")
