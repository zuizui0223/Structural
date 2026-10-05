from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_preoutcome_freeze_passed_all_gates_without_t2():
    x=json.loads((ROOT/"development/bala_preoutcome_feature_freeze_v1_143.json").read_text())
    assert x["pre_t2_gate"]["exactly_one_loss_taxa"]==20
    assert x["pre_t2_gate"]["exactly_one_loss_target_rows"]==64
    assert x["pre_t2_gate"]["distinct_E_i_values"]==53
    assert x["pre_t2_gate"]["prefeature_estimable_taxon_folds"]==20
    assert x["pre_t2_gate"]["all_gate_checks_passed"] is True
    assert x["response_boundary"]["t2_occurrence_values_opened"]==0

def test_v143_is_irreversible_one_shot_t2_authorization():
    x=json.loads((ROOT/"development/bala_t2_execution_request_v1_143.json").read_text())
    assert x["t2_semantic_access_authorized"] is True
    assert x["noneligible_t2_quantity_decode_authorized"] is False
    assert x["model_refit_or_feature_change_after_t2_authorized"] is False
    assert x["same_lineage_rerun_after_first_eligible_t2_quantity_decode"] is False
    assert x["one_shot"] is True

def test_v143_binds_exact_frozen_t2_and_features():
    x=json.loads((ROOT/"development/bala_t2_execution_request_v1_143.json").read_text())
    assert x["sealed_t2"]["t2_surface_sha256"]=="cf320dca37f17641219f80fc98b302994c9062c5a89dda01419e57cb7800d967"
    assert x["preoutcome_features"]["features_sha256"]=="0f0d4601ff4c06757df874f4d687699bb8084bc7bcf82ec99ea05cd917e469fd"
    assert x["preoutcome_features"]["fold_manifest_sha256"]=="6af472fb97f1472c00b7b3ee6b69a5eb098104c5e5c60ecc94029583d32c042f"
    assert x["preoutcome_features"]["fold_standardization_sha256"]=="ea69f0d3ab5704caf2f34729ca77919d074f301096d8d023deee10333d3e965b"

def test_workflow_preserves_terminal_result_even_if_nonestimable():
    s=(ROOT/".github/workflows/bala-source-loss-score-v1_143.yml").read_text()
    assert "set +e" in s
    assert "Upload terminal BALA result bundle" in s
    assert "if: always()" in s
    assert "Fail closed if scorer stopped" in s
    assert "rerun_authorized" in s

def test_workflow_uses_frozen_v141_scorer_only():
    s=(ROOT/".github/workflows/bala-source-loss-score-v1_143.yml").read_text()
    assert "score_bala_source_loss_t2_v1_141.py" in s
    assert "--expected-t2-sha cf320dca37f17641219f80fc98b302994c9062c5a89dda01419e57cb7800d967" in s
    assert "prepare_dryad_token" not in s
