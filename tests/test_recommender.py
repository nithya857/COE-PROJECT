import pytest
import pandas as pd
from recommender import (
    calculate_inventory_metrics,
    calculate_pack_size_adjustment,
    evaluate_transfer_feasibility,
    generate_recommendations
)

@pytest.fixture
def mock_supply_chain_data():
    df_components = pd.DataFrame([{
        "component_id": "C001",
        "component_name": "Motor Bearing",
        "pack_size": 50,
        "unit_cost": 120,
        "emission_factor": 0.5,
        "criticality": "HIGH"
    }])
    
    df_locations = pd.DataFrame([
        {"location_id": "L001", "location_name": "Chennai"},
        {"location_id": "L002", "location_name": "Bangalore"},
        {"location_id": "L003", "location_name": "Pune"}
    ])
    
    df_inventory = pd.DataFrame([
        # Destination: Chennai (Shortage = 180, needs 4 packs = 200 units)
        {"component_id": "C001", "location": "Chennai", "batch": "B1", "current_stock": 100, "safety_stock": 80, "reserved_stock": 10},
        # Source 1: Bangalore (Surplus available = 350)
        {"component_id": "C001", "location": "Bangalore", "batch": "B1", "current_stock": 400, "safety_stock": 50, "reserved_stock": 0},
        # Source 2: Pune (Current = 120, Safety = 50, Usable surplus = 70 >= 1 pack (50), but available stock 120 - 100 transfer = 20 < 50 safety stock)
        {"component_id": "C001", "location": "Pune", "batch": "B1", "current_stock": 120, "safety_stock": 50, "reserved_stock": 0}
    ])
    
    df_forecast = pd.DataFrame([
        {"component_id": "C001", "location": "Chennai", "batch": "B1", "forecast_7_days": 190, "uncertainty_percent": 10.0, "urgency": "HIGH"},
        {"component_id": "C001", "location": "Bangalore", "batch": "B1", "forecast_7_days": 50, "uncertainty_percent": 10.0, "urgency": "LOW"},
        {"component_id": "C001", "location": "Pune", "batch": "B1", "forecast_7_days": 10, "uncertainty_percent": 10.0, "urgency": "LOW"}
    ])
    
    df_transfers = pd.DataFrame([
        {"source": "Bangalore", "destination": "Chennai", "transfer_time_days": 1, "transfer_cost_per_unit": 8.5, "reliability": 0.95},
        {"source": "Pune", "destination": "Chennai", "transfer_time_days": 5, "transfer_cost_per_unit": 18.0, "reliability": 0.88}
    ])
    
    return df_components, df_locations, df_inventory, df_forecast, df_transfers

def test_shortage_calculation(mock_supply_chain_data):
    """Test 1: Verify shortage calculation formula: projected = current - res - forecast, shortage = max(0, safety - projected)"""
    df_c, df_l, df_i, df_f, df_t = mock_supply_chain_data
    metrics = calculate_inventory_metrics(df_i, df_f, df_c)
    
    chennai = metrics[metrics['location'] == 'Chennai'].iloc[0]
    assert chennai['available_stock'] == 90 # 100 - 10
    assert chennai['projected_stock'] == -100 # 90 - 190
    assert chennai['shortage'] == 180 # 80 - (-100)
    assert chennai['has_shortage'] == True

def test_surplus_calculation(mock_supply_chain_data):
    """Test 2: Verify usable surplus calculation formula: max(0, available_stock - safety_stock)"""
    df_c, df_l, df_i, df_f, df_t = mock_supply_chain_data
    metrics = calculate_inventory_metrics(df_i, df_f, df_c)
    
    bangalore = metrics[metrics['location'] == 'Bangalore'].iloc[0]
    assert bangalore['available_stock'] == 400
    assert bangalore['usable_surplus'] == 350 # 400 - 50
    assert bangalore['has_surplus'] == True

def test_pack_size_handling():
    """Test 3: Verify variable pack size adjustment (rounding up to whole pack multiples)"""
    shortage = 120
    pack_size = 50
    rec_qty, num_packs, note = calculate_pack_size_adjustment(shortage, pack_size, available_surplus=500)
    
    assert rec_qty == 150
    assert num_packs == 3
    assert "150 units (3 complete packs of 50)" in note

def test_safety_stock_protection(mock_supply_chain_data):
    """Test 4: Verify safety stock protection rejects transfers that reduce source stock below safety threshold"""
    df_c, df_l, df_i, df_f, df_t = mock_supply_chain_data
    metrics = calculate_inventory_metrics(df_i, df_f, df_c)
    
    dest_row = metrics[metrics['location'] == 'Chennai'].iloc[0]
    dest_row['urgency'] = 'LOW' # Max lead time 14 days, so Pune's 5 days lead time passes Rule 2
    
    pune_source = metrics[metrics['location'] == 'Pune'].copy()
    # Usable surplus = 60 (allows 1 pack of 50), but available stock = 70, safety stock = 50
    # 70 - 50 = 20 < 50 safety stock threshold -> Rule 4 triggers!
    pune_source.loc[:, 'usable_surplus'] = 60
    pune_source.loc[:, 'available_stock'] = 70
    pune_source.loc[:, 'safety_stock'] = 50

    feasible, rejected = evaluate_transfer_feasibility(dest_row, pune_source, df_t, df_c)
    
    assert len(feasible) == 0
    assert len(rejected) == 1
    assert "safety stock threshold" in rejected[0]['reason']

def test_transfer_time_rejection(mock_supply_chain_data):
    """Test 5: Verify transfer is rejected when transfer lead time exceeds service urgency threshold"""
    df_c, df_l, df_i, df_f, df_t = mock_supply_chain_data
    metrics = calculate_inventory_metrics(df_i, df_f, df_c)
    
    dest_row = metrics[metrics['location'] == 'Chennai'].iloc[0]
    dest_row['urgency'] = 'CRITICAL' # Max allowed lead time = 1 day
    
    # Pune has transfer lead time of 5 days to Chennai
    pune_source = metrics[metrics['location'] == 'Pune']
    feasible, rejected = evaluate_transfer_feasibility(dest_row, pune_source, df_t, df_c)
    
    assert len(feasible) == 0
    assert len(rejected) >= 1
    assert "exceeds service urgency threshold" in rejected[0]['reason']

def test_no_surplus_purchase_recommendation(mock_supply_chain_data):
    """Test 6: Verify fallback to Purchase recommendation when no network surplus exists"""
    df_c, df_l, df_i, df_f, df_t = mock_supply_chain_data
    
    # Set all sources to zero surplus
    df_i['current_stock'] = 10
    df_i['safety_stock'] = 50
    
    recs = generate_recommendations(df_i, df_f, df_c, df_l, df_t)
    
    assert len(recs) > 0
    first_rec = recs[0]
    assert first_rec['type'] == 'PURCHASE'
    assert first_rec['source'] == 'SUPPLIER'
    assert "No location in the network has usable surplus" in first_rec['evidence'][1]
