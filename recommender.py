import math
import pandas as pd
import numpy as np

URGENCY_MAX_DAYS = {
    "CRITICAL": 1,
    "HIGH": 3,
    "MEDIUM": 7,
    "LOW": 14
}

def validate_data(df_components, df_locations, df_inventory, df_forecast, df_transfers):
    """
    Validates supply chain datasets for data quality errors.
    Returns a list of error/warning message dictionaries.
    """
    warnings = []
    
    # Check for missing values
    for name, df in [("components", df_components), ("locations", df_locations), 
                     ("inventory", df_inventory), ("forecast", df_forecast), ("transfers", df_transfers)]:
        if df.isnull().sum().sum() > 0:
            warnings.append({"type": "WARNING", "dataset": name, "message": "Dataset contains missing values."})
            
    # Check negative stock in inventory
    if (df_inventory['current_stock'] < 0).any():
        warnings.append({"type": "ERROR", "dataset": "inventory", "message": "Negative current_stock detected."})
    if (df_inventory['safety_stock'] < 0).any():
        warnings.append({"type": "ERROR", "dataset": "inventory", "message": "Negative safety_stock detected."})
        
    # Check invalid pack sizes
    if (df_components['pack_size'] <= 0).any():
        warnings.append({"type": "ERROR", "dataset": "components", "message": "Invalid non-positive pack_size detected."})
        
    # Check invalid unit costs
    if (df_components['unit_cost'] <= 0).any():
        warnings.append({"type": "ERROR", "dataset": "components", "message": "Invalid non-positive unit_cost detected."})

    return warnings

def calculate_inventory_metrics(df_inventory, df_forecast, df_components):
    """
    Combines inventory, forecast, and component data to compute projected stock, shortage, and usable surplus.
    """
    # Merge datasets
    merged = pd.merge(df_inventory, df_forecast, on=['component_id', 'location', 'batch'], how='inner')
    merged = pd.merge(merged, df_components, on='component_id', how='inner')
    
    # Calculate available stock
    merged['available_stock'] = merged['current_stock'] - merged['reserved_stock']
    
    # Calculate projected stock (available_stock - forecast_7_days)
    merged['projected_stock'] = merged['available_stock'] - merged['forecast_7_days']
    
    # Calculate shortage = max(0, safety_stock - projected_stock)
    merged['shortage'] = merged.apply(lambda r: max(0, r['safety_stock'] - r['projected_stock']), axis=1)
    merged['has_shortage'] = merged['shortage'] > 0
    
    # Calculate usable surplus = max(0, available_stock - safety_stock)
    merged['usable_surplus'] = merged.apply(lambda r: max(0, r['available_stock'] - r['safety_stock']), axis=1)
    merged['has_surplus'] = merged['usable_surplus'] > 0
    
    return merged

def calculate_pack_size_adjustment(shortage_qty, pack_size, available_surplus=None):
    """
    Calculates whole-pack transfer requirements and adjustments.
    """
    if shortage_qty <= 0:
        return 0, 0, "No shortage to cover."
        
    num_packs = math.ceil(shortage_qty / pack_size)
    recommended_qty = num_packs * pack_size
    
    if available_surplus is not None and available_surplus < recommended_qty:
        # Bounded by source surplus
        max_packs = math.floor(available_surplus / pack_size)
        if max_packs > 0:
            recommended_qty = max_packs * pack_size
            num_packs = max_packs
            adjustment_note = (f"Shortage of {shortage_qty} units rounded to {num_packs * pack_size} units, "
                               f"but source usable surplus limits transfer to {recommended_qty} units ({num_packs} packs of {pack_size}).")
        else:
            return 0, 0, "Source usable surplus is insufficient for even one complete pack."
    else:
        adjustment_note = f"Shortage of {shortage_qty} units adjusted to {recommended_qty} units ({num_packs} complete packs of {pack_size})."
        
    return recommended_qty, num_packs, adjustment_note

