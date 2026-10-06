from pathlib import Path
import importlib.util, json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_birds_topology_nulls_v1_162.py"
CONTRACT=ROOT/"development/boreal_birds_topology_sensitivity_contract_v1_162.json"

def load_module():
    spec=importlib.util.spec_from_file_location("bb162",SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_contract_keeps_ebird_disabled_and_beetle_primary_closed():
    x=json.loads(CONTRACT.read_text())
    assert x["project_policy"]["ebird_used"] is False
    assert x["project_policy"]["beetle_primary_status_may_change"] is False
    assert x["project_policy"]["BALA_primary_status_may_change"] is False
    assert x["response_access_authorized"] is False

def test_contract_predeclares_sparse_source_mechanism():
    x=json.loads(CONTRACT.read_text())
    s=x["configuration_sensitivity"]
    assert s["possible_sources_M"]==6
    assert s["eligible_species"].startswith("2 <= n <= 6")
    assert "[(M-n)/(n*(M-1))]" in s["S_i_n"]
    assert x["primary"]["favourable_direction"]=="negative"
    assert x["primary"]["threshold_search_authorized"] is False

def test_null_rule_is_response_independent_and_exact():
    x=json.loads(CONTRACT.read_text())
    q=x["topology_null"]
    assert q["ensemble_size"]==20
    assert q["accepted_swaps_per_null"]==100
    assert "degree-preserving" in q["null_rule"]
    assert "same actual-edge geographic-length quintile" in q["null_rule"]
    assert "R0-R3" in q["fixed_across_nulls"]

def test_script_contains_no_bird_response_file_or_species_values():
    s=SCRIPT.read_text()
    assert "borealbirds_speciesmatrix_presenceabsence.csv" not in s
    assert "4569037" not in s
    assert "bird_response_values_opened" in s

def test_local_null_builder_can_make_distinct_invariant_graphs():
    m=load_module()
    coords=m.load_geometry()
    op=m.freeze_connected_knn_operator(coords)
    ids=sorted(coords)
    actual={tuple(sorted((x["left"],x["right"]))) for x in op["edges"]}
    pair=m.pairwise_distances(coords)
    def pd(e): return pair[tuple(sorted(e))]
    cuts=[m.type7_quantile([pd(e) for e in actual],p) for p in (0.2,0.4,0.6,0.8)]
    all_pairs=[tuple(sorted((a,b))) for i,a in enumerate(ids) for b in ids[i+1:]]
    bins={e:sum(pd(e)>cut for cut in cuts) for e in all_pairs}
    base_degree=m.degree(ids,actual)
    seen={tuple(sorted(actual))}
    made=[]
    for idx in range(5):
        E=m.build_null(actual,ids,bins,idx,0,25)
        assert E is not None
        assert m.degree(ids,E)==base_degree
        assert m.is_connected(ids,E)
        assert {k:sum(bins[e]==k for e in E) for k in range(5)}=={k:7 for k in range(5)}
        state=tuple(sorted(E))
        assert state not in seen
        seen.add(state); made.append(state)
    assert len(made)==5
