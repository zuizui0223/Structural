from pathlib import Path
import csv
import importlib.util
import io
import json

from structural.boreal_19island_bird_pilot_router import (
    build_boreal_19island_bird_pilot_surface,
)

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/run_boreal_bird_pilot_v1_163.py"
MODEL=ROOT/"scripts/freeze_boreal_bird_preconfirmatory_v1_164.py"
PILOT_CONTRACT=ROOT/"development/boreal_bird_pilot_contract_v1_163.json"
MODEL_CONTRACT=ROOT/"development/boreal_bird_preconfirmatory_contract_v1_164.json"
TOPO=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
GEOM_FREEZE=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"
FULL=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
STATE=ROOT/"development/boreal_19island_state_reference_v0_99.csv"
STATE_FREEZE=ROOT/"development/boreal_19island_state_reference_freeze_v0_99.json"
GEOM=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_csv():
    spatial=json.loads(SPATIAL.read_text())
    full=json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    pilot=sorted(spatial["pilot_islands"])
    species=[f"sp{j:02d}" for j in range(54)]
    patterns={}
    # 20 qualifying species, balanced across n=2..6.
    for j in range(20):
        n=2+(j%5)
        # Rotate the occupied subset to avoid degenerate source features.
        start=j%6
        patterns[j]={pilot[(start+k)%6] for k in range(n)}
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["Island",*species])
    for island in full:
        row=[island]
        for j in range(54):
            if island in set(pilot):
                row.append("1" if island in patterns.get(j,set()) else "0")
            else:
                row.append("OPAQUE")
        w.writerow(row)
    return out.getvalue().encode()


def make_pilot():
    run=load(RUNNER,"run163")
    spatial=json.loads(SPATIAL.read_text())
    full=json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    analysis=json.loads(GEOM_FREEZE.read_text())["island_order"]
    routed=build_boreal_19island_bird_pilot_surface(
        response_csv_bytes=synthetic_csv(),
        full_expected_islands=full,
        analysis_expected_islands=analysis,
        analysis_island_to_block=spatial["island_to_block"],
        pilot_partition=spatial["pilot_block_ids"],
        confirmatory_partition=spatial["confirmatory_block_ids"],
        expected_species_count=54,
    )
    contract=json.loads(PILOT_CONTRACT.read_text())
    snapshot,gate=run.evaluate_gate(
        routed=routed,
        topology=json.loads(TOPO.read_text()),
        contract=contract,
    )
    assert gate["gate_passed"] is True
    result={
        "schema":"structural.boreal_bird_pilot_execution.v1_163",
        "status":"BIRD_PILOT_GATE_PASSED_FREEZE_MODELS_AND_PREDICTIONS_ONLY",
        "candidate_id":contract["candidate_id"],
        "authorization_consumed":True,
        "bird_pilot_response_opened":True,
        "bird_confirmatory_response_opened":False,
        "confirmatory_values_parsed":0,
        "excluded_values_parsed":0,
        "snapshot_fingerprint":snapshot["snapshot_fingerprint"],
        "counts_as_empirical_evidence":False,
    }
    return result,snapshot


def test_preconfirmatory_implementation_fits_all_21_candidate_models_response_free():
    model=load(MODEL,"model164")
    result,snapshot=make_pilot()
    receipt,predictions=model.freeze(
        pilot_execution=result,
        pilot_snapshot=snapshot,
        contract=json.loads(MODEL_CONTRACT.read_text()),
        topology=json.loads(TOPO.read_text()),
        state_path=STATE,
        state_freeze=json.loads(STATE_FREEZE.read_text()),
        geometry_path=GEOM,
        geometry_freeze=json.loads(GEOM_FREEZE.read_text()),
        spatial=json.loads(SPATIAL.read_text()),
    )
    assert receipt["status"]=="BIRD_ACTUAL_AND_NULL_PREDICTIONS_FROZEN_BEFORE_CONFIRMATORY_RESPONSE"
    assert receipt["fixed_species_count"]==snapshot["fixed_species_count"]
    assert receipt["prediction_row_count"]==13*snapshot["fixed_species_count"]
    assert len(receipt["models"]["C_null"])==20
    assert len(receipt["null_graph_fingerprints"])==20
    assert receipt["bird_confirmatory_values_opened"]==0
    assert receipt["bird_confirmatory_response_authorized"] is False

    rows=list(csv.DictReader(predictions.splitlines()))
    assert len(rows)==receipt["prediction_row_count"]
    assert all("p_C_null_20_hex" in row for row in rows)
    assert all(row["island"] in json.loads(SPATIAL.read_text())["confirmatory_islands"] for row in rows)


def test_model_implementation_keeps_r3_common_across_topologies():
    c=json.loads(MODEL_CONTRACT.read_text())
    assert "R0, R1, R2 and R3 are identical" in c["reference_ladder"]["critical_invariant"]
    assert c["response_boundary"]["bird_confirmatory_response_opened"] is False
