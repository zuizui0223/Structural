from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
PRE=ROOT/"development/global_island_mammals_preintake_v0_1.json"
META=ROOT/"development/global_island_mammals_dryad_metadata_result_v0_1.json"
STATUS=ROOT/"development/current_status_v0_46.json"


def load(path: Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_global_mammals_remain_response_sealed_preintake():
    pre=load(PRE)
    assert pre["status"].startswith("HOLD_")
    assert pre["source_identity"]["response_file_downloaded_by_structural"] is False
    assert pre["source_identity"]["response_values_opened_by_structural"] is False
    assert pre["v0_11_intake_authorized"] is False
    assert pre["pilot_response_authorized"] is False
    assert pre["confirmatory_response_authorized"] is False
    assert pre["counts_as_empirical_evidence"] is False


def test_dryad_file_identities_are_exact_and_content_unopened():
    x=load(META)
    files={row["path"]:row for row in x["files"]}

    assert x["selected_version_number"]==6
    assert x["selected_version_last_modification_date"]=="2024-06-17"
    assert x["file_content_http_requests"]==0
    assert x["response_values_opened"] is False
    assert files["Appendix_1_presence_absence.csv"]["digest"]==(
        "32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6"
    )
    assert files["Appendix_2-dryad.xlsx"]["digest"]==(
        "fdcfc92bfa67e1ccf4d468fe2c7222bcb5919a1bce56d272b19d42525c234960"
    )


def test_response_domain_and_claim_population_are_frozen():
    pre=load(PRE)

    assert pre["response_domain"]["values"]==["0","1"]
    assert pre["response_domain"]["categorical_domain_is_explicit_before_response_access"] is True
    assert pre["public_metadata_basis"]["zero_mammal_islands_excluded"] is True
    assert pre["temporal_semantics"]["contemporary_colonization_claim_authorized"] is False
    assert pre["temporal_semantics"]["rescue_effect_claim_authorized"] is False


def test_mixed_appendix2_cannot_be_opened_before_column_firewall():
    pre=load(PRE)

    assert pre["required_preintake_firewall"]["Appendix_2-dryad.xlsx"].startswith("mixed_")
    assert "Richness_*" in pre["appendix2_forbidden_response_derived_columns_pattern"]
    assert "SIE_*" in pre["appendix2_forbidden_response_derived_columns_pattern"]
    assert "pSIE*" in pre["appendix2_forbidden_response_derived_columns_pattern"]
    assert pre["next_action"].startswith("resolve current Dryad file IDs")


def test_v046_does_not_promote_preintake_candidate():
    status=load(STATUS)
    reg=load(ROOT/status["authoritative_empirical_registry"]["path"])
    pre=status["hypothesis_driven_preintake_candidate"]

    assert reg["active_empirical_candidates"]==[]
    assert status["confirmatory_eligible_systems"]==[]
    assert status["confirmatory_eligible_count"]==0
    assert pre["counts_as_active_empirical_candidate"] is False
    assert pre["counts_as_confirmatory_evidence"] is False
    assert pre["response_values_opened"] is False
