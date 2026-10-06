from pathlib import Path
import csv
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_19island_bird_predictions_v1_163.py"

def load_module():
    spec=importlib.util.spec_from_file_location("bird_pred_v163",SCRIPT)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def test_actual_pilot_freezes_all_confirmatory_predictions_without_response():
    m=load_module()
    receipt,text=m.freeze(
        contract=m.load_json(ROOT/"development/boreal_19island_birds_prediction_freeze_contract_v1_163.json"),
        scientific_contract=m.load_json(ROOT/"development/boreal_19island_birds_topology_sensitivity_contract_v1_158.json"),
        null_receipt=m.load_json(ROOT/"development/boreal_19island_birds_topology_null_receipt_v1_158.json"),
        sensitivity_rows=m.load_csv(ROOT/"development/boreal_19island_birds_configuration_sensitivity_v1_158.csv"),
        pilot_freeze=m.load_json(ROOT/"development/boreal_19island_bird_pilot_freeze_v1_162.json"),
        pilot_execution=m.load_json(ROOT/"development/boreal_19island_bird_pilot_execution_v1_162.json"),
        pilot_snapshot=m.load_json(ROOT/"development/boreal_19island_bird_pilot_snapshot_v1_162.json"),
        pilot_execution_path=ROOT/"development/boreal_19island_bird_pilot_execution_v1_162.json",
        pilot_snapshot_path=ROOT/"development/boreal_19island_bird_pilot_snapshot_v1_162.json",
        state_path=ROOT/"development/boreal_19island_state_reference_v0_99.csv",
        state_freeze=m.load_json(ROOT/"development/boreal_19island_state_reference_freeze_v0_99.json"),
        geometry_path=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv",
        geometry_freeze=m.load_json(ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"),
        spatial_freeze=m.load_json(ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"),
        operator_freeze=m.load_json(ROOT/"development/boreal_19island_source_operator_freeze_v1_01.json"),
    )
    assert receipt["status"]=="BIRD_R3_ACTUAL_AND_20_NULL_PREDICTIONS_FROZEN_BEFORE_CONFIRMATORY_RESPONSE"
    assert receipt["eligible_species_count"]==18
    assert receipt["training_row_count"]==108
    assert receipt["prediction_row_count"]==234
    assert receipt["null_topology_count"]==20
    assert receipt["confirmatory_target_values_opened"]==0
    assert receipt["confirmatory_response_authorized"] is False
    rows=list(csv.DictReader(text.splitlines()))
    assert len(rows)==234
    assert len(rows[0])==28
    assert {int(r["pilot_presences"]) for r in rows}=={1,2,3,4}
    assert all(float.fromhex(r["S_hex"])>0 for r in rows)
    assert len({r["species"] for r in rows})==18
    assert len({r["island"] for r in rows})==13

def test_empty_source_rule_is_topology_invariant():
    c=json.loads((ROOT/"development/boreal_19island_birds_prediction_freeze_contract_v1_163.json").read_text())
    e=c["empty_source_semantics"]
    assert e["same_graph_empty_sentinel_for_actual_and_all_nulls"] is True
    assert e["pressure_empty"]==0.0
    assert e["changed_using_confirmatory_response"] is False
