"""Synthetic/source-methods intake checks, no biological response."""
import json,copy,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from temporal_rescue_design_intake_v1_221 import summarize
def doc():
    return json.loads((ROOT/"development/temporal_rescue_source_design_v1_221.json").read_text())
def test_fixed_methods_design_only():
    r=summarize(doc())
    assert r["hopson"]["independent_metapopulations"]==14
    assert r["hopson"]["patch_rows_not_independent"]==210
    assert r["green"]["unique_network_structures_at_most"]==16
    assert r["prospectively_eligible_systems_added"]==0
    assert r["source_outcome_cells_read"]==0
def test_cannot_promote_mammal_or_pilot():
    for key in ("empirical_admitted","pilot_opened","confirmatory_opened"):
        d=doc();d["gate_contract"][key]=True
        with pytest.raises(ValueError):summarize(d)
def test_pseudoreplication_and_source_reuse_guard():
    d=doc();d["sources"][0]["independent_metapopulation_replicates"]=210
    with pytest.raises(ValueError):summarize(d)
    d=doc();d["sources"][1]["unambiguous_independent_network_topology_units_at_most"]=88
    with pytest.raises(ValueError):summarize(d)
def test_nonfresh_published_gate():
    d=doc();d["sources"][0]["preliminary_design_decision"]="CONFIRMATORY"
    with pytest.raises(ValueError):summarize(d)
    d=doc();d["sources"][1]["raw_source_rows_opened"]=True
    with pytest.raises(ValueError):summarize(d)
