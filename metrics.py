import os
import pandas as pd
import numpy as np
from recommender import (
    generate_recommendations,
    calculate_inventory_metrics
)

def run_validation_experiment():
    """
    Executes reproducible validation experiment comparing Baseline Strategy (Purchase All)
    against the Multi-Location Balancing Recommender.
    Generates data/validation_cases.csv with line-item comparison.
    """
    df_components = pd.read_csv('data/components.csv')
    df_locations = pd.read_csv('data/locations.csv')
    df_inventory = pd.read_csv('data/inventory.csv')
    df_forecast = pd.read_csv('data/forecast.csv')
    df_transfers = pd.read_csv('data/transfers.csv')

    recs = generate_recommendations(df_inventory, df_forecast, df_components, df_locations, df_transfers)
    
    validation_records = []
    
    total_shortage_cases = len(recs)
    transfer_recs_count = 0
    purchase_recs_count = 0
    
    total_baseline_purchase_cost = 0.0
    total_recommender_purchase_cost = 0.0
    total_recommender_transfer_cost = 0.0
    total_units_transferred = 0
    
    for r in recs:
        comp_id = r['component_id']
        dest = r['destination']
        batch = r['batch']
        shortage = r['required_quantity']
        rec_qty = r['recommended_quantity']
        unit_cost = r['purchase_cost'] / rec_qty if rec_qty > 0 else 0
        
        # Baseline: Always purchase full shortage (rounded to complete pack size)
        baseline_qty = rec_qty
        baseline_purchase_cost = baseline_qty * unit_cost
        
        if r['type'] == 'TRANSFER':
            transfer_recs_count += 1
            recommender_purchase_cost = 0.0
            recommender_transfer_cost = r['transfer_cost']
            total_units_transferred += rec_qty
            action_taken = f"TRANSFER ({r['source']} -> {dest})"
        else:
            purchase_recs_count += 1
            recommender_purchase_cost = r['purchase_cost']
            recommender_transfer_cost = 0.0
            action_taken = f"PURCHASE (Supplier -> {dest})"
            
        purchase_avoided = baseline_purchase_cost - recommender_purchase_cost
        net_savings = baseline_purchase_cost - (recommender_purchase_cost + recommender_transfer_cost)
        
        total_baseline_purchase_cost += baseline_purchase_cost
        total_recommender_purchase_cost += recommender_purchase_cost
        total_recommender_transfer_cost += recommender_transfer_cost
        
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
            "purchase_avoided": purchase_avoided,
            "net_financial_savings": net_savings,
            "confidence": r['confidence'],
            "edge_case_flag": r['edge_case_flag']
        })
        
    df_val = pd.DataFrame(validation_records)
    df_val.to_csv('data/validation_cases.csv', index=False)
    
    total_recommender_cost = total_recommender_purchase_cost + total_recommender_transfer_cost
    total_purchase_avoided = total_baseline_purchase_cost - total_recommender_purchase_cost
    total_net_savings = total_baseline_purchase_cost - total_recommender_cost
    shortages_avoided = transfer_recs_count # Each transfer resolves a shortage via existing inventory
    
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
        "shortages_avoided": shortages_avoided
    }
    
    return summary, df_val

if __name__ == '__main__':
    summary, _ = run_validation_experiment()
    print("=== VALIDATION EXPERIMENT SUMMARY ===")
    for k, v in summary.items():
        print(f" {k}: {v}")
