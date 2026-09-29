#!/usr/bin/env python3
"""Freeze exact GIFT pilot and confirmatory list_ID surfaces without species access."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_pilot_list_router_contract_v1_50.json"
class Stop(RuntimeError): pass

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def truthy_num(x):
    try:return int(float(str(x).strip()))
    except Exception as exc: raise Stop("invalid metadata flag") from exc

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("metadata",type=Path); ap.add_argument("partition",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--pilot-output",type=Path,required=True)
    ap.add_argument("--confirmatory-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.gift_pilot_list_router_contract.v1_50": raise Stop("contract schema drift")
        if sha(a.metadata)!=c["metadata_input"]["metadata_sha256"]: raise Stop("metadata SHA mismatch")
        if sha(a.partition)!=c["partition_input"]["partition_sha256"]: raise Stop("partition SHA mismatch")
        with a.metadata.open("r",encoding="utf-8",newline="") as h: meta=list(csv.DictReader(h))
        with a.partition.open("r",encoding="utf-8",newline="") as h: part=list(csv.DictReader(h))
        if len(meta)!=c["metadata_input"]["expected_rows"]: raise Stop("metadata row count drift")
        if len(part)!=c["partition_input"]["expected_primary_islands"]: raise Stop("partition row count drift")
        if len({r["entity_ID"] for r in part})!=len(part): raise Stop("partition entity IDs not unique")
        split={r["entity_ID"]:r["split"] for r in part}
        if sum(v=="pilot" for v in split.values())!=c["partition_input"]["expected_pilot_islands"]: raise Stop("pilot island count drift")
        if sum(v=="confirmatory" for v in split.values())!=c["partition_input"]["expected_confirmatory_islands"]: raise Stop("confirmatory island count drift")

        rows=[]
        for r in meta:
            eid=str(r["entity_ID"])
            if eid not in split: continue
            if truthy_num(r["restricted"])!=0: raise Stop("restricted list reached primary population")
            if truthy_num(r["suit_geo"])!=1: raise Stop("suit_geo false list reached primary population")
            if truthy_num(r["native_indicated"])!=1: raise Stop("native status unavailable in primary population")
            rows.append({"entity_ID":eid,"list_ID":str(r["list_ID"]),"ref_ID":str(r["ref_ID"]),"split":split[eid]})
        if len({r["list_ID"] for r in rows})!=len(rows): raise Stop("duplicate list_ID in primary list surface")
        pilot=sorted([r for r in rows if r["split"]=="pilot"],key=lambda r:(int(r["entity_ID"]),int(r["list_ID"])))
        confirm=sorted([r for r in rows if r["split"]=="confirmatory"],key=lambda r:(int(r["entity_ID"]),int(r["list_ID"])))
        if len(pilot)!=c["router"]["expected_pilot_list_ID_count"]: raise Stop("pilot list_ID count drift")
        if len(confirm)!=c["router"]["expected_confirmatory_list_ID_count"]: raise Stop("confirmatory list_ID count drift")
        a.pilot_output.parent.mkdir(parents=True,exist_ok=True)
        fields=["entity_ID","list_ID","ref_ID"]
        for path,data in [(a.pilot_output,pilot),(a.confirmatory_output,confirm)]:
            with path.open("w",encoding="utf-8",newline="") as h:
                w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); w.writeheader()
                for r in data:w.writerow({k:r[k] for k in fields})
        result={
          "schema":"structural.gift_pilot_list_router_result.v1_50",
          "status":"PILOT_AND_CONFIRMATORY_LIST_IDS_FROZEN_WITHOUT_SPECIES_ACCESS",
          "primary_islands":len(split),
          "pilot_islands":sum(v=="pilot" for v in split.values()),
          "confirmatory_islands":sum(v=="confirmatory" for v in split.values()),
          "primary_list_IDs":len(rows),"pilot_list_IDs":len(pilot),"confirmatory_list_IDs":len(confirm),
          "pilot_lists_sha256":sha(a.pilot_output),"confirmatory_lists_sha256":sha(a.confirmatory_output),
          "species_API_called":False,"species_rows_opened":0,
          "pilot_species_response_authorized":False,"confirmatory_species_response_authorized":False,
          "counts_as_empirical_evidence":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={"schema":"structural.gift_pilot_list_router_result.v1_50","status":"STOP","reason":str(e),
          "species_API_called":False,"species_rows_opened":0,"pilot_species_response_authorized":False,
          "confirmatory_species_response_authorized":False,"counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
