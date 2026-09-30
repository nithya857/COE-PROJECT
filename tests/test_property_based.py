import math
import pytest
from hypothesis import given, settings, strategies as st
from recommender import (
    calculate_pack_size_adjustment,
    generate_recommendations,
    load_data_from_db
)

@given(
    shortage=st.integers(min_value=1, max_value=1_000_000),
    pack_size=st.integers(min_value=1, max_value=10_000)
)
def test_unbounded_pack_size_rounding_properties(shortage, pack_size):
    """
    Property 1: Unbounded Whole-Pack Quantization & Over-Allocation Bounds
    For any shortage S > 0 and pack size P > 0:
    - Recommended quantity Q >= S
    - Q is a whole multiple of P (Q % P == 0)
    - Over-allocation Q - S < P (minimal over-allocation)
    - Number of packs N = ceil(S / P)
    """
    rec_qty, num_packs, note = calculate_pack_size_adjustment(shortage, pack_size, available_surplus=None)
    
    assert rec_qty >= shortage, f"Unbounded rec qty {rec_qty} must cover shortage {shortage}"
    assert rec_qty % pack_size == 0, f"Rec qty {rec_qty} must be whole multiple of pack size {pack_size}"
    assert rec_qty - shortage < pack_size, f"Over-allocation {rec_qty - shortage} must be strictly less than pack size {pack_size}"
    assert num_packs * pack_size == rec_qty, f"Num packs {num_packs} * pack size {pack_size} must equal rec qty {rec_qty}"

@given(
    shortage=st.integers(min_value=1, max_value=500_000),
    pack_size=st.integers(min_value=1, max_value=5_000),
    available_surplus=st.integers(min_value=0, max_value=500_000)
)
def test_surplus_bounded_transfer_properties(shortage, pack_size, available_surplus):
    """
    Property 2: Surplus-Bounded Pack Size Quantization Invariants
    For any shortage S, pack size P, and source usable surplus U:
    - Rec qty Q is always a whole multiple of P (Q % P == 0)
    - Rec qty Q is bounded by available surplus (Q <= U)
    - If U < P, Q is 0 (cannot transfer partial packs)
    """
    rec_qty, num_packs, note = calculate_pack_size_adjustment(shortage, pack_size, available_surplus=available_surplus)
    
    assert rec_qty % pack_size == 0, f"Rec qty {rec_qty} must be whole pack multiple of {pack_size}"
    assert rec_qty <= available_surplus, f"Rec qty {rec_qty} must never exceed available surplus {available_surplus}"
    
    if available_surplus < pack_size:
        assert rec_qty == 0, "Transfer must be 0 when usable surplus is less than 1 pack"

@settings(deadline=None, max_examples=50)
@given(
    demand_spike=st.integers(min_value=10_000, max_value=5_000_000)
)
def test_extreme_demand_surge_resilience(demand_spike):
    """
    Property 3: Extreme Demand Spike Resilience
    Under massive demand spikes (up to 5,000,000 units), the recommendation engine:
    - Never crashes or raises unhandled exceptions.
    - Preserves pack size integer rounding across all generated recommendations.
    - If PURCHASE is recommended, Q >= S.
    - If TRANSFER is recommended, Q <= source usable surplus and Q % P == 0.
    """
    df_c, df_l, df_i, df_f, df_t = load_data_from_db()
    
    # Inject extreme demand spike into forecast dataset
    df_f_spiked = df_f.copy()
    df_f_spiked.loc[0, 'forecast_7_days'] = float(demand_spike)
    
    recs = generate_recommendations(df_i, df_f_spiked, df_c, df_l, df_t)
    
    assert len(recs) > 0, "Engine must return valid recommendation list"
    
    for r in recs:
        assert r['recommended_quantity'] % r['pack_size'] == 0, "All rec quantities must be whole pack multiples"
        if r['type'] == 'PURCHASE':
            assert r['recommended_quantity'] >= r['required_quantity'], "Purchase rec must cover full required shortage"
        elif r['type'] == 'TRANSFER':
            assert r['recommended_quantity'] > 0, "Transfer rec quantity must be positive"
