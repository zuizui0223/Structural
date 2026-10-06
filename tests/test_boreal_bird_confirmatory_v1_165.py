from pathlib import Path
import csv
import io
import json
import importlib.util

from structural.boreal_19island_bird_confirmatory_router import route_boreal_bird_confirmatory

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/boreal_bird_confirmatory_scoring_contract_v1_165.json"
SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
FULL=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
SCRIPT=ROOT/"scripts/score_boreal_bird_confirmatory_v1_165.py"

def load_module():
    spec=importlib.util.spec_from_file_location("bird165",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def synthetic_response(fixed):
    full=json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    spatial=json.loads(SPATIAL.read_text())
    confirm=set(spatial["confirmatory_islands"])
    species=[*fixed]+[f"other{j}" for j in range(54-len(fixed))]
    out=io.StringIO(newline="");w=csv.writer(out,lineterminator="\n")
    w.writerow(["Island",*species])
    for i,island in enumerate(full):
        row=[island]
        for j,_ in enumerate(species):
            if island in confirm and j<len(fixed):
                row.append("1" if (i+j)%3==0 else "0")
            else:
                row.append("OPAQUE")
        w.writerow(row)
    return out.getvalue().encode()

def test_confirmatory_router_never_reopens_pilot_or_nonfixed_cells():
    fixed=[f"sp{j}" for j in range(12)]
    spatial=json.loads(SPATIAL.read_text())
    full=json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    r=route_boreal_bird_confirmatory(
      response_csv_bytes=synthetic_response(fixed),
      full_expected_islands=full,
      pilot_islands=spatial["pilot_islands"],
      confirmatory_islands=spatial["confirmatory_islands"],
      fixed_species=fixed,
      expected_species_columns=54,
    )
    assert r.confirmatory_values_parsed==13*len(fixed)
    assert r.pilot_values_parsed==0
    assert r.excluded_values_parsed==0
    assert r.nonfixed_confirmatory_values_parsed==0

def test_weighted_slope_block_equalization():
    m=load_module()
    rows=[
      ("a",-1.0,1.0),("a",0.0,0.0),("a",1.0,-1.0),
      ("b",-1.0,2.0),("b",1.0,-2.0),
    ]
    assert m.weighted_slope(rows)<0

def test_confirmatory_contract_is_one_shot_and_nonrescuing():
    x=json.loads(CONTRACT.read_text())
    assert x["primary"]["minimum_presence_blocks"]==4
    assert x["primary"]["bootstrap_replicates"]==10000
    assert x["result_ceiling"]["beetle_primary_status_change_authorized"] is False
    assert x["project_policy"]["eBird_enabled"] is False
