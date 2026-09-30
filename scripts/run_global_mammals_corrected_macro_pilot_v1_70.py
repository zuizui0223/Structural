#!/usr/bin/env python3
"""One-shot corrected mammal macro pilot for the nonconfirmatory lineage."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,re,tempfile
from pathlib import Path
from scripts.fetch_global_mammal_response_opaque_v1_17 import transport as transport_v117,GlobalMammalTransportError

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_corrected_macro_pilot_contract_v1_70.json"
DIGITS=re.compile(r"^[0-9]+$")
class Stop(RuntimeError):pass

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def iter_records(raw):
 start=0;inq=False;i=0
 while i<len(raw):
  b=raw[i]
  if b==34:
   if inq and i+1<len(raw) and raw[i+1]==34:i+=2;continue
   inq=not inq;i+=1;continue
  if b==10 and not inq:
   rec=raw[start:i]
   if rec.endswith(b"\r"):rec=rec[:-1]
   yield rec;start=i+1
  i+=1
 if inq:raise Stop("unterminated quoted record")
 if start<len(raw):
  rec=raw[start:]
  if rec.endswith(b"\r"):rec=rec[:-1]
  if rec:yield rec

def first_field(record,delimiter=59):
 out=bytearray();inq=False;i=0;at_start=True
 while i<len(record):
  b=record[i]
  if inq:
   if b==34:
    if i+1<len(record) and record[i+1]==34:out.append(34);i+=2;continue
    inq=False;i+=1;continue
   out.append(b);i+=1;continue
  if at_start and b==34:inq=True;at_start=False;i+=1;continue
  if b==delimiter:return bytes(out)
  out.append(b);at_start=False;i+=1
 if inq:raise Stop("unterminated first field")
 return bytes(out)

def parse_record(record):
 try:text=record.decode("utf-8-sig")
 except UnicodeDecodeError as e:raise Stop("opened record not UTF-8") from e
 rows=list(csv.reader(io.StringIO(text),delimiter=";",quotechar='"'))
 if len(rows)!=1:raise Stop("logical record parse drift")
 return rows[0]

def canon_id(raw):
 try:s=raw.decode("utf-8").strip()
 except UnicodeDecodeError as e:raise Stop("routing ID not UTF-8") from e
 if len(s)>=2 and s[0]=='"' and s[-1]=='"':s=s[1:-1].replace('""','"')
 s=s.strip()
 if DIGITS.fullmatch(s) is None:raise Stop("routing ID not unsigned decimal")
 return str(int(s,10))

def load_routing(path,expected_sha,expected_n):
 if sha(path)!=expected_sha:raise Stop("routing SHA drift")
 with path.open(encoding="utf-8",newline="") as h:rows=list(csv.DictReader(h))
 if len(rows)!=expected_n:raise Stop("routing row-count drift")
 if not rows or tuple(rows[0].keys())!=("ID","block_id","bioregion"):raise Stop("routing header drift")
 order=[];meta={}
 for r in rows:
  iid=str(int(str(r["ID"]).strip(),10))
  if iid in meta:raise Stop("duplicate routing ID")
  order.append(iid);meta[iid]=r
 return order,meta

def load_manifest(path,expected_sha):
 if sha(path)!=expected_sha:raise Stop("corrected manifest SHA drift")
 with path.open(encoding="utf-8",newline="") as h:rows=list(csv.DictReader(h))
 if len(rows)!=5394:raise Stop("corrected manifest species count drift")
 if tuple(rows[0].keys())!=("species_index","data_column_index","species_name"):raise Stop("corrected manifest header drift")
 names=[]
 for j,r in enumerate(rows):
  if int(r["species_index"])!=j or int(r["data_column_index"])!=j+2:raise Stop("corrected manifest index drift")
  n=str(r["species_name"])
  if not n.strip():raise Stop("blank corrected species name")
  names.append(n)
 if len(set(names))!=len(names):raise Stop("duplicate corrected species name")
 return rows,names

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
 ap.add_argument("--manifest",type=Path,required=True)
 ap.add_argument("--pilot-routing",type=Path,required=True)
 ap.add_argument("--confirmatory-routing",type=Path,required=True)
 ap.add_argument("--species-universe",type=Path,required=True)
 ap.add_argument("--pilot-matrix",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args();occ_started=False
 try:
  c=json.loads(a.contract.read_text())
  if c.get("schema")!="structural.global_mammals_corrected_macro_pilot_contract.v1_70":raise Stop("contract schema drift")
  manifest,names=load_manifest(a.manifest,c["schema_parent"]["corrected_manifest_sha256"])
  pilot_order,pmeta=load_routing(a.pilot_routing,c["routing"]["pilot_ids_sha256"],c["routing"]["pilot_islands"])
  conf_order,_=load_routing(a.confirmatory_routing,c["routing"]["confirmatory_ids_sha256"],c["routing"]["confirmatory_islands"])
  pset=set(pilot_order);cset=set(conf_order)
  if pset&cset or len(pset|cset)!=5401:raise Stop("routing population drift")
  t=c["response_identity"]
  tc={"candidate_id":c["candidate_id"],"target":{"name":t["name"],"dryad_file_id":t["dryad_file_id"],"download_url":t["download_url"],"expected_size_bytes":t["expected_size_bytes"],"expected_sha256":t["expected_sha256"]},"attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/t["name"]
   tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
   if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":raise Stop("response transport failed")
   raw=p.read_bytes()
  records=iter(iter_records(raw))
  try:hrec=next(records)
  except StopIteration as e:raise Stop("empty response") from e
  header=parse_record(hrec)
  if header!=names:raise Stop("response header does not exactly equal corrected species manifest")
  counts=[0]*5394;pilot_values={};data_rows=pilot_n=conf_n=excluded_n=0
  for rec in records:
   if not rec:continue
   data_rows+=1;iid=canon_id(first_field(rec,59))
   if iid in pset:
    occ_started=True
    fields=parse_record(rec)
    if len(fields)!=5395:raise Stop("pilot data-record field-count drift")
    if canon_id(fields[0].encode("utf-8"))!=iid:raise Stop("pilot routing field parse disagreement")
    vals=fields[1:]
    row=[]
    for j,v in enumerate(vals):
     if v not in ("0","1"):raise Stop("pilot occurrence outside 0/1")
     y=int(v);row.append(y);counts[j]+=y
    if iid in pilot_values:raise Stop("duplicate pilot response row")
    pilot_values[iid]=row;pilot_n+=1
   elif iid in cset:
    conf_n+=1
   else:
    excluded_n+=1
  if data_rows!=5592:raise Stop("response row-count drift")
  if pilot_n!=1275 or set(pilot_values)!=pset:raise Stop("pilot row coverage drift")
  if conf_n!=4126:raise Stop("confirmatory routing-only count drift")
  if excluded_n!=191:raise Stop("excluded routing-only count drift")
  m=13
  selected=[j for j,x in enumerate(counts) if x>=m and 1275-x>=m]
  if not selected:raise Stop("fixed m=13 rule selected zero species")
  a.species_universe.parent.mkdir(parents=True,exist_ok=True)
  with a.species_universe.open("w",encoding="utf-8",newline="") as h:
   w=csv.writer(h,lineterminator="\n");w.writerow(["species_index","source_species_index","data_column_index","species_name","pilot_presence","pilot_absence"])
   for k,j in enumerate(selected):w.writerow([k,j,j+2,names[j],counts[j],1275-counts[j]])
  labels=[f"S{k:05d}" for k in range(len(selected))]
  with a.pilot_matrix.open("w",encoding="utf-8",newline="") as h:
   w=csv.writer(h,lineterminator="\n");w.writerow(["ID","block_id","bioregion"]+labels)
   for iid in pilot_order:
    r=pmeta[iid];vals=pilot_values[iid]
    w.writerow([iid,r["block_id"],r["bioregion"]]+[vals[j] for j in selected])
  positives=sum(counts[j] for j in selected)
  result={
   "schema":"structural.global_mammals_corrected_macro_pilot_result.v1_70",
   "status":"CORRECTED_NONCONFIRMATORY_MACRO_PILOT_CONSUMED",
   "candidate_id":c["candidate_id"],
   "source_species":5394,
   "pilot_islands":1275,
   "confirmatory_islands_seen_routing_only":4126,
   "excluded_islands_seen_routing_only":191,
   "pilot_occurrence_values_decoded":1275*5394,
   "confirmatory_occurrence_values_decoded":0,
   "excluded_occurrence_values_decoded":0,
   "species_threshold_m":13,
   "focal_species":len(selected),
   "pilot_matrix_cells":1275*len(selected),
   "pilot_matrix_positive":positives,
   "pilot_matrix_negative":1275*len(selected)-positives,
   "species_universe_sha256":sha(a.species_universe),
   "pilot_matrix_sha256":sha(a.pilot_matrix),
   "pilot_response_consumed":True,
   "confirmatory_response_authorized":False,
   "fresh_status_restored":False,
   "counts_as_fresh_confirmation":False,
   "fresh_system_denominator_contribution":0,
   "next_action":"freeze v1.67 R0-R3-C models and all 4126-island confirmatory predictions before any confirmatory occurrence access"
  };code=0
 except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
  result={"schema":"structural.global_mammals_corrected_macro_pilot_result.v1_70","status":"TERMINAL_AFTER_PILOT_OCCURRENCE_ACCESS" if occ_started else "HOLD_BEFORE_PILOT_OCCURRENCE_ACCESS","reason":str(e),"pilot_response_consumed":occ_started,"confirmatory_occurrence_values_decoded":0,"excluded_occurrence_values_decoded":0,"confirmatory_response_authorized":False,"fresh_status_restored":False,"counts_as_fresh_confirmation":False,"fresh_system_denominator_contribution":0};code=2
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
