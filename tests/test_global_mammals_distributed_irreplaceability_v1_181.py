from pathlib import Path
import importlib.util,json
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/run_global_mammals_distributed_irreplaceability_v1_181.py"
CONTRACT=ROOT/"development/global_mammals_distributed_irreplaceability_contract_v1_181.json"

def load():
    spec=importlib.util.spec_from_file_location("v181",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_source_turnover_is_high_when_sources_partition_targets():
    np=pytest.importorskip("numpy", reason="NumPy is optional in standalone CI; dedicated numeric job runs these tests")
    m=load()
    w=np.array([[1.,1.,0.,0.],[0.,0.,1.,1.]])
    alpha,gamma,beta,dom,n=m.source_turnover(w)
    assert alpha==1.0
    assert gamma==2.0
    assert beta==2.0
    assert dom==1.0
    assert n==4

def test_source_turnover_is_one_when_sources_are_locally_redundant():
    np=pytest.importorskip("numpy", reason="NumPy is optional in standalone CI; dedicated numeric job runs these tests")
    m=load()
    w=np.array([[1.,1.,1.,1.],[1.,1.,1.,1.]])
    alpha,gamma,beta,dom,n=m.source_turnover(w)
    assert abs(alpha-2.0)<1e-12
    assert abs(gamma-2.0)<1e-12
    assert abs(beta-1.0)<1e-12
    assert abs(dom-.5)<1e-12

def test_contract_is_response_free_and_null_preserves_bioregion_counts():
    c=json.loads(CONTRACT.read_text())
    assert c["population"]["heldout_occurrence_authorized"] is False
    assert c["matched_random_placement_null"]["replicates_per_species"]==1000
    assert "exact source count in each bioregion" in c["matched_random_placement_null"]["preserves"]
    assert "do not infer temporal insurance or persistence from spatial source turnover" in c["claim_boundary"]
