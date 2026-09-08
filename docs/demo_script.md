# 5-Minute College Viva Demonstration Script (Review 1)

## Step 1: Project Objective (0:00 - 0:45)
"Respected evaluators, our project is titled **Multi-Location Balancing Recommender for a Manufacturer Managing Components Supplied in Variable Pack Sizes**. In manufacturing, plant shortages lead to expensive supplier procurement orders while neighboring plants hold surplus inventory. Crucially, components cannot be shipped in arbitrary amounts—they are supplied in fixed pack sizes (e.g. 50 or 100 units). Our 45% Review 1 prototype provides an explainable decision-support system that balances network stock using complete pack transfers."

## Step 2: Architecture & Dataset Overview (0:45 - 1:30)
"We have built a lightweight Python Flask solution with 10 components (C001-C010) across 5 locations (Chennai, Bangalore, Coimbatore, Hyderabad, Pune). 
Let us launch the system by generating our reproducible dataset with `python data_generator.py` and starting our server with `python app.py`."

## Step 3: Dashboard & Baseline Comparison (1:30 - 2:45)
"Navigating to `http://127.0.0.1:5000/`, our dashboard displays key metric cards:
1. **Active Shortages**: Detected by comparing current inventory, safety stock, and 7-day forecast.
2. **Purchase Avoided & Shortages Avoided**: Measuring exact financial savings.
3. **Three Core Charts**:
   - Chart 1 compares Baseline Purchase Cost vs Recommender Purchase Cost.
   - Chart 2 shows Shortages Avoided via inter-location transfers.
   - Chart 3 breaks down Inter-Location Transfer Costs vs Supplier Purchase Costs."

## Step 4: Variable Pack-Size & Edge Cases Demonstration (2:45 - 4:00)
"Clicking on **Recommendations**, we can examine individual recommendation details:
- **Variable Pack Size Handling**: For a shortage of 120 units with a pack size of 50, the engine adjusts the quantity to 150 units (3 complete packs).
- **Explainable Evidence**: Under 'WHY THIS RECOMMENDATION?', the system lists exact mathematical proof: surplus availability, source safety stock protection, lead time feasibility, and cost savings.
- **Four Edge Cases**:
  1. *No Surplus Available*: Direct supplier purchase recommendation.
  2. *Transfer Too Slow*: Rejected due to service urgency violation.
  3. *Safety Stock Violation*: Rejected to protect source inventory.
  4. *Pack-Size Adjustment*: Whole pack rounding display."

## Step 5: Human Approval & Override Logging (4:00 - 5:00)
"High-impact recommendations (high criticality, large quantities, or low confidence) require human planner approval.
If a planner clicks **Override**, the system prompts for an operational reason and logs the decision with a timestamp to `data/override_log.csv`.
Finally, our automated test suite can be run with `pytest tests/test_recommender.py` to verify all business rules."
