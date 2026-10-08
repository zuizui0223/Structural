import importlib.util
import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"scripts/audit_kelp_temporal_independence_v1_205.py"
LEDGER=ROOT/"development/kelp_temporal_source_ontology_v1_205.json"

def module():
    spec=importlib.util.spec_from_file_location("kelp_v205",SRC)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_published_kelp_lineage_stops_fresh_mechanism_claims():
    x=json.loads(LEDGER.read_text(encoding="utf-8"))
    r=module().classify(x)
    assert r["fresh_469_patch_forecast"]=="STOP_FUTURE_DEFINED_GEOMETRY"
    assert r["fresh_117_cell_forecast"]=="STOP_BIOLOGICALLY_SELECTED_RISK_SET"
    assert r["independent_reproductive_failure"]=="STOP_CANOPY_DERIVED_PROXY"
    assert r["cross_grain_2017_2024"]=="STOP_NO_JOIN_CROSSWALK"
    assert r["biology_values_opened"]==0
    assert r["new_ecological_score"] is None

def test_repairs_are_hypothetical_and_not_reruns():
    old=json.loads(LEDGER.read_text(encoding="utf-8"))
    fake=deepcopy(old)
    fake["frozen_design"]["castorani"]["patch_definition_end_year"]=1995
    fake["frozen_design"]["castorani"]["independent_patch_fecundity_failure_measured"]=True
    fake["frozen_design"]["wanner"]["cutoff_specific_inclusion_proven"]=True
    r=module().classify(fake)
    for k in ("fresh_469_patch_forecast","fresh_117_cell_forecast","independent_reproductive_failure"):
        assert r[k]=="REQUIRE_OTHER_GATES"
    assert old["frozen_design"]["castorani"]["patch_definition_end_year"]==2011

def test_no_stale_biological_inference():
    x=json.loads(LEDGER.read_text(encoding="utf-8"))
    assert len(x["public_catalog_roles"])==3
    assert all(v["exact_DOI_version_verified"] is False for v in x["public_catalog_roles"])
    for v in ("raw_data_opened","original_mammal_response_reopened","source_file_headers_verified",
              "EDI_API_authenticated","cross_grain_patch_cell_crosswalk_verified",
              "manuscript_submission_authorized","original_results_changed","eBird_used"):
        assert x["evidence_boundaries"][v] is False
