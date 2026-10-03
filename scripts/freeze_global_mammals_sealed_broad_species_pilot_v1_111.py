#!/usr/bin/env python3
"""Freeze a very-broad mammal species layer from already-open pilot rows only.

Membership is fixed prospectively to species with 1-12 pilot absences.
Heldout rows are routed by their first field only; no heldout occurrence field
is decoded.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,os,tempfile
from pathlib import Path

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError, transport as transport_v117,
)
from scripts.run_global_mammals_macro_pilot_response_v1_65 import (
    iter_records, first_field_bytes, parse_full_record, canon_id_bytes, load_routing,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_sealed_broad_species_pilot_contract_v1_111.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def species_fp(names:list[str])->str:
    h=hashlib.sha256()
    for n in names:
        h.update(n.encode("utf-8"));h.update(b"\n")
    return h.hexdigest()

def load_manifest(path:Path,expected_fp:str)->list[str]:
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    if len(rows)!=5394: raise Stop("species manifest count drift")
    names=[]
    for j,r in enumerate(rows):
        if int(r["species_index"])!=j or int(r["data_column_index"])!=j+2:
            raise Stop("species manifest index drift")
        names.append(str(r["species_name"]))
    if len(set(names))!=len(names):raise Stop("duplicate species names")
    if species_fp(names)!=expected_fp:raise Stop("species-order fingerprint drift")
    return names

def consume(raw:bytes,species:list[str],pilot_order:list[str],pilot_meta:dict[str,dict],heldout_order:list[str],c:dict):
    records=iter(iter_records(raw))
    try: header_rec=next(records)
    except StopIteration as e: raise Stop("empty response") from e
    if parse_full_record(header_rec)!=species:raise Stop("header/schema mismatch")

    pilot_set=set(pilot_order);heldout_set=set(heldout_order)
    nsp=len(species);counts=[0]*nsp;pilot_values={}
    data_rows=pilot_decoded=heldout_seen=excluded_seen=0

    for rec in records:
        if not rec:continue
        data_rows+=1
        iid=canon_id_bytes(first_field_bytes(rec,59))
        if iid in pilot_set:
            fields=parse_full_record(rec)
            if len(fields)!=nsp+1:raise Stop("pilot field-count drift")
            vals=fields[1:];row=[]
            for j,v in enumerate(vals):
                if v not in ("0","1"):raise Stop("pilot target outside binary domain")
                y=1 if v=="1" else 0
                row.append(y);counts[j]+=y
            if iid in pilot_values:raise Stop("duplicate pilot row")
            pilot_values[iid]=row;pilot_decoded+=1
        elif iid in heldout_set:
            # Crucial firewall: no full record parse and no occurrence decode.
            heldout_seen+=1
        else:
            excluded_seen+=1

    if data_rows!=5592 or pilot_decoded!=1275 or heldout_seen!=4126 or excluded_seen!=191:
        raise Stop("routing count drift")
    if set(pilot_values)!=pilot_set:raise Stop("pilot support incomplete")

    rule=c["broad_layer_rule"]
    amin=int(rule["pilot_absence_min_inclusive"]);amax=int(rule["pilot_absence_max_inclusive"])
    pmin=int(rule["pilot_presence_min_inclusive"]);pmax=int(rule["pilot_presence_max_inclusive"])
    selected=[]
    for j,pres in enumerate(counts):
        absn=1275-pres
        if amin<=absn<=amax and pmin<=pres<=pmax:
            selected.append(j)

    if len(selected)<int(rule["minimum_species_count_gate"]):
        raise Stop(f"broad layer below frozen minimum species gate: {len(selected)}")

    universe=[]
    for si,j in enumerate(selected):
        pres=counts[j];absn=1275-pres
        universe.append((si,j+2,species[j],pres,absn))

    labels=[f"S{si:05d}" for si in range(len(selected))]
    matrix=[]
    for iid in pilot_order:
        m=pilot_meta[iid];vals=pilot_values[iid]
        matrix.append((iid,m["block_id"],m["bioregion"],[vals[j] for j in selected]))

    return universe,matrix,{
      "schema":"structural.global_mammals_sealed_broad_species_pilot_result.v1_111",
      "status":"BROAD_OCCUPANCY_LAYER_FROZEN_FROM_PILOT_ONLY",
      "selected_species":len(selected),
      "pilot_islands":1275,
      "pilot_presence_min":min(counts[j] for j in selected),
      "pilot_presence_max":max(counts[j] for j in selected),
      "pilot_absence_min":min(1275-counts[j] for j in selected),
      "pilot_absence_max":max(1275-counts[j] for j in selected),
      "pilot_positive_cells":sum(counts[j] for j in selected),
      "pilot_negative_cells":sum(1275-counts[j] for j in selected),
      "pilot_target_cells":1275*len(selected),
      "heldout_islands_seen_routing_only":4126,
      "heldout_occurrence_values_decoded":0,
      "excluded_occurrence_values_decoded":0,
      "heldout_broad_layer_response_still_sealed":True,
      "primary_future_prediction_frozen":"broad-layer C-minus-R3 is less favourable than original79 under paired 168-block contrast",
      "counts_as_current_empirical_result":False
    }

def write(universe,matrix,uout:Path,mout:Path):
    uout.parent.mkdir(parents=True,exist_ok=True)
    with uout.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["species_index","source_data_column_index","species_name","pilot_presence","pilot_absence"])
        w.writerows(universe)
    labels=[f"S{i:05d}" for i in range(len(universe))]
    with mout.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["ID","block_id","bioregion"]+labels)
        for iid,b,r,vals in matrix:w.writerow([iid,b,r]+vals)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--corrected-manifest",type=Path,required=True)
    ap.add_argument("--pilot-routing",type=Path,required=True)
    ap.add_argument("--heldout-routing",type=Path,required=True)
    ap.add_argument("--species-universe",type=Path,required=True)
    ap.add_argument("--pilot-matrix",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_sealed_broad_species_pilot_contract.v1_111":
            raise Stop("contract schema drift")
        species=load_manifest(a.corrected_manifest,c["physical_schema"]["species_order_sha256"])
        pilot_order,pilot_meta=load_routing(a.pilot_routing,c["routing"]["pilot_ids_sha256"],1275)
        heldout_order,_=load_routing(a.heldout_routing,c["routing"]["confirmatory_ids_sha256"],4126)
        tc={"candidate_id":c["candidate_id"],"target":{
          "name":"Appendix_1_presence_absence.csv","dryad_file_id":3242161,
          "download_url":"https://datadryad.org/api/v2/files/3242161/download",
          "expected_size_bytes":60486843,"expected_sha256":c["physical_schema"]["response_sha256"]},
          "attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"Appendix_1_presence_absence.csv"
            tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
            if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":
                raise Stop("response transport did not qualify")
            universe,matrix,result=consume(p.read_bytes(),species,pilot_order,pilot_meta,heldout_order,c)
        write(universe,matrix,a.species_universe,a.pilot_matrix)
        result["species_universe_sha256"]=sha(a.species_universe)
        result["pilot_matrix_sha256"]=sha(a.pilot_matrix)
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={
          "schema":"structural.global_mammals_sealed_broad_species_pilot_result.v1_111",
          "status":"STOP",
          "reason":str(e),
          "heldout_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,
          "heldout_broad_layer_response_still_sealed":True,
          "counts_as_current_empirical_result":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
