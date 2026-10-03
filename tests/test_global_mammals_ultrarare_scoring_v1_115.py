from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_ultrarare_primary_is_presence_opportunity():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_115.json").read_text())
    p=x["primary_presence_opportunity"]
    assert "presence-cell" in p["estimand"]
    assert p["favourable_direction"]=="negative"
    assert p["minimum_presence_blocks"]==10
    assert "95% block-bootstrap upper bound < 0" in p["support"]

def test_secondaries_cannot_rescue_primary():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_115.json").read_text())
    assert x["secondary_absence_signature"]["may_rescue_primary"] is False
    assert x["secondary_external_isolation_attenuation"]["may_rescue_primary"] is False
    assert x["secondary_source_support"]["may_rescue_primary"] is False
    assert x["secondary_topology_specificity"]["may_rescue_primary"] is False

def test_router_decodes_exactly_ultrarare_layer():
    s=(ROOT/"scripts/run_global_mammals_ultrarare_response_v1_115.py").read_text()
    assert "len(universe)!=529" in s
    assert "1<=int(r[\"pilot_presence\"])<=4" in s
    assert "len(picked)!=529" in s
    assert "decoded!=2182654" in s
    assert "heldout_non_ultrarare_values_decoded" in s
    assert "pilot_occurrence_values_decoded_during_run" in s

def test_scorer_contains_all_preregistered_estimands():
    s=(ROOT/"scripts/score_global_mammals_ultrarare_v1_115.py").read_text()
    assert "primary_presence_opportunity" in s
    assert "secondary_external_isolation_attenuation" in s
    assert "secondary_source_support" in s
    assert "secondary_topology_specificity" in s
    assert "actual_C_better_than_n_of_20_nulls_on_presence_metric" in s
    assert "secondary_results_may_rescue_primary" in s

def test_response_not_authorized_by_scoring_contract():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_115.json").read_text())
    assert x["execution_not_authorized_until"].startswith("successful v1.114")
    assert x["heldout_response_authorized_now"] is False
    assert x["response_firewall"]["same_lineage_rerun_after_first_decode"] is False
