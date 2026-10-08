import importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"development/global_mammals_independent_provenance_contract_v1_189.json").read_text())
p=ROOT/"scripts/audit_external_mammal_checklist_provenance_v1_189.py"
spec=importlib.util.spec_from_file_location("g189",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def receipt(files=None,status="PRE_OUTCOME_IDENTITY_POOL_AVAILABLE_GAZETTEER_REQUIRED"):
    if files is None:
        files=[]
        for group,meta in C["groups"].items():
            taxa=["Genus%d species%d"%(i,i) for i in range(23)] if meta["primary_eligible_metadata"] else ["Excluded1 x"]
            files.append({"group":group,"file":meta["file"],"named_islands":7,
                "overlap_species_names":taxa,"exact_ultrarare_taxon_header_overlap":len(taxa)})
    return {"status":status,"files":files,"unique_529_species_header_overlap":24,
      "external_checklist_binary_cells_decoded":0,"original_mammal_heldout_cells_opened":0}

def test_direct_iucn_and_historical_groups_preexcluded():
    assert C["groups"]["CaliforniaGulf"]["primary_eligible_metadata"] is False
    assert C["groups"]["MediterraneanLandbridge"]["primary_eligible_metadata"] is False
    assert C["groups"]["MediterraneanOceanic"]["primary_eligible_metadata"] is False

def test_classification_never_authorizes_scoring():
    x=m.audit(receipt(),C)
    assert x["status"]=="HOLD_PROVENANCE_QUALIFIED_ISLAND_ID_GAZETTEER_REQUIRED"
    assert x["eligible_group_focal_species_headers_unique"]==23
    assert x["eligible_groups_with_exact_focal_headers"]==6
    assert x["external_scoring_authorized"] is False
    assert x["external_checklist_binary_cells_decoded"]==0

def test_provisional_eligibility_does_not_relax_before_response():
    x=receipt()
    for f in x["files"]:
        if C["groups"][f["group"]]["primary_eligible_metadata"]:
            f["overlap_species_names"]=[]
            f["exact_ultrarare_taxon_header_overlap"]=0
    x["unique_529_species_header_overlap"]=1
    out=m.audit(x,C)
    assert out["status"]=="STOP_PROVENANCE_QUALIFIED_HEADER_SUPPORT"

def test_original_header_failure_cannot_be_turned_into_success():
    x=m.audit(receipt(status="STOP_EXTERNAL_CHECKLIST_HEADER_SUPPORT_INSUFFICIENT"),C)
    assert x["status"]=="STOP_PARENT_V188_HEADER_SUPPORT"
