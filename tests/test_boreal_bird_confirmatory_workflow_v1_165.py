from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/boreal-bird-confirmatory-v1_165.yml"

def test_confirmatory_workflow_is_one_shot_and_hash_bound():
    s=WF.read_text()
    assert 'test "$GITHUB_RUN_ATTEMPT" = "1"' in s
    assert 'git rev-list --count HEAD -- "$REQUEST"' in s
    assert 'committed_input_sha256' in s
    assert 'irreversible_confirmatory_open"] is True' in s
    assert 'pilot_response_may_be_reopened"] is False' in s
    assert 'nonfixed_confirmatory_species_may_be_opened"] is False' in s

def test_confirmatory_workflow_deletes_raw_before_upload():
    s=WF.read_text()
    delete_at=s.index("Delete raw response bytes before artifact handling")
    upload_at=s.index("Upload result-only audit bundle")
    assert delete_at < upload_at
    upload=s[upload_at:]
    assert "raw/" not in upload
    assert "confirmatory_result.json" in upload

def test_confirmatory_workflow_uses_frozen_prediction_surface():
    s=WF.read_text()
    assert "development/boreal_bird_confirmatory_predictions_v1_164.csv" in s
    assert "development/boreal_bird_preconfirmatory_freeze_v1_164.json" in s
    assert "development/boreal_bird_pilot_snapshot_v1_163.json" in s
    assert "score_boreal_bird_confirmatory_v1_165.py" in s
