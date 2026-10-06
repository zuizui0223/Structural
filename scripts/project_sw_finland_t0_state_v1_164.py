#!/usr/bin/env python3
"""Build SW Finland t0 state from a byte-routed safe projection only.

The raw mixed archive is forbidden input here. Exact historical source identity
is reconstructed only for species whose routed historical-absence rows are
complete relative to the independently documented historical source count.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_t0_projection_contract_v1_164.json"
DEFAULT_FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

class Stop(RuntimeError):
    pass

def load_json(p:Path)->dict:
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise Stop("JSON object required")
    return x

def fsha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def clean(x:str)->str:
    return str(x).strip()

def as_float(x:str,label:str)->float:
    try:
        v=float(clean(x))
    except ValueError as exc:
        raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):
        raise Stop(f"nonfinite {label}")
    return v

def historical_source_count(log_value:str,tol:float)->tuple[int,bool,float]:
    """Invert the documented log10(x+1) transform without outcome information."""
    try:
        z=float(clean(log_value))
    except ValueError:
        return 0,False,float("nan")
    if not math.isfinite(z):
        return 0,False,float("nan")
    raw=(10.0**z)-1.0
    n=int(round(raw))
    ok=(0<=n<=471 and abs(raw-n)<=tol*max(1.0,abs(raw)))
    return n,ok,raw

def write_csv(path:Path,fields:list[str],rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        w.writeheader();w.writerows(rows)

def project(safe_csv:Path,router_receipt:dict,contract:dict,firewall:dict,outdir:Path)->dict:
    if contract.get("schema")!="structural.sw_finland_t0_projection_contract.v1_164":
        raise Stop("contract schema drift")
    if firewall.get("schema")!="structural.sw_finland_plant_colonization_column_firewall.v1_162":
        raise Stop("firewall schema drift")
    auth=contract["authorization"]
    if router_receipt.get("schema")!=auth["required_router_schema"]:
        raise Stop("router receipt schema drift")
    if router_receipt.get("status")!=auth["required_router_status"]:
        raise Stop("router did not qualify")
    if router_receipt.get("protected_field_values_decoded")!=0:
        raise Stop("protected future endpoint was decoded")
    if router_receipt.get("protected_field_bytes_persisted")!=0:
        raise Stop("protected future endpoint bytes were persisted")
    if router_receipt.get("safe_projection_sha256")!=fsha(safe_csv):
        raise Stop("safe projection SHA mismatch")

    island_cols=[
      "Euref_X_original","Euref_Y_original","Euref_X","Euref_Y",
      "Residents_per_area_log","Area_log","Buffer_2_km_log","Buffer_5_km_log",
      "Shannon_habitats","Convolution","Limestone","Buildings","Meadow_or_pasture",
      "Deciduous_forest","Coniferous_forest","Mixed_forest","Scrub","Sand",
      "Open_rock_or_bare_ground","Marsh","Shore_meadow"
    ]
    species_cols=[
      "Historical_total_log","North_limit","Ellenberg_Light","Ellenberg_Temperature",
      "Ellenberg_Moisture","Ellenberg_Reaction","Ellenberg_Nitrogen","Eklund_culture",
      "Life_cycle","Life_form","SLA","Plant_height_log","Dispersal_vector","Seed_bank",
      "Seed_mass_log","Pollen_vector","Apomictic","Veg_repr","Family","Genus"
    ]
    pair_cols=["Dist_to_historical_log","Gowdis_traits"]
    required={"spp.name","holmkod"}|set(island_cols)|set(species_cols)|set(pair_cols)

    islands={}
    species={}
    absent=set()
    pair_state={}
    rows=0
    with safe_csv.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None:
            raise Stop("safe projection missing header")
        if "outcome" in rd.fieldnames:
            raise Stop("protected future endpoint leaked into safe projection")
        missing=sorted(required-set(rd.fieldnames))
        if missing:
            raise Stop(f"safe projection missing t0 columns: {missing}")
        for row in rd:
            rows+=1
            sp=clean(row["spp.name"]);isl=clean(row["holmkod"])
            if not sp or not isl:
                raise Stop("blank species/island routing key")
            key=(sp,isl)
            if key in absent:
                raise Stop("duplicate historical-absence event key")
            absent.add(key)
            ival=tuple(clean(row[c]) for c in island_cols)
            sval=tuple(clean(row[c]) for c in species_cols)
            pval=tuple(clean(row[c]) for c in pair_cols)
            if isl in islands and islands[isl]!=ival:
                raise Stop(f"island-state drift for {isl}")
            islands[isl]=ival
            if sp in species and species[sp]!=sval:
                raise Stop(f"species-state drift for {sp}")
            species[sp]=sval
            pair_state[key]=pval

    expected_islands=int(contract["expected_support"]["island_count"])
    if len(islands)!=expected_islands:
        raise Stop(f"unexpected island count: {len(islands)}")

    coords={}
    for isl,ival in islands.items():
        x=as_float(ival[island_cols.index("Euref_X_original")],"Euref_X_original")
        y=as_float(ival[island_cols.index("Euref_Y_original")],"Euref_Y_original")
        coords[isl]=(x,y)
    if len(set(coords.values()))!=len(coords):
        raise Stop("duplicate original EUREF island centres")

    island_ids=sorted(islands)
    species_ids=sorted(species)
    tol=float(contract["source_identity_gate"]["integer_tolerance"])
    min_exact=int(contract["source_identity_gate"]["minimum_exact_species"])

    counts_by_species={sp:0 for sp in species_ids}
    absent_by_species={sp:set() for sp in species_ids}
    for sp,isl in absent:
        counts_by_species[sp]+=1
        absent_by_species[sp].add(isl)

    species_rows=[]
    occupied_rows=[]
    absent_rows=[]
    exact_species=set()
    direct_transform_invalid=0
    incomplete_species=0
    zero_source_species=0

    for sp in species_ids:
        sval=species[sp]
        hist_log=sval[species_cols.index("Historical_total_log")]
        n_source,transform_ok,raw_source=historical_source_count(hist_log,tol)
        n_absent=counts_by_species[sp]
        if not transform_ok:
            direct_transform_invalid+=1
            status="source_count_transform_unresolved"
            source_exact=False
        elif n_absent+n_source>expected_islands:
            raise Stop(f"absence + source count exceeds island universe for {sp}")
        elif n_source==0:
            zero_source_species+=1
            status="zero_historical_sources"
            source_exact=False
        elif n_absent+n_source==expected_islands:
            status="exact_source_identity"
            source_exact=True
            exact_species.add(sp)
        else:
            incomplete_species+=1
            status="archive_absence_rows_incomplete"
            source_exact=False

        species_rows.append({
          "spp.name":sp,
          "archived_absent_row_count":n_absent,
          "historical_source_count":n_source if transform_ok else "",
          "historical_source_count_raw_inverse":raw_source if transform_ok else "",
          "source_identity_status":status,
          "source_identity_exact":int(source_exact),
          **{c:v for c,v in zip(species_cols,sval)}
        })

        if source_exact:
            source_islands=[isl for isl in island_ids if isl not in absent_by_species[sp]]
            if len(source_islands)!=n_source:
                raise Stop(f"source complement arithmetic drift for {sp}")
            occupied_rows.extend({"spp.name":sp,"holmkod":isl} for isl in source_islands)

            for target in sorted(absent_by_species[sp]):
                tx,ty=coords[target]
                nearest=min(math.hypot(tx-coords[src][0],ty-coords[src][1]) for src in source_islands)
                dist_log,gowdis=pair_state[(sp,target)]
                absent_rows.append({
                  "spp.name":sp,"holmkod":target,
                  "source_identity_exact":1,
                  "recomputed_nearest_source_distance_euref":format(nearest,".17g"),
                  "archived_Dist_to_historical_log":dist_log,
                  "Gowdis_traits":gowdis
                })
        else:
            for target in sorted(absent_by_species[sp]):
                dist_log,gowdis=pair_state[(sp,target)]
                absent_rows.append({
                  "spp.name":sp,"holmkod":target,
                  "source_identity_exact":0,
                  "recomputed_nearest_source_distance_euref":"",
                  "archived_Dist_to_historical_log":dist_log,
                  "Gowdis_traits":gowdis
                })

    island_rows=[
      {"holmkod":isl,**{c:v for c,v in zip(island_cols,islands[isl])}}
      for isl in island_ids
    ]
    exact_event_rows=sum(counts_by_species[sp] for sp in exact_species)

    write_csv(outdir/"sw_finland_t0_island_state.csv",["holmkod"]+island_cols,island_rows)
    write_csv(
      outdir/"sw_finland_t0_species_state.csv",
      ["spp.name","archived_absent_row_count","historical_source_count",
       "historical_source_count_raw_inverse","source_identity_status","source_identity_exact"]+species_cols,
      species_rows
    )
    write_csv(
      outdir/"sw_finland_t0_historical_absent_pairs.csv",
      ["spp.name","holmkod","source_identity_exact","recomputed_nearest_source_distance_euref",
       "archived_Dist_to_historical_log","Gowdis_traits"],
      absent_rows
    )
    write_csv(outdir/"sw_finland_t0_historical_occupied_pairs.csv",["spp.name","holmkod"],occupied_rows)

    qualified=len(exact_species)>=min_exact
    result={
      "schema":"structural.sw_finland_t0_projection_result.v1_164",
      "status":(
        "T0_EXACT_SOURCE_SUPPORT_QUALIFIED_FUTURE_OUTCOME_REMAINS_SEALED"
        if qualified else
        "STOP_INSUFFICIENT_EXACT_SOURCE_IDENTITY"
      ),
      "candidate_id":contract["candidate_id"],
      "raw_mixed_file_sha256":router_receipt.get("raw_mixed_file_sha256"),
      "safe_projection_sha256":fsha(safe_csv),
      "archived_event_rows":rows,
      "island_count":len(islands),
      "archive_species_count":len(species),
      "exact_source_species_count":len(exact_species),
      "minimum_exact_source_species_required":min_exact,
      "exact_source_event_row_count":exact_event_rows,
      "incomplete_species_count":incomplete_species,
      "zero_source_species_count":zero_source_species,
      "source_count_transform_unresolved_species_count":direct_transform_invalid,
      "historical_occupied_pair_count_exact_species":len(occupied_rows),
      "protected_field_values_decoded":0,
      "protected_field_bytes_persisted":0,
      "outcome_values_read":0,
      "future_outcome_opened":False,
      "model_fit_count":0,
      "counts_as_empirical_evidence":False,
      "graph_freeze_may_proceed":qualified,
      "next_action":(
        "freeze eligible exact-source species, graph/null topology and spatial validation before future outcome access"
        if qualified else
        "STOP/HOLD before future outcome; exact historical source identity support is insufficient"
      )
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"sw_finland_t0_projection_receipt.json").write_text(
      json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("safe_csv",type=Path)
    ap.add_argument("--router-receipt",type=Path,required=True)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--firewall",type=Path,default=DEFAULT_FIREWALL)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    try:
        r=project(
          a.safe_csv,load_json(a.router_receipt),load_json(a.contract),
          load_json(a.firewall),a.output_dir
        )
        code=0 if r["graph_freeze_may_proceed"] else 2
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_t0_projection_result.v1_164",
          "status":"STOP_T0_PROJECTION","reason":str(exc),
          "protected_field_values_decoded":0,"protected_field_bytes_persisted":0,
          "outcome_values_read":0,"future_outcome_opened":False,
          "graph_freeze_may_proceed":False,"counts_as_empirical_evidence":False
        }
        code=2
    print(json.dumps(r,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
