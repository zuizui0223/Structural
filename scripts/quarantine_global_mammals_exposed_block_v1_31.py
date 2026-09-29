#!/usr/bin/env python3
"""Quarantine the entire pre-frozen v1.25 block containing exposed ID=1."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_contamination_quarantine_contract_v1_31.json"
class Stop(RuntimeError): pass

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()

def q7(values,p):
 xs=sorted(values)
 if not xs: raise Stop("empty quantile input")
 if len(xs)==1:return xs[0]
 h=(len(xs)-1)*p; lo=math.floor(h); hi=math.ceil(h)
 if lo==hi:return xs[lo]
 f=h-lo; return xs[lo]*(1-f)+xs[hi]*f

def load_csv(path,expected_sha):
 if sha(path)!=expected_sha: raise Stop(f"{path.name} SHA mismatch")
 with path.open("r",encoding="utf-8",newline="") as h:
  return list(csv.DictReader(h))

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("partition",type=Path); ap.add_argument("blocks",type=Path)
 ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
 ap.add_argument("--output-partition",type=Path,required=True); ap.add_argument("--output-blocks",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True); a=ap.parse_args()
 try:
  c=json.loads(a.contract.read_text())
  if c["schema"]!="structural.global_mammals_contamination_quarantine_contract.v1_31": raise Stop("contract schema drift")
  rows=load_csv(a.partition,c["spatial_artifact"]["island_partition_sha256"])
  blocks=load_csv(a.blocks,c["spatial_artifact"]["block_table_sha256"])
  exposed=c["known_exposure"]["source_local_row_id"]
  hit=[r for r in rows if str(r["ID"]).strip()==exposed]
  if len(hit)!=1: raise Stop("exposed ID not uniquely present in v1.25 partition")
  qblock=hit[0]["block_id"]; qkey=hit[0]["block_key"]; qsplit=hit[0]["split"]; qregion=hit[0]["bioregion"]
  quarantined=[r for r in rows if r["block_id"]==qblock]
  retained=[r for r in rows if r["block_id"]!=qblock]
  if not quarantined: raise Stop("quarantine block empty")
  retained_blocks=[b for b in blocks if b["block_id"]!=qblock]
  if len(retained)+len(quarantined)!=len(rows): raise Stop("partition accounting failure")
  if any(r["ID"]==exposed for r in retained): raise Stop("exposed ID survived quarantine")
  if any(r["block_id"]==qblock for r in retained): raise Stop("quarantine block survived")
  by_region=Counter((b["bioregion"],b["split"]) for b in retained_blocks)
  for region in sorted(set(b["bioregion"] for b in retained_blocks)):
   if by_region[(region,"pilot")]<c["post_quarantine_design"]["minimum_pilot_blocks_per_bioregion"]: raise Stop(f"pilot minimum failed: {region}")
   if by_region[(region,"confirmatory")]<c["post_quarantine_design"]["minimum_confirmatory_blocks_per_bioregion"]: raise Stop(f"confirmatory minimum failed: {region}")
  confirm=[float.fromhex(r["Current_isolation_hex"]) for r in retained if r["split"]=="confirmatory"]
  q75=q7(confirm,0.75)
  extreme=sum(1 for r in retained if r["split"]=="confirmatory" and float.fromhex(r["Current_isolation_hex"])>=q75)
  fieldnames=list(rows[0].keys())
  a.output_partition.parent.mkdir(parents=True,exist_ok=True)
  with a.output_partition.open("w",encoding="utf-8",newline="") as h:
   w=csv.DictWriter(h,fieldnames=fieldnames,lineterminator="\n"); w.writeheader(); w.writerows(retained)
  bfields=list(blocks[0].keys())
  with a.output_blocks.open("w",encoding="utf-8",newline="") as h:
   w=csv.DictWriter(h,fieldnames=bfields,lineterminator="\n"); w.writeheader(); w.writerows(retained_blocks)
  receipt={
   "schema":"structural.global_mammals_contamination_quarantine_result.v1_31",
   "status":"KNOWN_EXPOSURE_BLOCK_QUARANTINED",
   "candidate_id":c["candidate_id"],"analysis_route":c["analysis_route"],
   "exposed_id":exposed,"quarantined_block_id":qblock,"quarantined_block_key":qkey,
   "quarantined_block_split":qsplit,"quarantined_block_bioregion":qregion,
   "quarantined_island_count":len(quarantined),
   "retained_island_count":len(retained),"retained_block_count":len(retained_blocks),
   "retained_pilot_blocks":sum(b["split"]=="pilot" for b in retained_blocks),
   "retained_confirmatory_blocks":sum(b["split"]=="confirmatory" for b in retained_blocks),
   "retained_pilot_islands":sum(r["split"]=="pilot" for r in retained),
   "retained_confirmatory_islands":sum(r["split"]=="confirmatory" for r in retained),
   "current_isolation_q75_hex":q75.hex(),"extreme_confirmatory_island_count":extreme,
   "partition_sha256":sha(a.output_partition),"block_table_sha256":sha(a.output_blocks),
   "Appendix1_reopened":False,"mammal_occurrence_values_opened":False,
   "fresh_status_restored":False,"counts_as_fresh_confirmation":False,
   "fresh_system_denominator_contribution":0,"macro_reference_may_be_built":True
  }
  a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(json.dumps(receipt,indent=2,sort_keys=True)); return 0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
  result={"schema":"structural.global_mammals_contamination_quarantine_result.v1_31","status":"STOP","reason":str(e),"Appendix1_reopened":False,"mammal_occurrence_values_opened":False,"fresh_status_restored":False,"counts_as_fresh_confirmation":False,"fresh_system_denominator_contribution":0}
  a.receipt.parent.mkdir(parents=True,exist_ok=True); a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(json.dumps(result,indent=2,sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())
