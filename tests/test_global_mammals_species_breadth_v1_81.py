from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_global_mammals_species_breadth_diagnostics_v1_81.py"
    spec=importlib.util.spec_from_file_location("sdiag",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_rank_correlation_is_deterministic():
    m=load_module()
    assert m.ranks([1,1,3])==[1.5,1.5,3.0]
    assert abs(m.corr([1,2,3],[3,2,1])+1.0)<1e-15

def test_contract_uses_frozen_species_universe_without_subgroup_search():
    x=json.loads((ROOT/"development/global_mammals_species_breadth_diagnostics_contract_v1_81.json").read_text())
    assert x["inputs"]["focal_species"]==79
    assert x["diagnostics"]["breadth"].startswith("pilot_presence")
    assert "no species are removed" in x["anti_rescue"][1]
    assert "no trait or taxonomic subgroup search" in x["anti_rescue"][2]
    assert x["counts_as_confirmatory_evidence"] is False

def test_workflow_reads_only_existing_frozen_response_surface():
    s=(ROOT/".github/workflows/global-mammals-species-breadth-v1_81.yml").read_text()
    assert "11112360652" in s
    assert "11112450910" in s
    assert "11113225988" in s
    assert "DRYAD_TOKEN" not in s
    assert "Appendix_1" not in s
