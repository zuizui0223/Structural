#!/usr/bin/env python3
"""Freeze exact GIFT pilot/confirmatory entity and list routing without species access."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/gift_pilot_routing_contract_v1_51.json"
class Stop(RuntimeError):pass
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def write_rows(path,header,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",encoding="utf-8",newline="") as h:
  w=csv.writer(h,lineterminator="\n");w.writerow(header);w.writerows(rows)
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("lists",type=Path);ap.add_argument("partition",type=Path)
 ap.add_argument("--pilot-entities",type=Path,required=True);ap.add_argument("--pilot-lists",type=Path,required=True)
 ap.add_argument("--confirm-entities",type=Path,required=True);ap.add_argument("--confirm-lists",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True);a=ap.parse_args()
 try:
  c=json.loads(CONTRACT.read_text())
  if sha(a.lists)!=c["inputs"]["retained_lists_sha256"]:raise Stop("retained lists SHA drift")
  with a.lists.open(encoding="utf-8",newline="") as h:lists=list(csv.DictReader(h))
  with a.partition.open(encoding="utf-8",newline="") as h:part=list(csv.DictReader(h))
  pids={str(r["entity_ID"]) for r in part if r["split"]=="pilot"}
  cids={str(r["entity_ID"]) for r in part if r["split"]=="confirmatory"}
  if len(pids)!=99 or len(cids)!=404 or pids&cids:raise Stop("partition drift")
  list_by_entity={}
  for r in lists:
   eid=str(r["entity_ID"]); lid=str(r["list_ID"]); rid=str(r["ref_ID"])
   list_by_entity.setdefault(eid,[]).append((lid,rid))
  if any(eid not in list_by_entity for eid in pids|cids):raise Stop("primary entity lacks retained list routing")
  prows=[];crows=[]
  for eid in sorted(pids,key=lambda x:int(float(x))):
   for lid,rid in sorted(set(list_by_entity[eid]),key=lambda x:(int(float(x[0])),int(float(x[1])))):
    prows.append((eid,lid,rid))
  for eid in sorted(cids,key=lambda x:int(float(x))):
   for lid,rid in sorted(set(list_by_entity[eid]),key=lambda x:(int(float(x[0])),int(float(x[1])))):
    crows.append((eid,lid,rid))
  plids={r[1] for r in prows};clids={r[1] for r in crows}
  if plids&clids:raise Stop("list_ID shared across pilot and confirmatory entities")
  write_rows(a.pilot_entities,["entity_ID"],[(x,) for x in sorted(pids,key=lambda x:int(float(x)))])
  write_rows(a.confirm_entities,["entity_ID"],[(x,) for x in sorted(cids,key=lambda x:int(float(x)))])
  write_rows(a.pilot_lists,["entity_ID","list_ID","ref_ID"],prows)
  write_rows(a.confirm_lists,["entity_ID","list_ID","ref_ID"],crows)
  out={"schema":"structural.gift_pilot_routing_result.v1_51","status":"PRISTINE_PLANT_PILOT_ROUTING_FROZEN","pilot_entities":len(pids),"confirmatory_entities":len(cids),"pilot_list_rows":len(prows),"confirmatory_list_rows":len(crows),"unique_pilot_list_IDs":len(plids),"unique_confirmatory_list_IDs":len(clids),"pilot_entities_sha256":sha(a.pilot_entities),"pilot_lists_sha256":sha(a.pilot_lists),"confirmatory_entities_sha256":sha(a.confirm_entities),"confirmatory_lists_sha256":sha(a.confirm_lists),"GIFT_checklists_raw_called":False,"species_composition_opened":False,"species_response_authorized":False,"counts_as_empirical_evidence":False};code=0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  out={"schema":"structural.gift_pilot_routing_result.v1_51","status":"STOP","reason":str(e),"GIFT_checklists_raw_called":False,"species_composition_opened":False,"species_response_authorized":False,"counts_as_empirical_evidence":False};code=2
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
