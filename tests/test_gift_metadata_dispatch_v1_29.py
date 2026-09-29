from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "development/gift_metadata_dispatch_request_v1_29.json"
WORKFLOW = ROOT / ".github/workflows/gift-metadata-dispatcher-v1_29.yml"
TARGET = ROOT / ".github/workflows/gift-metadata-freeze-v0_89.yml"
CONTRACT = ROOT / "development/gift_metadata_freeze_contract_v0_89.json"
ELIGIBILITY = ROOT / "development/gift_metadata_eligibility_contract_v1_28.json"


def test_dispatch_request_targets_exact_frozen_metadata_workflow_only():
    req = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert req["status"] == "REQUEST_FROZEN_GIFT_METADATA_V089_DISPATCH"
    assert req["target_workflow"] == (
        ".github/workflows/gift-metadata-freeze-v0_89.yml"
    )
    assert req["target_ref"] == "main"
    assert req["species_composition_authorized"] is False
    assert req["species_richness_authorized"] is False
    assert req["checklist_contents_authorized"] is False
    assert req["source_pool_features_authorized"] is False
    assert req["counts_as_empirical_evidence"] is False
    assert req["fresh_system_denominator_contribution"] == 0
    assert req["one_shot"] is True


def test_dispatcher_only_emits_workflow_dispatch_and_never_queries_gift():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "gift-metadata-freeze-v0_89.yml/dispatches" in text
    assert '"ref": "main"' in text
    assert "GIFT_checklists" not in text
    assert "gift.uni-goettingen.de" not in text
    lowered = text.lower()
    prefix = lowered.split("validate one-shot metadata-only request", 1)[0]
    assert "species" not in prefix


def test_target_v089_is_still_metadata_only():
    text = TARGET.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "freeze_gift_metadata_v0_89.R" in text
    r = (ROOT / "scripts/freeze_gift_metadata_v0_89.R").read_text(
        encoding="utf-8"
    )
    assert "list_set_only = TRUE" in r
    assert "remove_overlap = FALSE" in r
    assert "species composition was returned despite list_set_only=TRUE" in r


def test_program_and_eligibility_keep_species_response_sealed():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    eligibility = json.loads(ELIGIBILITY.read_text(encoding="utf-8"))
    assert contract["counts_as_empirical_evidence"] is False
    assert contract["pilot_response_authorized"] is False
    assert contract["confirmatory_response_authorized"] is False
    assert eligibility["response_access"]["species_composition_allowed"] is False
    assert eligibility["response_access"]["species_richness_allowed"] is False
    assert eligibility["response_access"]["checklist_contents_allowed"] is False
    assert eligibility["species_response_authorized"] is False
