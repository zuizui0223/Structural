#!/usr/bin/env python3
"""Project SW Finland historical state while keeping colonization outcome opaque."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_t0_projection_contract_v1_164.json"
DEFAULT_FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

class Stop(RuntimeError): pass

def load_json(p:Path)->dict:
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop("JSON object required")
    return x

def fsha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def norm_missing(x:str)->str:
    return str(x).strip()

def write_csv(path:Path,fields:list[str],rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def project(csv_path:Path,header_receipt:dict,contract:dict,firewall:dict,outdir:Path)->dict:
    if contract.get("schema")!="structural.sw_finland_t0_projection_contract.v1_164":raise Stop("contract schema drift")
    if firewall.get("schema")!="structural.sw_finland_plant_colonization_column_firewall.v1_162":raise Stop("firewall schema drift")
    auth=contract["authorization"]
    if header_receipt.get("schema")!=auth["required_header_receipt_schema"]:raise Stop("header receipt schema drift")
    if header_receipt.get("status")!=auth["required_header_status"]:raise Stop("header audit not qualified")
    if header_receipt.get("t0_projection_authorized") is not True:raise Stop("t0 projection not authorized")
    if header_receipt.get("outcome_values_read")!=0:raise Stop("future outcome boundary already violated")
    if header_receipt.get("file_sha256")!=fsha(csv_path):raise Stop("CSV/header receipt SHA mismatch")

    protected=set(firewall["protected_future_endpoint_columns"])
    if protected!={"outcome"}:raise Stop("protected endpoint drift")
    island_cols=["Euref_X_original","Euref_Y_original","Euref_X","Euref_Y","Residents_per_area_log","Area_log",
      "Buffer_2_km_log","Buffer_5_km_log","Shannon_habitats","Convolution","Limestone","Buildings",
      "Meadow_or_pasture","Deciduous_forest","Coniferous_forest","Mixed_forest","Scrub","Sand",
      "Open_rock_or_bare_ground","Marsh","Shore_meadow"]
    species_cols=["Historical_total_log","North_limit","Ellenberg_Light","Ellenberg_Temperature","Ellenberg_Moisture",
      "Ellenberg_Reaction","Ellenberg_Nitrogen","Eklund_culture","Life_cycle","Life_form","SLA","Plant_height_log",
      "Dispersal_vector","Seed_bank","Seed_mass_log","Pollen_vector","Apomictic","Veg_repr","Family","Genus"]

    islands={};species={};absent=set();nearest={}
    rows=0
    with csv_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.reader(f)
        try: header=next(rd)
        except StopIteration as exc: raise Stop("empty CSV") from exc
        idx={name:i for i,name in enumerate(header)}
        if len(idx)!=len(header):raise Stop("duplicate header names")
        required={"outcome","spp.name","holmkod","Dist_to_historical_log"}|set(island_cols)|set(species_cols)
        miss=sorted(required-set(idx))
        if miss:raise Stop(f"projection header mismatch: {miss}")
        outcome_index=idx["outcome"]  # endpoint position is verified only; its cell is never dereferenced.
        assert outcome_index>=0
        for row in rd:
            rows+=1
            if len(row)!=len(header):raise Stop("ragged CSV row")
            sp=norm_missing(row[idx["spp.name"]]); isl=norm_missing(row[idx["holmkod"]])
            if not sp or not isl:raise Stop("blank species/island routing key")
            key=(sp,isl)
            if key in absent:raise Stop("duplicate potential-colonization event key")
            absent.add(key)
            ival=tuple(norm_missing(row[idx[c]]) for c in island_cols)
            sval=tuple(norm_missing(row[idx[c]]) for c in species_cols)
            nval=norm_missing(row[idx["Dist_to_historical_log"]])
            if isl in islands and islands[isl]!=ival:raise Stop(f"island-state drift for {isl}")
            islands[isl]=ival
            if sp in species and species[sp]!=sval:raise Stop(f"species-state drift for {sp}")
            species[sp]=sval
            nearest[key]=nval
            # Deliberately no endpoint-cell dereference.

    exp=contract["expected_support"]
    if rows!=exp["potential_event_rows"]:raise Stop(f"unexpected event row count: {rows}")
    if len(islands)!=exp["island_count"]:raise Stop(f"unexpected island count: {len(islands)}")
    if len(species)!=exp["species_count"]:raise Stop(f"unexpected species count: {len(species)}")

    island_ids=sorted(islands); species_ids=sorted(species)
    occupied=[]
    counts={}
    for sp in species_ids:
        occ=[isl for isl in island_ids if (sp,isl) not in absent]
        counts[sp]=len(occ)
        occupied.extend({"spp.name":sp,"holmkod":isl} for isl in occ)

    island_rows=[{"holmkod":isl,**{c:v for c,v in zip(island_cols,islands[isl])}} for isl in island_ids]
    species_rows=[{"spp.name":sp,"reconstructed_historical_island_count":counts[sp],
                   **{c:v for c,v in zip(species_cols,species[sp])}} for sp in species_ids]
    absent_rows=[{"spp.name":sp,"holmkod":isl,"Dist_to_historical_log":nearest[(sp,isl)]} for sp,isl in sorted(absent)]

    write_csv(outdir/"sw_finland_t0_island_state.csv",["holmkod"]+island_cols,island_rows)
    write_csv(outdir/"sw_finland_t0_species_state.csv",["spp.name","reconstructed_historical_island_count"]+species_cols,species_rows)
    write_csv(outdir/"sw_finland_t0_historical_absent_pairs.csv",["spp.name","holmkod","Dist_to_historical_log"],absent_rows)
    write_csv(outdir/"sw_finland_t0_historical_occupied_pairs.csv",["spp.name","holmkod"],occupied)

    result={
      "schema":"structural.sw_finland_t0_projection_result.v1_164",
      "status":"T0_SOURCE_STATE_FROZEN_FUTURE_OUTCOME_REMAINS_SEALED",
      "candidate_id":contract["candidate_id"],
      "source_file_sha256":fsha(csv_path),
      "potential_event_rows":rows,
      "island_count":len(islands),
      "species_count":len(species),
      "historical_absent_pair_count":len(absent),
      "historical_occupied_pair_count":len(occupied),
      "species_with_zero_reconstructed_historical_sources":sum(v==0 for v in counts.values()),
      "minimum_reconstructed_historical_sources":min(counts.values()),
      "maximum_reconstructed_historical_sources":max(counts.values()),
      "outcome_values_read":0,
      "future_outcome_opened":False,
      "model_fit_count":0,
      "counts_as_empirical_evidence":False,
      "next_action":"freeze source-state eligibility, spatial blocks, graph/null topologies and prediction protocol before any outcome access"
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"sw_finland_t0_projection_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("csv_file",type=Path);ap.add_argument("--header-receipt",type=Path,required=True)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);ap.add_argument("--firewall",type=Path,default=DEFAULT_FIREWALL)
    ap.add_argument("--output-dir",type=Path,required=True);a=ap.parse_args()
    try:
        r=project(a.csv_file,load_json(a.header_receipt),load_json(a.contract),load_json(a.firewall),a.output_dir);code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_t0_projection_result.v1_164","status":"STOP_T0_PROJECTION","reason":str(exc),
           "outcome_values_read":0,"future_outcome_opened":False,"counts_as_empirical_evidence":False};code=2
    print(json.dumps(r,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
