from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v142_authorizes_t0_t1_but_not_t2():
    x=json.loads((ROOT/"development/bala_preoutcome_feature_execution_request_v1_142.json").read_text())
    assert x["t0_t1_semantic_access_authorized"] is True
    assert x["t2_semantic_access_authorized"] is False
    assert x["candidate_effect_scoring_authorized"] is False
    assert x["one_shot"] is True

def test_v142_binds_exact_temporal_artifact():
    x=json.loads((ROOT/"development/bala_preoutcome_feature_execution_request_v1_142.json").read_text())
    t=x["temporal_firewall"]
    assert t["artifact_id"]==11326825183
    assert t["preoutcome_t0_t1_sha256"]=="1ff9708dc7b182a2df27ebdd4f7b394bee71867abf4c79b3e5a9387935b9c016"
    assert t["sealed_t2_sha256"]=="cf320dca37f17641219f80fc98b302994c9062c5a89dda01419e57cb7800d967"

def test_workflow_opens_no_t2_semantics():
    s=(ROOT/".github/workflows/bala-preoutcome-features-v1_142.yml").read_text()
    assert "confirmatory_t0_t1_rows.sealed.tsv" in s
    assert "build_bala_preoutcome_features_v1_140.py" in s
    assert "confirmatory_t2_rows.sealed.tsv" in s
    assert "t2_occurrence_values_opened" in s
    assert "score_bala_source_loss_t2" not in s

def test_pre_t2_gate_is_not_relaxed():
    p=json.loads((ROOT/"development/bala_preoutcome_feature_protocol_v1_140.json").read_text())
    g=p["pre_t2_gate"]
    assert g["minimum_taxonomically_eligible_confirmatory_taxa"]==30
    assert g["minimum_exactly_one_loss_taxa"]==10
    assert g["minimum_exactly_one_loss_target_rows"]==30
    assert g["minimum_distinct_E_i_values"]==3
    assert g["minimum_prefeature_estimable_taxon_folds"]==10
