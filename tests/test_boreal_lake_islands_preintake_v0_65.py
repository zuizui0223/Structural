from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
PRE=ROOT/"development/boreal_lake_islands_preintake_v0_65.json"
META=ROOT/"development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
STATUS=ROOT/"development/current_status_v0_65.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_65.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_boreal_candidate_is_preintake_and_response_sealed():
    x=load(PRE)

    assert x["status"]=="HOLD_safe_metadata_schema_and_transport_not_yet_frozen"
    assert x["source_identity"]["response_values_opened_by_structural"] is False
    assert x["v0_11_intake_authorized"] is False
    assert x["pilot_response_authorized"] is False
    assert x["confirmatory_response_authorized"] is False
    assert x["counts_as_empirical_evidence"] is False


def test_beetles_are_primary_and_secondaries_cannot_rescue():
    x=load(PRE)

    assert x["endpoint_scope"]["primary_taxon"]=="beetles"
    assert x["endpoint_scope"]["primary_species_count_reported"]==466
    assert x["endpoint_scope"]["primary_island_count_reported"]==42
    assert x["endpoint_scope"]["response_domain"]==["0","1"]
    assert x["endpoint_scope"]["whole_island_occupancy_claim_authorized"] is False
    assert all(y["may_rescue_primary"] is False for y in x["secondary_taxa"])


def test_exact_response_and_safe_file_identities_are_frozen():
    x=load(META)
    f=x["focal_files"]

    assert x["selected_version_id"]==422440
    assert x["selected_version_number"]==7
    assert x["file_content_requests"]==0
    assert x["response_values_opened"] is False
    assert f["beetles_speciesmatrix_presenceabsence.csv"]["sha256"] == (
        "01eef34863bfd49fdc68dfae0aec58766a6fcdd1234751a9c75824df9f038be0"
    )
    assert f["borealbirds_speciesmatrix_presenceabsence.csv"]["sha256"] == (
        "3838c39a7a94010569ce399a6b19e651f45fa60d0aef1793445dcb6c0b6e201c"
    )
    assert f["vascularplants_speciesmatrix_presenceabsence.csv"]["sha256"] == (
        "fa9bca793c58bf0a88e707c6841ede7513c4ea07662e4f3d6540088d5feea26d"
    )
    assert f["alpha_diversity_ALL_islands.csv"]["sha256"] == (
        "f63b37b3c4c9d5453c53b0b565c4bfb7b8485e017f257fbeea663b20cbf6bddf"
    )


def test_v055_binding_does_not_restore_remote_switch():
    x=load(PRE)
    binding=x["v0_55_binding"]

    assert binding["parent"] == (
        "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json"
    )
    assert binding["extreme_isolation_interaction_required"] is False
    assert x["reference_template"]["primary_contrast"]=="C_minus_R3 heldout log loss"
    assert x["reference_template"]["favourable_direction"]=="negative"


def test_fire_and_habitat_are_required_before_source_pool_interpretation():
    x=load(PRE)
    reference=x["reference_template"]

    assert "time_since_fire_beetles" in reference["R0"]
    assert "log10area" in reference["R1_add"]
    assert "buffer5000 external isolation" in reference["R1_add"]
    assert any("training-only global occupied breadth" in s for s in reference["R3_add"])
    assert any("internal source continuity" in s for s in reference["C_add"])
    assert any("fire history/habitat" in s for s in x["known_claim_boundaries"])


def test_current_status_keeps_fresh_denominator_zero():
    s=load(STATUS)
    p=load(PRIORITY)

    assert s["fresh_empirical_state"]["active_candidates"]==[]
    assert s["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert s["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    assert s["pristine_global_mammal_hold"]["response_opened"] is False
    assert s["boreal_lake_island_preintake"]["response_values_opened"] is False
    assert s["boreal_lake_island_preintake"]["counts_as_active_fresh_candidate"] is False
    assert p["fresh_active_empirical_candidate"] is None
    assert p["fresh_confirmatory_eligible_count"]==0
