from pathlib import Path
import csv
import importlib.util
import io
import json

ROOT=Path(__file__).resolve().parents[1]
AUTH_SCRIPT=ROOT/"scripts/authorize_boreal_19island_bird_pilot_v1_163.py"
AUTH=ROOT/"development/boreal_19island_bird_pilot_authorization_v1_163.json"
AUTH_CONTRACT=ROOT/"development/boreal_19island_bird_pilot_authorization_contract_v1_163.json"
PROTOCOL=ROOT/"development/boreal_bird_topology_sensitivity_contract_v1_162.json"
TOPOLOGY=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
FULL=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
METADATA=ROOT/"development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"


def load_script(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_authorization_exactly_replays_from_response_free_parents():
    m=load_script(AUTH_SCRIPT,"bird_auth_v163")
    observed=m.build(
        contract=m.load(AUTH_CONTRACT),
        protocol=m.load(PROTOCOL),
        topology=m.load(TOPOLOGY),
        full=m.load(FULL),
        metadata=m.load(METADATA),
        spatial=m.load(SPATIAL),
        geometry=m.load(GEOMETRY),
    )
    assert observed==json.loads(AUTH.read_text())


def test_authorization_opens_no_response_and_keeps_confirmatory_closed():
    x=json.loads(AUTH.read_text())
    assert x["response_values_opened_by_authorization"] is False
    assert x["authorization_consumed"] is False
    assert x["pilot_response_authorized"] is True
    assert x["confirmatory_response_authorized"] is False
    assert x["effect_size"] is None
    assert x["prediction_score"] is None
    assert x["counts_as_empirical_evidence"] is False
    assert len(x["topology_parent"]["null_edge_fingerprints"])==20


def synthetic_bird_matrix():
    x=json.loads(AUTH.read_text())
    species=[f"bird_{i:02d}" for i in range(54)]
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["Island",*species])
    pilot=x["pilot_islands"]
    pilot_index={island:i for i,island in enumerate(pilot)}
    analysis=set(x["analysis_island_order"])
    pilot_set=set(pilot)
    for island in x["full_source_island_order"]:
        if island in pilot_set:
            i=pilot_index[island]
            values=[]
            for j in range(54):
                if j<4:
                    n=2
                elif j<8:
                    n=3
                elif j<12:
                    n=4
                else:
                    n=0
                values.append("1" if i<n else "0")
        else:
            # These cells must remain opaque. If the router decodes any of them,
            # the synthetic test must fail immediately.
            values=["NOT_A_BINARY_RESPONSE"]*54
        w.writerow([island,*values])
    return out.getvalue().encode("utf-8")


def test_bird_router_decodes_only_six_pilot_islands_and_records_n():
    from structural.boreal_19island_bird_pilot_router import (
        build_boreal_19island_bird_pilot_surface,
    )
    x=json.loads(AUTH.read_text())
    routed=build_boreal_19island_bird_pilot_surface(
        response_csv_bytes=synthetic_bird_matrix(),
        full_expected_islands=x["full_source_island_order"],
        analysis_expected_islands=x["analysis_island_order"],
        analysis_island_to_block=x["island_to_block"],
        pilot_partition=x["pilot_block_ids"],
        confirmatory_partition=x["confirmatory_block_ids"],
        expected_species_count=54,
    )
    b=routed.base
    assert b.source_response_rows_seen==42
    assert b.routing_island_fields_decoded==42
    assert b.pilot_island_rows_semantically_parsed==6
    assert b.pilot_target_values_parsed==6*54
    assert b.confirmatory_target_values_parsed==0
    assert b.excluded_target_values_parsed==0
    assert b.pilot_species_universe_count==12
    counts=dict(routed.pilot_occupancy_count_by_species)
    assert set(counts.values())=={2,3,4}
    assert routed.distinct_pilot_occupancy_counts==(2,3,4)


def test_pilot_gate_is_fixed_before_response():
    c=json.loads(AUTH_CONTRACT.read_text())
    assert c["pilot_gate"]["minimum_fixed_species"]==10
    assert c["pilot_gate"]["minimum_distinct_n"]==3
    assert c["pilot_gate"]["allowed_n"]==[2,3,4,5,6]
    assert c["one_shot"]["rerun_after_semantic_open"] is False
