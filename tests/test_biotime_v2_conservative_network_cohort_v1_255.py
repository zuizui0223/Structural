"""Verify 33-candidate, no-outcome cohort and reject selection based on wrong physical counts."""
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_biotime_v2_conservative_network_cohort_v1_255 import verify

COHORT=json.loads((ROOT/"development/biotime_v2_conservative_network_cohort_v1_255.json").read_text())
PHYSICAL=json.loads((ROOT/"development/biotime_v2_reserved_physical_support_freeze_v1_253.json").read_text())

def test_original_33_network_representatives_without_species_read():
    r=verify(COHORT,PHYSICAL)
    assert r["status"]=="RESPONSE_FREE_33_NETWORK_PROXIES_VERIFIED"
    assert r["by_realm"]=={"Freshwater":5,"Marine":11,"Terrestrial":17}
    assert r["cross_split_excluded_ids"]==["272","559","560","837"]
    assert r["within_holdout_duplicate_removed_ids"]==["296","367","570","596","679","731","835"]
    assert r["not_claiming_33_independent_archipelagos"] is True

def test_duplicate_representative_changed_to_lower_quality_stops():
    bad=copy.deepcopy(COHORT)
    for g in bad["within_reserved_near_duplicate_groups"]:
        if set(g["members"])=={"367","917"}:g["representative"]="367"
    try:
        verify(bad,PHYSICAL)
    except ValueError as e:
        assert "Representative" in str(e)
    else:
        raise AssertionError("Must reject post-freeze representative selection")

def test_cross_split_duplicated_candidate_cannot_be_resurrected():
    bad=copy.deepcopy(COHORT)
    bad["selected_study_ids_by_realm"]["Freshwater"][0]="559"
    try:
        verify(bad,PHYSICAL)
    except ValueError as e:
        assert "33" in str(e) or "network" in str(e).lower()
    else:
        raise AssertionError("Must reject previously pilot-linked reserved study")
