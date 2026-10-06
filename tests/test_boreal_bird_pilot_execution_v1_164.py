from pathlib import Path
import csv
import hashlib
import io
import json
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/run_boreal_19island_bird_pilot_v1_164.py"
AUTH=ROOT/"development/boreal_19island_bird_pilot_authorization_v1_163.json"
TOPOLOGY=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
REQUEST=ROOT/"development/boreal_19island_bird_pilot_execution_request_v1_164.json"
WORKFLOW=ROOT/".github/workflows/boreal-19island-bird-pilot-v1_164.yml"


def load_runner():
    spec=importlib.util.spec_from_file_location("bird164",RUNNER)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def matrix(pattern):
    auth=json.loads(AUTH.read_text())
    species=[f"bird_{i:02d}" for i in range(54)]
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["Island",*species])
    pilot=auth["pilot_islands"]
    pidx={x:i for i,x in enumerate(pilot)}
    for island in auth["full_source_island_order"]:
        if island in pidx:
            i=pidx[island]; vals=[]
            for j in range(54):
                n=pattern(j)
                vals.append("1" if n and i<n else "0")
        else:
            vals=["OPAQUE_CONFIRMATORY_OR_EXCLUDED"]*54
        w.writerow([island,*vals])
    return out.getvalue().encode()


def auth_for_raw(m,raw):
    a=json.loads(AUTH.read_text())
    a["response_file"]["size_bytes"]=len(raw)
    a["response_file"]["sha256"]=hashlib.sha256(raw).hexdigest()
    a["topology_parent"]["bird_response_sha256"]=a["response_file"]["sha256"]
    a.pop("authorization_fingerprint",None)
    a["authorization_fingerprint"]=m.canonical_sha256(a)
    return a


def test_qualified_synthetic_pilot_consumes_once_and_stores_no_confirmatory_values():
    m=load_runner()
    raw=matrix(lambda j: 2 if j<4 else 3 if j<8 else 4 if j<12 else 0)
    auth=auth_for_raw(m,raw)
    topology=json.loads(TOPOLOGY.read_text())
    # Synthetic response identity is permitted only inside this unit test.
    topology=dict(topology);topology["parents"]=dict(topology["parents"])
    topology["parents"]["bird_response_sha256"]=auth["response_file"]["sha256"]
    result,snapshot=m.execute(auth,topology,raw)
    assert result["status"]=="BIRD_PILOT_QUALIFIED_TO_FREEZE_PREDICTIONS"
    assert result["authorization_consumed"] is True
    assert result["bird_pilot_opened"] is True
    assert result["fixed_species_count"]==12
    assert result["distinct_pilot_occupancy_counts"]==[2,3,4]
    assert result["confirmatory_target_values_parsed"]==0
    assert result["excluded_target_values_parsed"]==0
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert snapshot["qualified_for_prediction_freeze"] is True
    assert snapshot["confirmatory_occurrence_values_stored"] is False
    assert snapshot["excluded_occurrence_values_stored"] is False


def test_scientific_gate_failure_is_terminal_without_threshold_rescue():
    m=load_runner()
    raw=matrix(lambda j: 2 if j<8 else 0)
    auth=auth_for_raw(m,raw)
    topology=json.loads(TOPOLOGY.read_text())
    topology=dict(topology);topology["parents"]=dict(topology["parents"])
    topology["parents"]["bird_response_sha256"]=auth["response_file"]["sha256"]
    result,snapshot=m.execute(auth,topology,raw)
    assert result["status"]=="BIRD_PILOT_TERMINAL_ESTIMABILITY_STOP"
    assert result["authorization_consumed"] is True
    assert result["bird_pilot_opened"] is True
    assert result["qualified_for_prediction_freeze"] is False
    assert result["eligible_action"] is None
    assert snapshot["qualified_for_prediction_freeze"] is False


def test_execution_request_is_one_shot_and_pre_response():
    r=json.loads(REQUEST.read_text())
    assert r["one_shot"] is True
    assert r["bird_pilot_values_opened_before_request"] is False
    assert r["bird_confirmatory_values_opened_before_request"] is False
    assert r["effect_estimate_requested"] is False


def test_workflow_deletes_raw_before_commit_and_commits_only_json_record():
    s=WORKFLOW.read_text()
    assert "rm -rf build/bird_v164/raw" in s
    assert "confirmatory_target_values_parsed" in s
    assert "excluded_target_values_parsed" in s
    assert "effect_size" in s and "prediction_score" in s
    assert "git add development/boreal_19island_bird_pilot_execution_v1_164.json" in s
    assert "git add development/boreal_19island_bird_pilot_freeze_v1_164.json" in s
    assert "git status --porcelain" in s
    assert "borealbirds_speciesmatrix_presenceabsence.csv" not in s.split("Commit immutable pilot record",1)[1]
