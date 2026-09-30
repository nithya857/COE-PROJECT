import pytest
import pandas as pd
from recommender import (
    validate_data,
    evaluate_transfer_feasibility,
    generate_recommendations,
    calculate_inventory_metrics
)
from database import execute_transfer_transaction, init_db, SessionLocal, Inventory, Component, Location

@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes SQLite test database metadata before running error boundary tests."""
    init_db()

def test_invalid_negative_stock_validation():
    """
    Error Boundary 1: Invalid Negative Stock Guard
    Verifies that validate_data() detects negative stock in inventory datasets
    and returns explicit quality warnings without crashing.
    """
    df_components = pd.DataFrame([{"component_id": "C001", "component_name": "Bearing", "pack_size": 50, "unit_cost": 100, "criticality": "HIGH"}])
    df_locations = pd.DataFrame([{"location_id": "L001", "location_name": "Chennai"}])
    df_inventory = pd.DataFrame([{"component_id": "C001", "location": "Chennai", "batch": "B1", "current_stock": -50, "safety_stock": 20, "reserved_stock": 0}])
    df_forecast = pd.DataFrame([{"component_id": "C001", "location": "Chennai", "batch": "B1", "forecast_7_days": 10, "uncertainty_percent": 10.0, "urgency": "LOW"}])
    df_transfers = pd.DataFrame([])

    warnings = validate_data(df_components, df_locations, df_inventory, df_forecast, df_transfers)
    
    assert len(warnings) >= 1
    assert any(w['dataset'] == 'inventory' and 'Negative current_stock' in w['message'] for w in warnings)

def test_zero_or_negative_pack_size_error_guard():
    """
    Error Boundary 2: Non-Positive Pack Size Guard
    Verifies that validate_data() flags invalid pack sizes <= 0.
    """
    df_components = pd.DataFrame([{"component_id": "C001", "component_name": "Bearing", "pack_size": 0, "unit_cost": 100, "criticality": "HIGH"}])
    df_locations = pd.DataFrame([{"location_id": "L001", "location_name": "Chennai"}])
    df_inventory = pd.DataFrame([{"component_id": "C001", "location": "Chennai", "batch": "B1", "current_stock": 100, "safety_stock": 20, "reserved_stock": 0}])
    df_forecast = pd.DataFrame([{"component_id": "C001", "location": "Chennai", "batch": "B1", "forecast_7_days": 10, "uncertainty_percent": 10.0, "urgency": "LOW"}])
    df_transfers = pd.DataFrame([])

    warnings = validate_data(df_components, df_locations, df_inventory, df_forecast, df_transfers)
    
    assert len(warnings) >= 1
    assert any(w['dataset'] == 'components' and 'invalid' in w['message'].lower() for w in warnings)

def test_missing_transfer_route_fallback():
    """
    Error Boundary 3: Missing Inter-Location Graph Route Fallback
    Verifies that when no active transfer route exists between source and destination,
    the candidate source is rejected with a clear route missing reason.
    """
    df_components = pd.DataFrame([{"component_id": "C001", "component_name": "Bearing", "pack_size": 50, "unit_cost": 100, "unit_weight_kg": 1.0, "criticality": "HIGH"}])
    df_locations = pd.DataFrame([
        {"location_id": "L001", "location_name": "Chennai"},
        {"location_id": "L002", "location_name": "Pune"}
    ])
    df_inventory = pd.DataFrame([
        {"component_id": "C001", "location": "Chennai", "batch": "B1", "current_stock": 10, "safety_stock": 50, "reserved_stock": 0},
        {"component_id": "C001", "location": "Pune", "batch": "B1", "current_stock": 500, "safety_stock": 50, "reserved_stock": 0}
    ])
    df_forecast = pd.DataFrame([
        {"component_id": "C001", "location": "Chennai", "batch": "B1", "forecast_7_days": 100, "uncertainty_percent": 10.0, "urgency": "HIGH"},
        {"component_id": "C001", "location": "Pune", "batch": "B1", "forecast_7_days": 10, "uncertainty_percent": 10.0, "urgency": "LOW"}
    ])
    # Empty transfer routes dataframe -> no route from Pune to Chennai
    df_transfers = pd.DataFrame(columns=["source", "destination", "distance_km", "transfer_time_days", "transfer_cost_per_unit", "transport_mode", "vehicle_emission_rate", "reliability"])

    metrics = calculate_inventory_metrics(df_inventory, df_forecast, df_components)
    dest_row = metrics[metrics['location'] == 'Chennai'].iloc[0]
    pune_source = metrics[metrics['location'] == 'Pune']

    feasible, rejected = evaluate_transfer_feasibility(dest_row, pune_source, df_transfers, df_components)

    assert len(feasible) == 0
    assert len(rejected) == 1
    assert "No active transfer route configured" in rejected[0]['reason']

def test_database_transaction_rollback():
    """
    Error Boundary 4: ACID Transaction Rollback Guard
    Verifies that execute_transfer_transaction() aborts and rolls back changes
    when a stock transfer would breach the source safety stock threshold.
    """
    session = SessionLocal()
    try:
        # Clean up temporary test component C999 if present
        session.query(Inventory).filter(Inventory.component_id == "C999").delete()
        session.query(Component).filter(Component.component_id == "C999").delete()
        session.commit()

        session.add(Component(component_id="C999", component_name="Test Widget", pack_size=50, unit_cost=100.0, unit_weight_kg=1.0, criticality="HIGH"))
        session.add(Inventory(component_id="C999", location="Chennai", batch="B1", current_stock=100, safety_stock=80, reserved_stock=0))
        session.add(Inventory(component_id="C999", location="Pune", batch="B1", current_stock=100, safety_stock=80, reserved_stock=0))
        session.commit()

        # Attempt to transfer 50 units from Pune (available = 100, safety = 80 -> remaining stock = 50 < 80 safety)
        success, msg = execute_transfer_transaction(
            rec_id="REC-TEST-ERR",
            source_loc="Pune",
            dest_loc="Chennai",
            comp_id="C999",
            batch="B1",
            quantity=50
        )

        assert success == False, "Transaction must fail due to safety stock violation"
        assert "Transaction aborted" in msg or "safety stock" in msg

        # Verify database inventory remains unchanged due to rollback
        pune_inv = session.query(Inventory).filter(Inventory.location == "Pune", Inventory.component_id == "C999").first()
        assert pune_inv.current_stock == 100, "Source stock must remain unchanged after rollback"

    finally:
        session.query(Inventory).filter(Inventory.component_id == "C999").delete()
        session.query(Component).filter(Component.component_id == "C999").delete()
        session.commit()
        session.close()

def test_corrupt_or_empty_dataset_graceful_handling():
    """
    Error Boundary 5: Empty Inventory Dataset Graceful Handling
    Verifies that generate_recommendations() handles empty shortage datasets without raising exceptions.
    """
    df_components = pd.DataFrame([{"component_id": "C001", "component_name": "Bearing", "pack_size": 50, "unit_cost": 100, "unit_weight_kg": 1.0, "criticality": "HIGH"}])
    df_locations = pd.DataFrame([{"location_id": "L001", "location_name": "Chennai"}])
    # Inventory current stock high -> zero shortages
    df_inventory = pd.DataFrame([{"component_id": "C001", "location": "Chennai", "batch": "B1", "current_stock": 500, "safety_stock": 50, "reserved_stock": 0}])
    df_forecast = pd.DataFrame([{"component_id": "C001", "location": "Chennai", "batch": "B1", "forecast_7_days": 10, "uncertainty_percent": 10.0, "urgency": "LOW"}])
    df_transfers = pd.DataFrame([])

    recs = generate_recommendations(df_inventory, df_forecast, df_components, df_locations, df_transfers)

    assert isinstance(recs, list)
    assert len(recs) == 0, "No recommendations generated when zero shortages exist"
