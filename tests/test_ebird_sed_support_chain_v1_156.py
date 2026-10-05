from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_ebird_sed_support_chain_v1_156.py"
    spec=importlib.util.spec_from_file_location("eb156",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_chain_contract_requires_same_sed_bytes():
    x=json.loads((ROOT/"development/ebird_sed_support_chain_contract_v1_156.json").read_text())
    assert x["status"]=="RESPONSE_UNOPENED_SAME_BYTE_SED_AUDIT_CHAIN_FROZEN"
    assert x["success_requirements"]["same_SED_sha256_before_between_after"] is True
    assert x["response_access_authorized"] is False
    assert x["counts_as_empirical_source_loss_evidence"] is False

def test_child_receipt_validation_accepts_only_closed_response_boundaries():
    m=load_module()
    c=json.loads((ROOT/"development/ebird_sed_support_chain_contract_v1_156.json").read_text())
    audit={
      "status":"SED_SCHEMA_AND_COVERAGE_AUDIT_COMPLETE_RESPONSE_INDEPENDENTLY",
      "detected_protocol_schema":"modern_v1_16_plus",
      "species_headers_seen":0,"species_values_read":0,"species_nondetections_constructed":0,
      "response_access_authorized":False
    }
    survey={
      "status":"RESPONSE_INDEPENDENT_ISLAND_YEAR_SURVEY_SURFACE_FROZEN",
      "detected_protocol_schema":"modern_v1_16_plus",
      "species_identity_read":False,"species_detection_read":False,
      "species_nondetection_constructed":False,"annual_species_occupancy_constructed":False,
      "source_loss_events_constructed":False,"response_access_authorized":False
    }
    assert m.validate_receipts(audit,survey,c) is True

def test_child_receipt_validation_rejects_species_access():
    m=load_module()
    c=json.loads((ROOT/"development/ebird_sed_support_chain_contract_v1_156.json").read_text())
    audit={
      "status":"SED_SCHEMA_AND_COVERAGE_AUDIT_COMPLETE_RESPONSE_INDEPENDENTLY",
      "detected_protocol_schema":"modern_v1_16_plus",
      "species_headers_seen":0,"species_values_read":1,"species_nondetections_constructed":0,
      "response_access_authorized":False
    }
    survey={
      "status":"RESPONSE_INDEPENDENT_ISLAND_YEAR_SURVEY_SURFACE_FROZEN",
      "detected_protocol_schema":"modern_v1_16_plus",
      "species_identity_read":False,"species_detection_read":False,
      "species_nondetection_constructed":False,"annual_species_occupancy_constructed":False,
      "source_loss_events_constructed":False,"response_access_authorized":False
    }
    try:
        m.validate_receipts(audit,survey,c)
    except m.Stop:
        pass
    else:
        raise AssertionError("species-value access should stop the chain")

def test_runner_hashes_sed_before_between_and_after():
    s=(ROOT/"scripts/run_ebird_sed_support_chain_v1_156.py").read_text()
    assert "sed0=sha256(args.sed_file)" in s
    assert "sed1=sha256(args.sed_file)" in s
    assert "sed2=sha256(args.sed_file)" in s
    assert "SED bytes changed during metadata audit" in s
    assert "SED bytes changed during island-year build" in s

def test_priority_has_no_species_effect_before_sed_support():
    x=json.loads((ROOT/"development/structural_active_priority_v1_156.json").read_text())
    assert x["confirmatory_lane"]["status"]=="HOLD_OFFICIAL_SAMPLING_EVENT_DATA_NOT_PRESENT"
    assert "no species effect" in x["next_scientific_event"]
    assert "open Dryad eBird observed-species rows" in "\n".join(x["do_not"])
