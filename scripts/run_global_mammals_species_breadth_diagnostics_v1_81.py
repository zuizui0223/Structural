#!/usr/bin/env python3
"""Post-hoc species-breadth diagnostics for the frozen global mammal exploratory surface."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,struct
from pathlib import Path

MAGIC=b"STRUCTURAL_MAMMAL_PRED_V1\n"
class Stop(RuntimeError): pass

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def load(p):
 with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def mean(x): return math.fsum(x)/len(x)
def median(x):
 y=sorted(x);n=len(y)
 return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2

def ranks(x):
 order=sorted(range(len(x)),key=lambda i:(x[i],i));out=[0.0]*len(x);j=0
 while j<len(order):
  k=j+1
  while k<len(order) and x[order[k]]==x[order[j]]:k+=1
  r=((j+1)+k)/2
  for i in order[j:k]:out[i]=r
  j=k
 return out

def corr(x,y):
 mx,my=mean(x),mean(y);dx=[a-mx for a in x];dy=[b-my for b in y]
 sx=math.sqrt(math.fsum(a*a for a in dx));sy=math.sqrt(math.fsum(b*b for b in dy))
 if not sx>0 or not sy>0:raise Stop("zero variance")
 return math.fsum(a*b for a,b in zip(dx,dy))/(sx*sy)

def parse_pred(p):
 raw=p.read_bytes()
 if not raw.startswith(MAGIC):raise Stop("prediction magic drift")
 off=len(MAGIC);ne,ns=struct.unpack_from("<II",raw,off);off+=8
 vals=list(struct.iter_unpack("<dd",memoryview(raw)[off:]))
 if len(vals)!=ne*ns:raise Stop("prediction size drift")
 return ne,ns,vals

def logloss(p,y):
 return -math.log(p) if y==1 else -math.log1p(-p)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("universe",type=Path);ap.add_argument("predictions",type=Path)
 ap.add_argument("entity_order",type=Path);ap.add_argument("matrix",type=Path)
 ap.add_argument("--species-output",type=Path,required=True);ap.add_argument("--quartile-output",type=Path,required=True);ap.add_argument("--result",type=Path,required=True)
 a=ap.parse_args()
 try:
  expected={
   a.universe:"c15cb86ba0b0bd88e8d22fd566c495adcec113a3c9f7dd65f4b7c3415796335e",
   a.predictions:"f48ab1f09c825f99bced712a64e7c5f1ff927d024fdbe1aaf80db588b0372ef8",
   a.entity_order:"afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715",
   a.matrix:"25db7bf42396c66452c7611503522e68b6b4262bc83770c737be43076677a252"
  }
  for p,s in expected.items():
   if sha(p)!=s:raise Stop(f"SHA drift: {p.name}")
  u=load(a.universe);e=load(a.entity_order);m=load(a.matrix)
  if len(u)!=79 or len(e)!=4126 or len(m)!=4126:raise Stop("dimension drift")
  labels=[f"S{i:05d}" for i in range(79)]
  if any(x not in m[0] for x in labels):raise Stop("matrix species columns drift")
  ne,ns,pairs=parse_pred(a.predictions)
  if (ne,ns)!=(4126,79):raise Stop("prediction shape drift")
  effects=[0.0]*79; held_pos=[0]*79
  for i,row in enumerate(m):
   for j,label in enumerate(labels):
    y=int(row[label]);p3,pc=pairs[i*79+j]
    effects[j]+=logloss(pc,y)-logloss(p3,y);held_pos[j]+=y
  effects=[x/4126 for x in effects]
  rows=[]
  for j,r in enumerate(u):
   presence=int(r["pilot_presence"])
   rows.append({
    "species_index":int(r["species_index"]),"species_name":r["species_name"],
    "pilot_presence":presence,"pilot_prevalence":presence/1275.0,
    "heldout_presence":held_pos[j],"heldout_prevalence":held_pos[j]/4126.0,
    "mean_C_minus_R3":effects[j]
   })
  rho=corr(ranks([r["pilot_prevalence"] for r in rows]),ranks([r["mean_C_minus_R3"] for r in rows]))
  ordered=sorted(rows,key=lambda r:(r["pilot_presence"],r["species_index"]))
  sizes=[20,20,20,19];quart=[];start=0
  for q,n in enumerate(sizes,1):
   g=ordered[start:start+n];start+=n;ds=[r["mean_C_minus_R3"] for r in g]
   quart.append({"quartile":q,"species":n,"pilot_presence_min":min(r["pilot_presence"] for r in g),
     "pilot_presence_max":max(r["pilot_presence"] for r in g),"mean_pilot_prevalence":mean([r["pilot_prevalence"] for r in g]),
     "mean_C_minus_R3":mean(ds),"median_C_minus_R3":median(ds),"negative_species":sum(d<0 for d in ds)})
  a.species_output.parent.mkdir(parents=True,exist_ok=True)
  with a.species_output.open("w",encoding="utf-8",newline="") as h:
   f=list(rows[0]);w=csv.DictWriter(h,fieldnames=f,lineterminator="\n");w.writeheader();w.writerows(rows)
  with a.quartile_output.open("w",encoding="utf-8",newline="") as h:
   f=list(quart[0]);w=csv.DictWriter(h,fieldnames=f,lineterminator="\n");w.writeheader();w.writerows(quart)
  out={"schema":"structural.global_mammals_species_breadth_diagnostics_result.v1_81","status":"POSTHOC_SPECIES_BREADTH_DIAGNOSTICS_COMPLETE",
   "species":79,"negative_species":sum(r["mean_C_minus_R3"]<0 for r in rows),"positive_species":sum(r["mean_C_minus_R3"]>0 for r in rows),
   "pilot_prevalence_vs_C_minus_R3_spearman_rho":rho,"quartiles":quart,
   "species_table_sha256":sha(a.species_output),"quartile_table_sha256":sha(a.quartile_output),
   "posthoc":True,"may_change_primary_status":False,"counts_as_confirmatory_evidence":False}
  a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return 0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  out={"schema":"structural.global_mammals_species_breadth_diagnostics_result.v1_81","status":"STOP","reason":str(e),"posthoc":True,"may_change_primary_status":False,"counts_as_confirmatory_evidence":False}
  a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True));return 2
if __name__=="__main__":raise SystemExit(main())
