from pathlib import Path
import importlib.util
import json

from structural.boreal_beetle_pilot_router import encode_binary_vector_hex

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_bird_preconfirmatory_v1_164.py"
CONTRACT=ROOT/"development/boreal_bird_preconfirmatory_contract_v1_164.json"
TOPO=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
STATE=ROOT/"development/boreal_19island_state_reference_v0_99.csv"
STATE_FREEZE=ROOT/"development/boreal_19island_state_reference_freeze_v0_99.json"
GEOM=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"
GEOM_FREEZE=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"

def load_module():
    spec=importlib.util.spec_from_file_location("bird164",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def synthetic_pilot():
    m=load_module()
    spatial=json.loads(SPATIAL.read_text())
    topo=json.loads(TOPO.read_text())
    species=[f"sp{j:02d}" for j in range(15)]
    pilot=["DN","FD","PP","HU","IL","IS"]
    # Use n=2..6 cyclically and deterministic prefix occupancy.
    matrix={}
    for island in pilot:
        matrix[island]=[]
    for j in range(15):
        n=2+(j%5)
        for k,island in enumerate(pilot):
            matrix[island].append(int(k<n))
    nrows=[{"species":species[j],"n":2+(j%5)} for j in range(15)]
    raw=[]
    for row in nrows:
        for target in spatial["confirmatory_islands"]:
            raw.append(float.fromhex(topo["configuration_sensitivity"]["targets"][target]["S_by_n_hex"][str(row["n"])]))
    mean=sum(raw)/len(raw)
    sd=(sum((x-mean)**2 for x in raw)/len(raw))**0.5
    snapshot={
      "schema":"structural.boreal_bird_pilot_snapshot.v1_163",
      "status":"BIRD_PILOT_GATE_PASSED",
      "candidate_id":"lac_la_ronge_boreal_19island_birds_2026_topology_sensitivity",
      "response_file_sha256":"3838c39a7a94010569ce399a6b19e651f45fa60d0aef1793445dcb6c0b6e201c",
      "fixed_species":species,
      "fixed_species_count":len(species),
      "fixed_species_sha256":"x"*64,
      "pilot_island_order":pilot,
      "pilot_island_to_block":{i:spatial["island_to_block"][i] for i in pilot},
      "targets_hex_by_island":{i:encode_binary_vector_hex(matrix[i]) for i in pilot},
      "n_by_species":nrows,
      "n_histogram":{str(n):3 for n in range(2,7)},
      "distinct_n_count":5,
      "pilot_positive_cells":sum(r["n"] for r in nrows),
      "pilot_negative_cells":6*len(species)-sum(r["n"] for r in nrows),
      "S_standardization":{"surface_cells":13*len(species),"mean_hex":float(mean).hex(),"population_sd_hex":float(sd).hex()},
      "gate_failures":[],
      "confirmatory_values_parsed":0,
      "excluded_values_parsed":0,
      "effect_size":None,
      "prediction_score":None,
      "counts_as_empirical_evidence":False,
    }
    snapshot["snapshot_fingerprint"]=m.canonical_sha256(snapshot)
    execution={
      "schema":"structural.boreal_bird_pilot_execution.v1_163",
      "status":"BIRD_PILOT_GATE_PASSED_FREEZE_MODELS_AND_PREDICTIONS_ONLY",
      "candidate_id":snapshot["candidate_id"],
      "authorization_consumed":True,
      "bird_pilot_response_opened":True,
      "bird_confirmatory_response_opened":False,
      "confirmatory_values_parsed":0,
      "excluded_values_parsed":0,
      "snapshot_fingerprint":snapshot["snapshot_fingerprint"],
      "counts_as_empirical_evidence":False,
    }
    return execution,snapshot

def test_synthetic_pilot_freezes_21_candidate_prediction_surfaces():
    m=load_module();execution,snapshot=synthetic_pilot()
    receipt,text=m.freeze(
      pilot_execution=execution,pilot_snapshot=snapshot,
      contract=json.loads(CONTRACT.read_text()),
      topology=json.loads(TOPO.read_text()),
      state_path=STATE,state_freeze=json.loads(STATE_FREEZE.read_text()),
      geometry_path=GEOM,geometry_freeze=json.loads(GEOM_FREEZE.read_text()),
      spatial=json.loads(SPATIAL.read_text()),
    )
    assert receipt["status"]=="BIRD_ACTUAL_AND_NULL_PREDICTIONS_FROZEN_BEFORE_CONFIRMATORY_RESPONSE"
    assert receipt["prediction_row_count"]==13*15
    assert len(receipt["models"]["C_null"])==20
    assert len(receipt["null_graph_fingerprints"])==20
    header=text.splitlines()[0].split(",")
    assert header[-1]=="p_C_null_20_hex"
    assert "zS_hex" in header
    assert receipt["bird_confirmatory_values_opened"]==0
    assert receipt["bird_confirmatory_response_authorized"] is False

def test_model_freeze_reuses_actual_generic_context_for_nulls():
    x=json.loads(CONTRACT.read_text())
    assert "R0, R1, R2 and R3 are identical" in x["reference_ladder"]["critical_invariant"]
