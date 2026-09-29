#!/usr/bin/env python3
"""Project only Appendix-2 identity fields and audit overlap with the historical
318-source / 309-analyzed mammal system. No Appendix-1 or occurrence access.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,re,unicodedata,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from scripts.project_global_mammals_appendix2_safe_rows_v1_23 import (
    ROW_RE,CELL_RE,_attr,_column_index_from_ref,_decode_safe_cell_fragment,
    _selected_shared_strings,_download_exact,
)
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"development/global_mammals_appendix2_safe_rows_contract_v1_23.json"
DEFAULT=ROOT/"development/global_mammals_historical_overlap_contract_v1_37.json"
class Stop(RuntimeError): pass

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()

def norm(s):
 s=unicodedata.normalize("NFKD",str(s))
 s="".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
 s=" ".join(re.sub(r"[^0-9a-z]+"," ",s).split())
 return s

def core(s,tokens):
 return " ".join(x for x in norm(s).split() if x not in tokens)

def area_ratio(a,b):
 a=float(a); b=float(b)
 if not a>0 or not b>0:return math.inf
 return max(a,b)/min(a,b)

def project_identity(xlsx,base):
 source=base["source"]; wanted=("ID","Island_name","CountryISO","Area")
 headers=(
  "ID","Island_name","CountryISO","Longitude_centroid","Latitude_centroid","Area",
  "Current_isolation","Past_isolation","Climate_velocity","Temperature_mean",
  "Temperature_sd","Precipitation_mean","Precipitation_sd","Elevation_sd",
  "Richness_mammal","Richness_bat","Richness_nonVol","SIE_mammal","SIE_bats",
  "SIE_nonVol","pSIE_mammal","pSIE_bats","pSIE_nonVol","bioregion","bioregion_SIE"
 )
 idx={headers.index(c):c for c in wanted}
 protected=set(range(14,25))-{23}
 with zipfile.ZipFile(xlsx,"r") as z:
  raw=z.read(source["worksheet_member"])
  shared=z.read("xl/sharedStrings.xml") if "xl/sharedStrings.xml" in z.namelist() else b""
 parsed=[]; needed=set()
 for pos,m in enumerate(ROW_RE.finditer(raw)):
  if pos==0: continue
  values={}
  for cell in CELL_RE.finditer(m.group("body")):
   attrs=cell.group("attrs") if cell.group("attrs") is not None else cell.group("selfattrs") or b""
   rr=_attr(attrs,"r")
   if rr is None: raise Stop("cell lacks reference")
   ref=rr.decode("utf-8"); ci=_column_index_from_ref(ref)
   if ci in protected or ci not in idx: continue
   text,si=_decode_safe_cell_fragment(attrs=attrs,body=cell.group("body") or b"",cell_ref=ref)
   values[idx[ci]]=(text,si)
   if si is not None: needed.add(si)
  parsed.append(values)
 if len(parsed)!=source["expected_data_row_count"]: raise Stop("Appendix2 row count drift")
 selected=_selected_shared_strings(shared,needed) if needed else {}
 out=[]
 for row in parsed:
  resolved={}
  for c in wanted:
   if c not in row: resolved[c]=""; continue
   text,si=row[c]; resolved[c]=selected[si] if si is not None else text
   resolved[c]=str(resolved[c]).strip()
  if not resolved["ID"]: raise Stop("blank global ID")
  try: area=float(resolved["Area"])
  except ValueError as e: raise Stop("nonnumeric Area") from e
  if not area>0: raise Stop("nonpositive Area")
  resolved["Area"]=area
  out.append(resolved)
 if len({r["ID"] for r in out})!=len(out): raise Stop("duplicate global IDs")
 return out

def audit(hist,global_rows,retained_partition,tokens):
 hfreq=Counter(norm(r["Island"]) for r in hist)
 gfreq=Counter(norm(r["Island_name"]) for r in global_rows if r["Island_name"])
 byfull=defaultdict(list); bycore=defaultdict(list)
 for g in global_rows:
  if not g["Island_name"]: continue
  byfull[norm(g["Island_name"])].append(g)
  c=core(g["Island_name"],tokens)
  if c: bycore[c].append(g)
 matches=[]
 for h in hist:
  hn=norm(h["Island"]); hc=core(h["Island"],tokens); ha=float(h["Area_km2"])
  candidates={}
  for g in byfull.get(hn,[]):
   rr=area_ratio(ha,g["Area"])
   tier=None
   if hfreq[hn]==1 and gfreq[hn]==1: tier="A_unique"
   elif rr<=2.0: tier="A_area"
   if tier: candidates[g["ID"]]=(g,tier,rr)
  if hc:
   for g in bycore.get(hc,[]):
    rr=area_ratio(ha,g["Area"])
    if rr<=1.25 and g["ID"] not in candidates:
     candidates[g["ID"]]=(g,"B_core_area",rr)
  for gid,(g,tier,rr) in sorted(candidates.items(),key=lambda x:(x[1][1],x[0])):
   matches.append({
    "historical_ID":h["ID"],"historical_Island":h["Island"],
    "historical_Island_group":h["Island_group"],"historical_Area_km2":ha,
    "global_ID":gid,"global_Island_name":g["Island_name"],
    "global_CountryISO":g["CountryISO"],"global_Area":g["Area"],
    "match_tier":tier,"area_ratio":rr
   })
 overlap_ids={m["global_ID"] for m in matches}
 retained=[r for r in retained_partition if r["ID"] not in overlap_ids]
 removed=[r for r in retained_partition if r["ID"] in overlap_ids]
 return matches,overlap_ids,retained,removed

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("historical_csv",type=Path); ap.add_argument("retained_partition",type=Path)
 ap.add_argument("--contract",type=Path,default=DEFAULT)
 ap.add_argument("--identity-output",type=Path,required=True)
 ap.add_argument("--matches-output",type=Path,required=True)
 ap.add_argument("--retained-output",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args()
 raw=None
 try:
  c=json.loads(a.contract.read_text()); base=json.loads(BASE.read_text())
  if c["schema"]!="structural.global_mammals_historical_overlap_contract.v1_37": raise Stop("contract schema drift")
  if sha(a.historical_csv)!=c["historical_population"]["safe_design_csv_sha256"]: raise Stop("historical safe CSV SHA drift")
  with a.historical_csv.open(encoding="utf-8",newline="") as h: hist=list(csv.DictReader(h))
  if len(hist)!=c["historical_population"]["historically_analyzed_eligible_islands"]: raise Stop("historical analyzed population drift")
  with a.retained_partition.open(encoding="utf-8",newline="") as h: retained_part=list(csv.DictReader(h))
  raw=a.identity_output.parent/"Appendix_2-dryad.xlsx"
  _download_exact(raw,contract=base,token=os.environ.get("DRYAD_TOKEN",""))
  global_rows=project_identity(raw,base)
  tokens=set(c["name_normalization"]["generic_island_tokens_for_tier_B"])
  matches,overlap_ids,retained,removed=audit(hist,global_rows,retained_part,tokens)
  a.identity_output.parent.mkdir(parents=True,exist_ok=True)
  with a.identity_output.open("w",encoding="utf-8",newline="") as h:
   w=csv.DictWriter(h,fieldnames=["ID","Island_name","CountryISO","Area"],lineterminator="\n"); w.writeheader(); w.writerows(global_rows)
  with a.matches_output.open("w",encoding="utf-8",newline="") as h:
   fields=["historical_ID","historical_Island","historical_Island_group","historical_Area_km2","global_ID","global_Island_name","global_CountryISO","global_Area","match_tier","area_ratio"]
   w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); w.writeheader()
   for m in matches:
    mm=dict(m); mm["historical_Area_km2"]=float(mm["historical_Area_km2"]).hex(); mm["global_Area"]=float(mm["global_Area"]).hex(); mm["area_ratio"]=float(mm["area_ratio"]).hex(); w.writerow(mm)
  with a.retained_output.open("w",encoding="utf-8",newline="") as h:
   fields=list(retained_part[0].keys()); w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(retained)
  receipt={
   "schema":"structural.global_mammals_historical_overlap_result.v1_37",
   "status":"HISTORICAL_OVERLAP_AUDIT_COMPLETE_RESPONSE_INDEPENDENTLY",
   "historical_analyzed_islands":len(hist),"global_identity_rows":len(global_rows),
   "matched_pair_rows":len(matches),"unique_global_overlap_ids":len(overlap_ids),
   "overlap_ids_already_absent_after_v131":len(overlap_ids-{r["ID"] for r in retained_part}),
   "overlap_ids_removed_from_v131_retained":len(removed),
   "retained_after_historical_overlap":len(retained),
   "match_tier_counts":dict(Counter(m["match_tier"] for m in matches)),
   "identity_sha256":sha(a.identity_output),"matches_sha256":sha(a.matches_output),"retained_partition_sha256":sha(a.retained_output),
   "Appendix1_reopened":False,"species_headers_opened":False,"occurrence_values_opened":False,
   "counts_as_empirical_evidence":False,"fresh_system_denominator_contribution":0
  }
  a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(json.dumps(receipt,indent=2,sort_keys=True)); return 0
 except Exception as e:
  result={"schema":"structural.global_mammals_historical_overlap_result.v1_37","status":"STOP","reason":f"{type(e).__name__}: {e}","Appendix1_reopened":False,"species_headers_opened":False,"occurrence_values_opened":False,"counts_as_empirical_evidence":False,"fresh_system_denominator_contribution":0}
  a.receipt.parent.mkdir(parents=True,exist_ok=True); a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(json.dumps(result,indent=2,sort_keys=True)); return 2
 finally:
  if raw is not None and raw.exists(): raw.unlink()
if __name__=="__main__": raise SystemExit(main())
