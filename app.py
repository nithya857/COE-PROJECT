import os
import datetime
import pandas as pd
from flask import Flask, render_template, jsonify, request, redirect, url_for
from database import (
    db_session, execute_transfer_transaction,
    OverrideLog, Inventory, Component, Location
)
from recommender import (
    load_data_from_db, generate_recommendations,
    calculate_inventory_metrics, validate_data
)
from metrics import run_validation_experiment

app = Flask(__name__)

# Cache / In-memory storage for interactive session state overrides
session_overrides = {}

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

def get_current_recommendations():
    df_c, df_l, df_i, df_f, df_t = load_data_from_db()
    recs = generate_recommendations(df_i, df_f, df_c, df_l, df_t)
    
    # Merge session state / override log
    for r in recs:
        rec_id = r['recommendation_id']
        if rec_id in session_overrides:
            r['status'] = session_overrides[rec_id]['status']
            r['override_reason'] = session_overrides[rec_id].get('reason', '')
    return recs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommendations')
def recommendations_page():
    return render_template('recommendations.html')

@app.route('/recommendation/<rec_id>')
def details_page(rec_id):
    return render_template('details.html', rec_id=rec_id)

@app.route('/api/dashboard')
def api_dashboard():
    df_c, df_l, df_i, df_f, df_t = load_data_from_db()
    warnings = validate_data(df_c, df_l, df_i, df_f, df_t)
    metrics_df = calculate_inventory_metrics(df_i, df_f, df_c)
    
    summary, val_df = run_validation_experiment()
    recs = get_current_recommendations()
    
    # Extract shortage records table data
    shortages_table = metrics_df[metrics_df['has_shortage']].copy()
    shortage_list = []
    for _, r in shortages_table.iterrows():
        rec_match = next((item for item in recs if item['component_id'] == str(r['component_id']) and item['destination'] == str(r['location'])), None)
        conf = rec_match['confidence'] if rec_match else "MEDIUM"
        
        shortage_list.append({
            "component_id": str(r['component_id']),
            "component_name": str(r['component_name']),
            "location": str(r['location']),
            "current_stock": int(r['current_stock']),
            "forecast_7_days": int(r['forecast_7_days']),
            "projected_stock": float(r['projected_stock']),
            "shortage": float(r['shortage']),
            "urgency": str(r['urgency']),
            "confidence": str(conf)
        })
        
    return jsonify({
        "summary": {
            "total_components": len(df_c),
            "total_locations": len(df_l),
            "active_shortages": summary['total_shortage_cases'],
            "transfer_recommendations": summary['transfer_recommendations'],
            "purchase_recommendations": summary['purchase_recommendations'],
            "total_units_transferred": summary['total_units_transferred'],
            "baseline_purchase": summary['total_baseline_purchase_cost'],
            "recommender_purchase": summary['total_recommender_purchase_cost'],
            "recommender_transfer": summary['total_recommender_transfer_cost'],
            "recommender_total_cost": summary['total_recommender_cost'],
            "purchase_avoided": summary['purchase_avoided'],
            "net_financial_savings": summary['net_financial_savings'],
            "shortages_avoided": summary['shortages_avoided'],
            "baseline_emissions_kg": summary['total_baseline_emissions_kg'],
            "recommender_emissions_kg": summary['total_recommender_emissions_kg'],
            "emissions_avoided_kg": summary['total_emissions_avoided_kg']
        },
        "warnings": warnings,
        "shortages": shortage_list
    })

@app.route('/api/recommendations')
def api_recommendations():
    recs = get_current_recommendations()
    return jsonify(recs)

@app.route('/api/recommendation/<rec_id>')
def api_single_recommendation(rec_id):
    recs = get_current_recommendations()
    match = next((r for r in recs if r['recommendation_id'] == rec_id), None)
    if match:
        return jsonify(match)
    return jsonify({"error": "Recommendation not found"}), 404

@app.route('/api/recommendation/<rec_id>/approve', methods=['POST'])
def approve_recommendation(rec_id):
    recs = get_current_recommendations()
    match = next((r for r in recs if r['recommendation_id'] == rec_id), None)
    
    if match and match['type'] == 'TRANSFER':
        # Execute ACID transactional inventory allocation in SQLite database
        success, msg = execute_transfer_transaction(
            rec_id=rec_id,
            source_loc=match['source'],
            dest_loc=match['destination'],
            comp_id=match['component_id'],
            batch=match['batch'],
            quantity=match['recommended_quantity']
        )
        if success:
            session_overrides[rec_id] = {"status": "APPROVED", "reason": msg}
            return jsonify({"status": "success", "message": f"Recommendation {rec_id} approved. {msg}"})
        else:
            return jsonify({"status": "error", "message": f"Transaction failed: {msg}"}), 400
            
    session_overrides[rec_id] = {"status": "APPROVED", "reason": "Approved Supplier Procurement"}
    return jsonify({"status": "success", "message": f"Recommendation {rec_id} approved."})

@app.route('/api/recommendation/<rec_id>/reject', methods=['POST'])
def reject_recommendation(rec_id):
    session_overrides[rec_id] = {"status": "REJECTED", "reason": "Rejected by Supply Chain Planner"}
    return jsonify({"status": "success", "message": f"Recommendation {rec_id} rejected."})

@app.route('/api/recommendation/<rec_id>/override', methods=['POST'])
def override_recommendation(rec_id):
    data = request.get_json() or {}
    reason = data.get("reason", "Manual planner override")
    
    session_overrides[rec_id] = {"status": "OVERRIDDEN", "reason": reason}
    
    log_entry = {
        "recommendation_id": rec_id,
        "decision": "OVERRIDE",
        "reason": reason,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    override_csv = 'data/override_log.csv'
    df_log = pd.read_csv(override_csv) if os.path.exists(override_csv) else pd.DataFrame(columns=["recommendation_id", "decision", "reason", "timestamp"])
    df_log = pd.concat([df_log, pd.DataFrame([log_entry])], ignore_index=True)
    df_log.to_csv(override_csv, index=False)
    
    return jsonify({"status": "success", "message": f"Recommendation {rec_id} overridden.", "log": log_entry})

if __name__ == '__main__':
    if not os.path.exists('data/inventory.db'):
        from data_generator import generate_datasets
        generate_datasets()
    app.run(host='127.0.0.1', port=5000, debug=True)
