from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "development/macro_dual_isolation_preregistration_v0_90.json"
MAMMAL = ROOT / "development/global_mammals_authenticated_routing_contract_v0_90.json"
GIFT = ROOT / "development/gift_metadata_freeze_contract_v0_90.json"
STATUS = ROOT / "development/current_status_v0_90.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_90.json"
MAMMAL_WF = ROOT / ".github/workflows/global-mammals-routing-v0_90.yml"
GIFT_WF = ROOT / ".github/workflows/gift-metadata-freeze-v0_90.yml"
GIFT_SCRIPT = ROOT / "scripts/freeze_gift_metadata_v0_90.R"
MAMMAL_SCRIPT = ROOT / "scripts/fetch_global_mammal_routing_ids_v0_90.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_mammal_module():
    spec = importlib.util.spec_from_file_location("mammal_v090", MAMMAL_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_macro_core_is_two_taxon_and_boreal_is_supplementary():
    x = load(PREREG)
    systems = {(s["candidate_id"], s["taxon"]) for s in x["primary_systems"]}
    assert systems == {
        ("global_island_native_mammals_barreto_2024", "Mammalia"),
        ("gift_native_angiosperm_islands_v3_2", "Angiospermae"),
    }
    assert x["boreal_role"] == "supplementary_local_contrast_only_not_macro_core"
    assert set(x["discovery_only_not_confirmatory"]) == {
        "A-Islands",
        "Tanzania",
        "zenodo_318_island_mammals_2024",
    }


def test_r3_contains_regional_pool_and_all_source_features_are_leave_block_out():
    x = load(PREREG)
    r3 = x["reference_ladder"]["R3_add"]
    assert "training-only species_x_regional_pool membership/prevalence" in r3
    firewall = x["leakage_firewall"]
    assert firewall["source_features_leave_block_out"] is True
    assert firewall["no_full_dataset_source_features"] is True
    assert firewall["heldout_block_may_not_contribute_as_source"] is True


def test_mammal_route_supersedes_only_transport_retry_boundary():
    x = load(MAMMAL)
    assert x["supersedes_transport_boundary"].endswith("v0_64.json")
    assert "authenticated" in x["status"]
    d = x["dryad"]
    assert d["version_id"] == 299966
    assert d["size_bytes"] == 60486843
    assert d["sha256"] == (
        "32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6"
    )
    sem = x["semantic_firewall"]
    assert sem["expected_data_rows"] == 5592
    assert sem["species_header_fields_opened"] == 0
    assert sem["occurrence_cells_opened"] == 0


def test_numeric_id_noncollision_is_not_treated_as_independence():
    x = load(PREREG)["independence_gate"]
    assert x["numeric_ID_collision_check"] == "diagnostic_only"
    assert x["numeric_ID_noncollision_is_not_proof_of_independence"] is True
    assert "response-independent" in x["required_final_gate"]
    assert x["overlapping_islands_action"].startswith("exclude")


def test_mammal_first_field_parser_opens_only_field_one():
    module = load_mammal_module()
    assert module.first_csv_field_only(b'123,0,1,0\r\n') == b"123"
    assert module.first_csv_field_only(b'"001.0",0,1\n') == b"001.0"
    assert module.first_csv_field_only(b'"A""B",0,1\n') == b'A"B'
    assert module.normalize_routing_id("001.000") == "1"
    assert module.normalize_routing_id(" island-x ") == "island-x"


def test_mammal_workflow_is_manual_main_only_and_raw_response_never_uploaded():
    text = MAMMAL_WF.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in text
    assert "prepare_dryad_token_v0_73.py" in text
    assert "fetch_global_mammal_routing_ids_v0_90.py" in text
    assert "rm -rf build/global_mammals_v090/raw" in text
    upload = text[text.index("Upload routing-only artifact"):]
    assert "Appendix_1_presence_absence.csv" not in upload
    assert "build/global_mammals_v090/raw" not in upload


def test_gift_contract_and_script_are_metadata_only():
    x = load(GIFT)
    call = x["call"]
    assert call["taxon_name"] == "Angiospermae"
    assert call["floristic_group"] == "native"
    assert call["geo_type"] == "Island"
    assert call["suit_geo"] is True
    assert call["list_set_only"] is True
    assert call["GIFT_version"] == "3.2"
    assert x["database"]["database_version"] == "3.2"
    assert x["database"]["package_version"] == "1.3.4"

    script = GIFT_SCRIPT.read_text(encoding="utf-8")
    assert 'list_set_only = TRUE' in script
    assert 'GIFT_version = "3.2"' in script
    assert 'res$lists' in script
    assert 'sealed_species_placeholder' in script
    assert "GIFT_richness" not in script


def test_gift_workflow_is_manual_main_only():
    text = GIFT_WF.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in text
    assert "any::GIFT@1.3.4" in text
    assert "freeze_gift_metadata_v0_90.R" in text


def test_v090_keeps_response_and_confirmatory_denominator_closed():
    status = load(STATUS)
    priority = load(PRIORITY)
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    assert status["global_mammals"]["response_occurrence_values_opened"] is False
    assert status["gift_plants"]["species_composition_requested"] is False
    assert priority["fresh_confirmatory_eligible_count"] == 0
    assert priority["boreal"]["role"] == "supplementary_local_contrast_only"
    assert priority["boreal"]["may_not_block_macro_progress"] is True
