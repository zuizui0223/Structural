#!/usr/bin/env python3
"""Classify documented checklist provenance before opening external binary labels."""
from __future__ import annotations
import argparse,json,sys,unicodedata
from pathlib import Path

class GateError(ValueError): pass

def taxon_key(s:str)->str:
    return " ".join(unicodedata.normalize("NFC",str(s)).replace("."," ").replace("_"," ").split()).casefold()

def audit(receipt,contract):
    if contract["schema"]!="structural.external_mammal_checklist_provenance_contract.v1_189":
        raise GateError("contract mismatch")
    if receipt.get("external_checklist_binary_cells_decoded")!=0 or receipt.get("original_mammal_heldout_cells_opened")!=0:
        raise GateError("response boundary already violated")
    mapping=contract["groups"]
    files=receipt.get("files",[])
    if len(files)!=9 or len({f.get("group") for f in files})!=9 or set(mapping)!={f.get("group") for f in files}:
        raise GateError("nine frozen group identities mismatch")
    rows=[]
    available=set();pool=set();ngroup=0;nrow=0
    for f in files:
        group=f["group"];meta=mapping[group]
        if meta["file"]!=f["file"]:
            raise GateError("group filename drift: "+group)
        status="PROVISIONAL_LITERATURE_PRIMARY" if meta["primary_eligible_metadata"] else "EXCLUDED_SOURCE_INDEPENDENCE_UNVERIFIED"
        taxa={taxon_key(t) for t in f["overlap_species_names"]}
        if len(taxa)!=f["exact_ultrarare_taxon_header_overlap"]:
            raise GateError("species canonical collision or drift: "+group)
        available.update(taxa)
        if meta["primary_eligible_metadata"]:
            pool.update(taxa);nrow+=f["named_islands"]
            ngroup+=bool(taxa)
        rows.append({
            "group":group,"file":f["file"],"provenance_class":meta["class"],
            "in_independent_primary_pool":bool(meta["primary_eligible_metadata"]),
            "named_islands":f["named_islands"],
            "focal_species_headers":len(taxa),
            "status":status
        })
    if len(available)!=receipt.get("unique_529_species_header_overlap"):
        raise GateError("v188 all-group overlap mismatch")
    g=contract["gating"]
    qualifies=(len(pool)>=g["min_unique_focal_species_headers_in_primary_eligible_groups"]
        and ngroup>=g["min_primary_eligible_groups_with_exact_focal_headers"]
        and nrow>=g["min_primary_eligible_named_islands"])
    state=contract["status_logic"]["v188_not_pass"] if receipt["status"]!=g["require_v188_header_gate_status"] else (
        contract["status_logic"]["metadata_sufficient"] if qualifies else contract["status_logic"]["metadata_insufficient"])
    return {
      "schema":"structural.external_mammal_checklist_provenance_result.v1_189",
      "status":state,
      "source_dataset":contract["source_dataset"],
      "groups":rows,
      "all_group_focal_species_headers_unique":len(available),
      "eligible_group_focal_species_headers_unique":len(pool),
      "eligible_groups_with_exact_focal_headers":ngroup,
      "eligible_group_named_islands":nrow,
      "excluded_direct_IUCN_groups":["CaliforniaGulf"],
      "excluded_mixed_historical_groups":["MediterraneanLandbridge","MediterraneanOceanic"],
      "metadata_gates_passed":qualifies,
      "external_checklist_binary_cells_decoded":0,
      "original_mammal_heldout_cells_opened":0,
      "original_heldout_predictions_scored":False,
      "island_ID_crosswalk_available":False,
      "external_scoring_authorized":False,
      "scientific_evidence_produced":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("v188_receipt",type=Path)
    p.add_argument("--contract",type=Path,default=Path("development/global_mammals_independent_provenance_contract_v1_189.json"))
    p.add_argument("--result",type=Path,required=True)
    a=p.parse_args()
    try:
        out=audit(json.loads(a.v188_receipt.read_text()),json.loads(a.contract.read_text()))
        code=0
    except (GateError,ValueError,KeyError,TypeError,OSError) as e:
        out={"schema":"structural.external_mammal_checklist_provenance_result.v1_189","status":"STOP_PROVENANCE_GATE_SCHEMA","reason":str(e),"external_checklist_binary_cells_decoded":0,"original_mammal_heldout_cells_opened":0,"external_scoring_authorized":False,"scientific_evidence_produced":False}
        code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return code
if __name__=="__main__":sys.exit(main())
