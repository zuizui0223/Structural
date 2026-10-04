from pathlib import Path
import importlib.util,json,tempfile

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/validate_source_loss_leverage_intake_v1_126.py"
    spec=importlib.util.spec_from_file_location("intake",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def base_candidate():
    return {
      "candidate_id":"x",
      "system_name":"test",
      "taxon_scope":"mammals",
      "island_or_island_like_units":"islands",
      "ordered_wave_count":3,
      "wave_labels":["t0","t1","t2"],
      "stable_unit_ids":True,
      "stable_species_ids":True,
      "response_is_occupancy_or_presence_absence":True,
      "response_values_currently_unopened":True,
      "geometry_available_response_independently":True,
      "environment_or_habitat_available_response_independently":True,
      "sampling_effort_or_detection_metadata_available":True,
      "known_overlap_with_existing_structural_systems":"none"
    }

def test_three_wave_clean_candidate_qualifies_metadata_only():
    m=load_module()
    c=json.loads((ROOT/"development/source_loss_leverage_intake_contract_v1_126.json").read_text())
    out=m.adjudicate(base_candidate(),c)
    assert out["status"]=="QUALIFIED_METADATA_ONLY"
    assert out["response_access_authorized"] is False
    assert out["counts_as_empirical_evidence"] is False

def test_two_wave_candidate_stops():
    m=load_module()
    c=json.loads((ROOT/"development/source_loss_leverage_intake_contract_v1_126.json").read_text())
    x=base_candidate();x["ordered_wave_count"]=2;x["wave_labels"]=["t0","t1"]
    out=m.adjudicate(x,c)
    assert out["status"]=="STOP_TWO_WAVE"
    assert out["response_access_authorized"] is False

def test_exposed_future_response_stops():
    m=load_module()
    c=json.loads((ROOT/"development/source_loss_leverage_intake_contract_v1_126.json").read_text())
    x=base_candidate();x["response_values_currently_unopened"]=False
    out=m.adjudicate(x,c)
    assert out["status"]=="STOP_RESPONSE_EXPOSED"

def test_same_structural_response_stops():
    m=load_module()
    c=json.loads((ROOT/"development/source_loss_leverage_intake_contract_v1_126.json").read_text())
    x=base_candidate();x["known_overlap_with_existing_structural_systems"]="same response"
    out=m.adjudicate(x,c)
    assert out["status"]=="STOP_NONINDEPENDENT_RESPONSE"

def test_missing_geometry_stops():
    m=load_module()
    c=json.loads((ROOT/"development/source_loss_leverage_intake_contract_v1_126.json").read_text())
    x=base_candidate();x["geometry_available_response_independently"]=False
    out=m.adjudicate(x,c)
    assert out["status"]=="STOP_NO_GEOMETRY"

def test_contract_forbids_outcome_based_candidate_selection():
    x=json.loads((ROOT/"development/source_loss_leverage_intake_contract_v1_126.json").read_text())
    joined="\n".join(x["anti_selection"])
    assert "published results suggest a favourable leverage effect" in joined
    assert "inspect t2 occupancy" in joined
    assert "connectivity coefficient" in joined
