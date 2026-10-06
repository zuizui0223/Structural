from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/boreal-bird-pilot-v1_163.yml"

def test_bird_pilot_workflow_is_one_shot_and_confirmatory_sealed():
    s=WF.read_text()
    assert 'test "$GITHUB_RUN_ATTEMPT" = "1"' in s
    assert 'git rev-list --count HEAD -- "$REQUEST"' in s
    assert 'confirmatory_response_may_be_opened"] is False' in s
    assert 'raw_response_may_be_uploaded"] is False' in s
    assert 'ebird_enabled"] is False' in s

def test_bird_pilot_workflow_deletes_raw_response_before_upload():
    s=WF.read_text()
    assert "rm -rf build/boreal_bird_v163/raw" in s
    upload=s.split("Upload pilot and preconfirmatory audit bundle only",1)[1]
    assert "raw/" not in upload
    assert "pilot_snapshot.json" in upload
    assert "execution_receipt.json" in upload
    assert "preconfirmatory_receipt.json" in upload
    assert "confirmatory_predictions.csv" in upload

def test_bird_pilot_workflow_uses_exact_transport_and_v163_runner():
    s=WF.read_text()
    assert "fetch_boreal_bird_response_v1_163.py" in s
    assert "run_boreal_bird_pilot_v1_163.py" in s
    assert "prepare_dryad_token_v0_73.py" in s


def test_preconfirmatory_freeze_runs_only_after_raw_response_deletion():
    s=WF.read_text()
    delete_at=s.index("Delete raw bird bytes before artifact handling")
    freeze_at=s.index("Freeze all actual and null predictions after clean pilot")
    assert delete_at < freeze_at
    assert "freeze_boreal_bird_preconfirmatory_v1_164.py" in s
    assert "PRECONFIRM_EXIT_CODE" in s
