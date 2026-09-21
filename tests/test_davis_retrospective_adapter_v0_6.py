from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_davis_adapter_is_permanently_retrospective():
    cfg = json.loads(
        (ROOT / "development/connectivity_retrospective_davis_schema_contract_v0_6.json").read_text()
    )
    assert cfg["counts_as_fresh_evidence"] is False
    assert cfg["response_exposure"]["response_blind_admission_status"] == "STOP"
    assert cfg["response_exposure"]["publication_abstract_exposes_results"] is True


def test_davis_adapter_keeps_geometry_process_and_endpoint_separate():
    cfg = json.loads(
        (ROOT / "development/connectivity_retrospective_davis_schema_contract_v0_6.json").read_text()
    )
    ladder = cfg["declared_ladder"]
    assert "structural_geometry" in ladder
    assert ladder["process_model"]["operator"] == "pollinator_mediated_pollen_flow"
    assert set(ladder["realized_endpoint"]["endpoint_candidates"]) == {
        "h_Pollen_Pool", "Outcrossing", "Biparental_Inbreeding"
    }


def test_patch_to_population_join_is_not_assumed():
    cfg = json.loads(
        (ROOT / "development/connectivity_retrospective_davis_schema_contract_v0_6.json").read_text()
    )
    identifiers = cfg["identifiers"]
    assert identifiers["primary_population_key"] == "Pop"
    assert identifiers["hummingbird_key"] == "Patch"
    assert identifiers["patch_to_pop_mapping_status"] == "must_verify_from_source_files_before_join"


def test_published_rankings_are_forbidden_for_candidate_selection():
    cfg = json.loads(
        (ROOT / "development/connectivity_retrospective_davis_schema_contract_v0_6.json").read_text()
    )
    stops = cfg["adapter_hard_stops"]
    assert "do not use published model rankings to select the primary process metric" in stops
    assert "do not use manuscript Output/Tables to choose candidate features" in stops
