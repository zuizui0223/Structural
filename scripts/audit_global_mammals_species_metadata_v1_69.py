#!/usr/bin/env python3
"""Audit the exact response-blind mammal species-insularity metadata."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,tempfile
from pathlib import Path
from scripts.fetch_global_mammal_response_opaque_v1_17 import transport as transport_v117,GlobalMammalTransportError

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_species_metadata_audit_contract_v1_69.json"
class Stop(RuntimeError):pass

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def parse_candidate(text,delimiter):
 try:
  rows=list(csv.reader(io.StringIO(text),delimiter=delimiter,quotechar='"'))
 except csv.Error:return None
 if not rows:return None
 width=len(rows[0])
 if width<2:return None
 if any(len(r)!=width for r in rows):return None
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);ap.add_argument("--receipt",type=Path,required=True);a=ap.parse_args()
 try:
  c=json.loads(a.contract.read_text())
  if c.get("schema")!="structural.global_mammals_species_metadata_audit_contract.v1_69":raise Stop("contract schema drift")
  s=c["source"]
  tc={"candidate_id":c["candidate_id"],"target":{"name":s["file_name"],"dryad_file_id":s["dryad_file_id"],"download_url":s["download_url"],"expected_size_bytes":s["expected_size_bytes"],"expected_sha256":s["expected_sha256"]},"attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/s["file_name"]
   tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
   if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":raise Stop("exact metadata transport failed")
   raw=p.read_bytes()
  try:text=raw.decode("utf-8-sig")
  except UnicodeDecodeError as e:raise Stop("species metadata is not UTF-8") from e
  candidates=[]
  for label,sep in [("comma",","),("semicolon",";"),("tab","\t")]:
   rows=parse_candidate(text,sep)
   if rows is not None:candidates.append((label,sep,rows))
  if len(candidates)!=1:raise Stop(f"delimiter not uniquely resolved: {[x[0] for x in candidates]}")
  label,sep,rows=candidates[0]
  header=rows[0];data=rows[1:]
  if len(set(header))!=len(header):raise Stop("duplicate metadata headers")
  stats={}
  for j,name in enumerate(header):
   vals=[r[j].strip() for r in data]
   stats[name]={"blank_count":sum(v=="" for v in vals),"unique_nonblank_count":len({v for v in vals if v!=""})}
  result={
   "schema":"structural.global_mammals_species_metadata_audit_result.v1_69",
   "status":"SPECIES_METADATA_SCHEMA_FROZEN_RESPONSE_BLINDLY",
   "file_sha256":hashlib.sha256(raw).hexdigest(),
   "delimiter":label,
   "header_fields":header,
   "field_count":len(header),
   "data_rows":len(data),
   "column_stats":stats,
   "species_column_selected":False,
   "Appendix1_opened":False,
   "occurrence_values_opened":False,
   "counts_as_empirical_evidence":False,
   "fresh_status_restored":False
  };code=0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
  result={"schema":"structural.global_mammals_species_metadata_audit_result.v1_69","status":"STOP","reason":str(e),"species_column_selected":False,"Appendix1_opened":False,"occurrence_values_opened":False,"counts_as_empirical_evidence":False,"fresh_status_restored":False};code=2
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