def evaluate_transfer_feasibility(dest_row, candidate_sources, df_transfers, df_components):
    """
    Evaluates candidate source locations for a destination shortage.
    Checks surplus availability, safety stock preservation, urgency deadline, and pack-size rules.
    """
    comp_id = dest_row['component_id']
    dest_loc = dest_row['location']
    shortage = dest_row['shortage']
    urgency = dest_row['urgency']
    pack_size = dest_row['pack_size']
    max_urgency_days = URGENCY_MAX_DAYS.get(urgency, 14)
    
    feasible_candidates = []
    rejected_candidates = []
    
    for _, src_row in candidate_sources.iterrows():
        src_loc = src_row['location']
        if src_loc == dest_loc:
            continue
            
        usable_surplus = src_row['usable_surplus']
        
        # Look up transfer route
        route = df_transfers[(df_transfers['source'] == src_loc) & (df_transfers['destination'] == dest_loc)]
        if route.empty:
            rejected_candidates.append({
                "source": src_loc,
                "reason": f"No active transfer route configured from {src_loc} to {dest_loc}."
            })
            continue
            
        transfer_time = route.iloc[0]['transfer_time_days']
        transfer_cost_unit = route.iloc[0]['transfer_cost_per_unit']
        reliability = route.iloc[0]['reliability']
        
        # Rule 1: Surplus >= 1 pack
        if usable_surplus < pack_size:
            rejected_candidates.append({
                "source": src_loc,
                "reason": f"Source usable surplus ({usable_surplus} units) is less than one complete pack ({pack_size} units)."
            })
            continue
            
        # Rule 2: Service Urgency Check
        if transfer_time > max_urgency_days:
            rejected_candidates.append({
                "source": src_loc,
                "reason": f"Transfer time ({transfer_time} days) exceeds service urgency threshold ({max_urgency_days} days for {urgency} urgency)."
            })
            continue
            
        # Rule 3: Calculate pack adjustment
        rec_qty, num_packs, pack_note = calculate_pack_size_adjustment(shortage, pack_size, usable_surplus)
        if rec_qty <= 0:
            rejected_candidates.append({
                "source": src_loc,
                "reason": pack_note
            })
            continue
            
        # Rule 4: Safety Stock Protection Check at Source
        post_transfer_stock = src_row['available_stock'] - rec_qty
        if post_transfer_stock < src_row['safety_stock']:
            rejected_candidates.append({
                "source": src_loc,
                "reason": f"Transfer of {rec_qty} units would reduce source stock below safety stock threshold ({src_row['safety_stock']} units)."
            })
            continue

        # Decision Support Score Calculation
        unit_cost = dest_row['unit_cost']
        service_score = max(0.0, 1.0 - (transfer_time / max_urgency_days))
        cost_score = max(0.0, 1.0 - (transfer_cost_unit / unit_cost)) if unit_cost > 0 else 0.5
        reliability_score = float(reliability)
        
        # Weighted Decision-Support Score
        score = round(0.5 * service_score + 0.3 * cost_score + 0.2 * reliability_score, 3)

        feasible_candidates.append({
            "source": str(src_loc),
            "recommended_qty": int(rec_qty),
            "num_packs": int(num_packs),
            "pack_size": int(pack_size),
            "transfer_time_days": int(transfer_time),
            "transfer_cost_per_unit": float(transfer_cost_unit),
            "transfer_cost": float(rec_qty * transfer_cost_unit),
            "reliability": float(reliability),
            "score": float(score),
            "pack_note": str(pack_note),
            "usable_surplus": float(usable_surplus)
        })
        
    return feasible_candidates, rejected_candidates

def calculate_uncertainty_and_confidence(dest_row, selected_candidate=None):
    """
    Computes forecast uncertainty range and confidence rating.
    """
    forecast = float(dest_row['forecast_7_days'])
    unc_pct = float(dest_row['uncertainty_percent'])
    
    range_min = round(max(0.0, forecast * (1.0 - unc_pct / 100.0)), 1)
    range_max = round(forecast * (1.0 + unc_pct / 100.0), 1)
    
    if selected_candidate is None:
        # Purchase recommendation or no feasible transfer
        if unc_pct > 20.0:
            confidence = "LOW"
        else:
            confidence = "MEDIUM"
    else:
        # Transfer recommendation
        surplus = selected_candidate['usable_surplus']
        req_qty = selected_candidate['recommended_qty']
        
        if unc_pct <= 15.0 and surplus >= 1.5 * req_qty:
            confidence = "HIGH"
        elif unc_pct <= 25.0 and surplus >= req_qty:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
            
    disclaimer = "This recommendation is decision support and is not a guaranteed outcome."
    
    return {
        "forecast": forecast,
        "uncertainty_percent": unc_pct,
        "range_min": range_min,
        "range_max": range_max,
        "confidence": confidence,
        "disclaimer": disclaimer
    }

