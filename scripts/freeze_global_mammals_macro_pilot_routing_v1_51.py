#!/usr/bin/env python3
"""Freeze exact final mammal pilot/confirmatory routing IDs without response access."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/global_mammals_macro_pilot_routing_contract_v1_51.json"
class Stop(RuntimeError):pass
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("partition",type=Path);ap.add_argument("--pilot",type=Path,required=True);ap.add_argument("--confirmatory",type=Path,required=True);ap.add_argument("--receipt",type=Path,required=True);a=ap.parse_args()
 try:
  c=json.loads(CONTRACT.read_text())
  if sha(a.partition)!=c["input"]["partition_sha256"]:raise Stop("partition SHA drift")
  with a.partition.open(encoding="utf-8",newline="") as h:rows=list(csv.DictReader(h))
  pilot=sorted((r for r in rows if r["split"]=="pilot"),key=lambda r:int(r["ID"]))
  conf=sorted((r for r in rows if r["split"]=="confirmatory"),key=lambda r:int(r["ID"]))
  if len(pilot)!=1275 or len(conf)!=4126:raise Stop("routing population count drift")
  def write(path,rs):
   path.parent.mkdir(parents=True,exist_ok=True)
   with path.open("w",encoding="utf-8",newline="") as h:
    w=csv.writer(h,lineterminator="\n");w.writerow(["ID","block_id","bioregion"]);w.writerows((r["ID"],r["block_id"],r["bioregion"]) for r in rs)
  write(a.pilot,pilot);write(a.confirmatory,conf)
  out={"schema":"structural.global_mammals_macro_pilot_routing_result.v1_51","status":"MACRO_MAMMAL_PILOT_ROUTING_FROZEN","pilot_islands":len(pilot),"confirmatory_islands":len(conf),"pilot_blocks":len({r["block_id"] for r in pilot}),"confirmatory_blocks":len({r["block_id"] for r in conf}),"pilot_sha256":sha(a.pilot),"confirmatory_sha256":sha(a.confirmatory),"Appendix1_reopened":False,"species_headers_opened":False,"occurrence_values_opened":False,"macro_pilot_response_authorized":False,"counts_as_empirical_evidence":False};code=0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  out={"schema":"structural.global_mammals_macro_pilot_routing_result.v1_51","status":"STOP","reason":str(e),"Appendix1_reopened":False,"occurrence_values_opened":False,"counts_as_empirical_evidence":False};code=2
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
