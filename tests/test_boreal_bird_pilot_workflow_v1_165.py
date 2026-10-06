from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/boreal-bird-pilot-v1_165.yml"

def test_workflow_is_request_triggered_one_shot_and_raw_response_not_uploaded():
    s=WF.read_text()
    assert "development/boreal_bird_pilot_execution_request_v1_165.json" in s
    assert 'test "$GITHUB_RUN_ATTEMPT" = "1"' in s
    assert "pilot_occurrence_cells_authorized" in s
    assert "confirmatory_occurrence_cells_authorized" in s
    assert "rm -rf build/boreal_bird_v165/raw" in s
    assert 'assert not any(root.rglob("*.csv"))' in s
    assert "borealbirds_speciesmatrix_presenceabsence.csv" not in s.split(
        "Upload consumed pilot audit bundle",1
    )[1]

def test_workflow_verifies_all_pre_response_freezes_before_transport():
    s=WF.read_text()
    verify=s.index("Verify pre-response contracts")
    transport=s.index("Transport exact bird response bytes")
    pilot=s.index("Consume bird pilot exactly once")
    assert verify < transport < pilot
    assert 't["null_ensemble"]["unique_topologies"]==20' in s
    assert 'm["response_boundary"]["bird_confirmatory_response_authorized"] is False' in s
