import pytest
pytest.importorskip("numpy")
pytest.importorskip("scipy")
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_strict_prior_15_site_screen_scope():
    d=json.loads((R/"development/camtrapasia_fifteen_candidate_contract_v1_241.json").read_text())
    assert d["fixed_gate"]["distance_less_than_km"]==25
    assert d["fixed_gate"]["candidates_expected"]==15
    assert d["fixed_gate"]["distinct_nearest_original_islands_expected"]==10
    assert d["candidate_island_identity_verified"] is False
    assert d["no_species_occurrences_or_predictive_model_access"] is True
