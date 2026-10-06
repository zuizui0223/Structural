from pathlib import Path
import importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_sw_finland_topology_v1_172.py"
CONTRACT=ROOT/"development/sw_finland_topology_freeze_contract_v1_172.json"

def load():
    spec=importlib.util.spec_from_file_location("swf172",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_contract_keeps_future_outcome_fully_sealed():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["pilot_future_outcome_authorized"] is False
    assert c["response_boundary"]["confirmatory_future_outcome_authorized"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
    assert c["matched_nulls"]["count"]==20

def test_spatial_partition_is_response_independent_and_disjoint():
    m=load();c=json.loads(CONTRACT.read_text())
    c["spatial_validation"]=dict(c["spatial_validation"])
    c["spatial_validation"].update({
      "minimum_total_blocks":5,"minimum_pilot_blocks":1,"minimum_confirmatory_blocks":3
    })
    coords={f"i{k:02d}":(k*15000.0,(k%3)*17000.0) for k in range(10)}
    rows,n,np,nc=m.partition(coords,c)
    assert n>=5 and np>=1 and nc>=3
    got={r[0]:r[4] for r in rows}
    assert set(got)==set(coords)
    assert set(got.values())=={"pilot","confirmatory"}

def test_minimal_connected_knn_and_shortest_paths():
    m=load()
    coords={f"i{k}":(k*10000.0,0.0) for k in range(8)}
    D=m.pairwise(coords);k,E,audit=m.minimal_connected_knn(coords,D)
    assert k>=1
    assert m.connected(sorted(coords),E,D)
    A=m.adjacency(sorted(coords),E,D)
    d=m.dijkstra("i0",A)
    assert d["i7"]>0 and math.isfinite(d["i7"])

def test_species_factor_decreases_with_historical_source_count():
    M=470
    vals=[(M-n)/(n*(M-1)) for n in (1,2,5,20,100,470)]
    assert all(a>=b for a,b in zip(vals,vals[1:]))
    assert vals[-1]==0
