"""v1.317: original evidence identity checks on frozen aggregates only."""
import copy
import json
import math
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_between_within_sourcefree_audit_v1_317 import audit


def fixture():
    d=json.loads((ROOT/"development/bala_within_campaign_detection_original_result_freeze_v1_316.json").read_text())
    c=json.loads((ROOT/"development/bala_within_period_excess_sourcefree_protocol_v1_317.json").read_text())
    return d,c


def test_seven_islands_exceed_same_campaigned_split_sampling_for_two_guilds():
    d,c=fixture()
    r=audit(d,c)
    assert r["status"]=="ORIGINAL_SOURCE_FREE_SEVEN_ISLAND_TEMPORAL_EXCESS_VALIDATED"
    assert r["source_original_independent_transects"]==29
    assert r["source_original_island_contexts"]==7
    a=r["main_pitfall"]["araneae"]
    b=r["main_pitfall"]["coleoptera"]
    assert a["physical_eligible_transects"]==29
    assert b["physical_eligible_transects"]==26
    assert a["physical_sites_positive_across_minus_within_sorensen"]==26
    assert b["physical_sites_positive_across_minus_within_sorensen"]==25
    assert a["islands_positive_excess_sorensen"]==7
    assert b["islands_positive_excess_sorensen"]==7
    assert a["islands_positive_excess_simpson"]==7
    assert b["islands_positive_excess_simpson"]==7
    assert math.isclose(a["island_equal_excess_sorensen"],0.19077547226911137,abs_tol=1e-13)
    assert math.isclose(b["island_equal_excess_sorensen"],0.22120879931840728,abs_tol=1e-13)
    assert math.isclose(a["island_equal_excess_simpson_replacement"],0.16765006928697404,abs_tol=1e-13)
    assert math.isclose(b["island_equal_excess_simpson_replacement"],0.2448435144367684,abs_tol=1e-13)
    assert 0.60<a["ratio_within_period_to_between_period_sorensen"]<0.61
    assert 0.65<b["ratio_within_period_to_between_period_sorensen"]<0.66
    assert r["islands_beetle_excess_sorensen_greater_than_spider_excess"]==5


def test_source_free_limits_and_secondary_beating_stop_are_immutable():
    d,c=fixture()
    r=audit(d,c)
    assert r["secondary_canopy_beetle_scientifically_stopped"]
    assert r["original_source_has_not_been_reopened_by_this_audit"]
    assert r["source_original_9_partitions_pseudoreplicates_not_independent"]
    assert r["within_sample_split_is_not_species_detection_probability_model"]
    assert r["biogeographic_immigration_or_extinction_not_observed"]
    assert r["no_causal_drivers_or_invasion_inferred"]
    assert r["v1_314_original_biological_workflow_SEALED"]
    assert r["v1_316_original_biological_workflow_SEALED"]
    assert r["new_confirmatory_systems"]==0
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "eventID" not in json.dumps(r)
    assert "scientificName" not in json.dumps(r)


def test_tampered_original_site_support_or_source_sha_fails_closed():
    d,c=fixture()
    x=copy.deepcopy(d)
    x["pitfall"]["coleoptera"]["per_island"]["fai"]["n"]+=1
    with pytest.raises(ValueError,match="source site supports"):
        audit(x,c)
    x=copy.deepcopy(d)
    x["original"]["v316_original_inner_JSON_SHA256"]="tampered"
    with pytest.raises(ValueError,match="source identity"):
        audit(x,c)
    x=copy.deepcopy(d)
    x["pitfall"]["araneae"]["per_island"]["ter"]["excess_sorensen"]*=0.5
    with pytest.raises(ValueError,match="island average"):
        audit(x,c)


def test_original_no_data_rescue_no_canopy_beetle_score():
    d,c=fixture()
    x=copy.deepcopy(d)
    x["secondary_beating"]["coleoptera"]["eligible_sites"]=29
    with pytest.raises(ValueError,match="secondary STOP"):
        audit(x,c)
    x=copy.deepcopy(d)
    x["limits"]["v316_original_taxon_workflow"]="AUTO_RERUN"
    with pytest.raises(ValueError,match="source seal"):
        audit(x,c)
