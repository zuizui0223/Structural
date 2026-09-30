#!/usr/bin/env python3
"""Score the nonconfirmatory endpoint-available GIFT surface using original frozen predictions."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import defaultdict
from pathlib import Path

MAGIC=b"STRUCTURAL_GIFT_PRED_V1\n"
class Stop(RuntimeError): pass

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def load(p):
 with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def logloss(p,y):
 return -math.log(p) if y==1 else -math.log1p(-p)

def type7(v,p):
 x=sorted(v);h=(len(x)-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
 return x[lo] if lo==hi else x[lo]*(hi-h)+x[hi]*(h-lo)

def parse_pred(p):
 raw=p.read_bytes()
 if not raw.startswith(MAGIC):raise Stop("prediction magic drift")
 off=len(MAGIC); ne,ns=struct.unpack_from("<II",raw,off);off+=8
 vals=list(struct.iter_unpack("<dd",memoryview(raw)[off:]))
 if len(vals)!=ne*ns:raise Stop("prediction size drift")
 return ne,ns,vals

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("predictions",type=Path);ap.add_argument("entity_order",type=Path)
 ap.add_argument("universe",type=Path);ap.add_argument("matrix",type=Path);ap.add_argument("response_receipt",type=Path)
 ap.add_argument("--block-output",type=Path,required=True);ap.add_argument("--result",type=Path,required=True)
 a=ap.parse_args()
 try:
  if sha(a.predictions)!="3c87379be8081edd05ad42e56a8b58a39b2ff75e15ba75993147fb21a0992db4":raise Stop("original prediction SHA drift")
  if sha(a.entity_order)!="22d61a3915ea2786f2ff2d34e9d4485b14cc5da5a22f197b72511885034fd663":raise Stop("entity order SHA drift")
  if sha(a.universe)!="6b92ebfa7e3c242f0cffde3e91f9ff05c821b2ca242638a0ead6f6f0591e4bce":raise Stop("species universe SHA drift")
  rr=json.loads(a.response_receipt.read_text())
  if rr.get("status")!="NONCONFIRMATORY_ENDPOINT_AVAILABLE_RESPONSE_FROZEN":raise Stop("response receipt did not qualify")
  if sha(a.matrix)!=rr.get("matrix_sha256"):raise Stop("matrix SHA drift")
  er=load(a.entity_order);ur=load(a.universe);mr=load(a.matrix)
  entity_ids=[str(r["entity_ID"]) for r in er];species_ids=[str(r["work_ID"]) for r in ur]
  eidx={e:i for i,e in enumerate(entity_ids)};sidx={s:i for i,s in enumerate(species_ids)}
  ne,ns,pairs=parse_pred(a.predictions)
  if (ne,ns)!=(404,224):raise Stop("prediction shape drift")
  byentity=defaultdict(dict);positives=0
  for r in mr:
   eid=str(r["entity_ID"]);wid=str(r["work_ID"]);y=int(r["y"])
   if eid not in eidx or wid not in sidx or y not in (0,1):raise Stop("matrix key/domain drift")
   if wid in byentity[eid]:raise Stop("duplicate matrix cell")
   byentity[eid][wid]=y;positives+=y
  retained=sorted(byentity,key=lambda e:eidx[e])
  if len(retained)!=int(rr["retained_entities"]):raise Stop("retained entity count drift")
  byblock=defaultdict(list);block_islands=defaultdict(set)
  for eid in retained:
   if len(byentity[eid])!=224:raise Stop("incomplete retained entity matrix")
   i=eidx[eid]; block=str(er[i]["archip"]).strip()
   if not block:raise Stop("blank block")
   for wid in species_ids:
    j=sidx[wid]; p3,pc=pairs[i*224+j];y=byentity[eid][wid]
    byblock[block].append(logloss(pc,y)-logloss(p3,y))
   block_islands[block].add(eid)
  names=sorted(byblock)
  if not names:raise Stop("no retained blocks")
  means={b:math.fsum(byblock[b])/len(byblock[b]) for b in names}
  point=math.fsum(means.values())/len(names)
  rng=random.Random(20260930);boot=[]
  for _ in range(10000):
   vals=[means[names[rng.randrange(len(names))]] for _ in names]
   boot.append(math.fsum(vals)/len(vals))
  low,high=type7(boot,0.025),type7(boot,0.975)
  a.block_output.parent.mkdir(parents=True,exist_ok=True)
  with a.block_output.open("w",encoding="utf-8",newline="") as h:
   w=csv.writer(h,lineterminator="\n");w.writerow(["archip","islands","targets","mean_C_minus_R3_logloss"])
   for b in names:w.writerow([b,len(block_islands[b]),len(byblock[b]),repr(means[b])])
  out={
   "schema":"structural.gift_exploratory_availability_scoring_result.v1_78",
   "status":"NONCONFIRMATORY_ENDPOINT_AVAILABLE_GIFT_PRIMARY_SCORED_ONCE",
   "retained_entities":len(retained),"excluded_entities":404-len(retained),
   "retained_blocks":len(names),"dropped_empty_blocks":59-len(names),
   "focal_species":224,"target_rows":len(retained)*224,
   "target_positive":positives,"target_negative":len(retained)*224-positives,
   "point_estimate_C_minus_R3_logloss":point,
   "bootstrap_ci95_low":low,"bootstrap_ci95_high":high,
   "bootstrap_replicates":10000,"bootstrap_seed":20260930,
   "directional_support_exploratory":point<0 and high<0,
   "prediction_sha256":sha(a.predictions),"matrix_sha256":sha(a.matrix),"block_scores_sha256":sha(a.block_output),
   "fresh_status_restored":False,"counts_as_fresh_confirmatory_evidence":False,
   "counts_as_primary_confirmatory_evidence":False,"fresh_system_denominator_contribution":0,
   "rerun_authorized":False
  }
  a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return 0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  out={"schema":"structural.gift_exploratory_availability_scoring_result.v1_78","status":"STOP","reason":str(e),"fresh_status_restored":False,"counts_as_fresh_confirmatory_evidence":False,"fresh_system_denominator_contribution":0}
  a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return 2
if __name__=="__main__":raise SystemExit(main())