def generate_recommendations(df_inventory, df_forecast, df_components, df_locations, df_transfers):
    """
    Runs the full recommendation engine over all components and locations.
    Returns a list of detailed recommendation dictionary objects.
    """
    processed = calculate_inventory_metrics(df_inventory, df_forecast, df_components)
    shortages = processed[processed['has_shortage']].copy()
    
    recommendations = []
    rec_counter = 1
    
    for idx, dest_row in shortages.iterrows():
        comp_id = str(dest_row['component_id'])
        comp_name = str(dest_row['component_name'])
        dest_loc = str(dest_row['location'])
        batch = str(dest_row['batch'])
        shortage_qty = int(dest_row['shortage'])
        unit_cost = float(dest_row['unit_cost'])
        pack_size = int(dest_row['pack_size'])
        criticality = str(dest_row['criticality'])
        
        # Find candidate source locations for same component & batch with usable surplus > 0
        candidate_sources = processed[
            (processed['component_id'] == comp_id) & 
            (processed['batch'] == batch) & 
            (processed['has_surplus'])
        ]
        
        feasible, rejected = evaluate_transfer_feasibility(dest_row, candidate_sources, df_transfers, df_components)
        
        rec_id = f"REC-{rec_counter:03d}"
        rec_counter += 1
        
        if len(feasible) == 0:
            # RULE 1: Purchase Recommendation (No feasible transfer source)
            req_packs = int(math.ceil(shortage_qty / pack_size))
            rec_qty = int(req_packs * pack_size)
            purchase_cost = float(rec_qty * unit_cost)
            transfer_cost = 0.0
            
            unc_info = calculate_uncertainty_and_confidence(dest_row, None)
            
            # Edge Case Reason Classification
            if len(candidate_sources) == 0:
                edge_case = "Edge Case 1: No surplus available in network"
                primary_reason = "No location in the network has usable surplus for this component."
            else:
                edge_case = "Transfer rejected: Constraints violated"
                primary_reason = rejected[0]['reason'] if rejected else "No candidate source satisfied all constraints."

            requires_approval = bool((criticality in ['HIGH', 'CRITICAL']) or (rec_qty > 200) or (unc_info['confidence'] == 'LOW'))
            
            recommendations.append({
                "recommendation_id": rec_id,
                "type": "PURCHASE",
                "component_id": comp_id,
                "component_name": comp_name,
                "destination": dest_loc,
                "source": "SUPPLIER",
                "batch": batch,
                "required_quantity": shortage_qty,
                "recommended_quantity": rec_qty,
                "num_packs": req_packs,
                "pack_size": pack_size,
                "transfer_time_days": 0,
                "transfer_cost": 0.0,
                "purchase_cost": purchase_cost,
                "cost_difference": purchase_cost,
                "decision_score": 0.0,
                "confidence": unc_info['confidence'],
                "uncertainty": unc_info,
                "criticality": criticality,
                "status": "PENDING_APPROVAL" if requires_approval else "AUTO_RECOMMENDED",
                "requires_approval": requires_approval,
                "evidence": [
                    f"Destination {dest_loc} has an active shortage of {shortage_qty} units.",
                    primary_reason,
                    f"Direct supplier purchase of {req_packs} complete packs ({rec_qty} units) is recommended to prevent stockout."
                ],
                "rejected_sources": rejected,
                "edge_case_flag": edge_case,
                "pack_adjustment_note": f"Shortage of {shortage_qty} units rounded to {rec_qty} units ({req_packs} packs of {pack_size}) for supplier procurement."
            })
            
        else:
            # RULE 2 & 3: Rank feasible sources and pick best score
            feasible_sorted = sorted(feasible, key=lambda x: x['score'], reverse=True)
            best_source = feasible_sorted[0]
            
            rec_qty = int(best_source['recommended_qty'])
            num_packs = int(best_source['num_packs'])
            transfer_cost = float(best_source['transfer_cost'])
            purchase_cost = float(rec_qty * unit_cost)
            cost_difference = float(purchase_cost - transfer_cost)
            
            unc_info = calculate_uncertainty_and_confidence(dest_row, best_source)
            
            requires_approval = bool((criticality in ['HIGH', 'CRITICAL']) or (rec_qty > 200) or (unc_info['confidence'] == 'LOW'))
            
            # Edge Case 4 flag: if shortage != recommended quantity
            if shortage_qty != rec_qty:
                edge_case = "Edge Case 4: Pack-size adjustment applied"
            else:
                edge_case = "Standard Transfer Recommendation"

            recommendations.append({
                "recommendation_id": rec_id,
                "type": "TRANSFER",
                "component_id": comp_id,
                "component_name": comp_name,
                "destination": dest_loc,
                "source": best_source['source'],
                "batch": batch,
                "required_quantity": shortage_qty,
                "recommended_quantity": rec_qty,
                "num_packs": num_packs,
                "pack_size": pack_size,
                "transfer_time_days": int(best_source['transfer_time_days']),
                "transfer_cost": transfer_cost,
                "purchase_cost": purchase_cost,
                "cost_difference": cost_difference,
                "decision_score": float(best_source['score']),
                "confidence": unc_info['confidence'],
                "uncertainty": unc_info,
                "criticality": criticality,
                "status": "PENDING_APPROVAL" if requires_approval else "AUTO_RECOMMENDED",
                "requires_approval": requires_approval,
                "evidence": [
                    f"Destination {dest_loc} has an active shortage of {shortage_qty} units.",
                    f"Source {best_source['source']} has {best_source['usable_surplus']} units usable surplus.",
                    f"Post-transfer source inventory remains safely above safety stock.",
                    f"Pack-size rule satisfied ({num_packs} complete packs of {pack_size}).",
                    f"Transfer lead time ({best_source['transfer_time_days']} days) satisfies {dest_row['urgency']} service urgency threshold.",
                    f"Inter-location transfer saves ₹{cost_difference:,.2f} compared to direct supplier purchase."
                ],
                "rejected_sources": rejected,
                "edge_case_flag": edge_case,
                "pack_adjustment_note": best_source['pack_note']
            })
            
    return recommendations
