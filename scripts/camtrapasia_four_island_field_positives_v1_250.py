#!/usr/bin/env python3
"""Prospectively defined exploratory POSITIVE photographic records at 4 response-safe island candidates.
No IUCN mammal response, model prediction, or unsupported camera-study area is opened.
"""
import argparse,csv,hashlib,io,json,math,unicodedata
from pathlib import Path
from collections import defaultdict,Counter
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError

ZEN="https://zenodo.org/api/records/10780971/files/"
INPUT={
 "CamTrapAsia_Captures_20231031.csv":(956340,"a73975d7626def4012a4e1197497ba87"),
 "CamTrapAsia_Metadata_20231031.csv":(245677,"2b50c534737b0c98a93da54128b10a32")}
HOSTS={"zenodo.org","www.zenodo.org","files.zenodo.org","s3.cern.ch"}
TARGET={
 "65489":("Bawean",2),
 "65360":("Buton",2),
 "65554":("Java",25),
 "70378":("Sumatra",49)}
SAFE_WILD={"false","f","0","no","n","wild","non-domestic","non domestic"}
DOMESTIC={"true","t","1","yes","y","domestic"}
def canon(x):
 return " ".join(unicodedata.normalize("NFC",x).replace("."," ").replace("_"," ").split()).casefold()
def fetch(name):
 expected,md5=INPUT[name]
 with urlopen(Request(ZEN+name+"/content",headers={"User-Agent":"Structural-field-positive-only-v1.250"}),timeout=55) as f:
  u=urlsplit(f.url)
  if u.scheme!="https" or u.hostname not in HOSTS:raise ValueError("Untrusted official source URL")
  raw=f.read(expected+1)
 if len(raw)!=expected or hashlib.md5(raw).hexdigest()!=md5:raise ValueError("Original Zenodo source bytes changed")
 return raw
def dataset(raw,cols):
 with io.StringIO(raw.decode("utf-8-sig")) as f:
  reader=csv.DictReader(f)
  if not cols.issubset(reader.fieldnames or []):raise ValueError("Required public source column absent")
  for record in reader:
   yield {key:record[key] for key in cols}
def evidence(geom,taxa,capture,metadata):
 if geom.get("schema")!="structural.camtrapasia_all239_GADM36_polygon_support_result.v1_248" or geom.get("status")!="PASS_RESPONSE_SAFE_FULL239_POLYGON_IDENTITY_PRESCREEN":
  raise ValueError("Original geography candidate proof missing")
 if (geom.get("retained_geography_candidate_study_count"),geom.get("distinct_candidate_original_heldout_islands"),
     geom.get("distinct_candidate_original_heldout_blocks"))!=(79,5,4):raise ValueError("Original candidate denominator drift")
 if taxa.get("exact_verified_taxon_overlaps")!=38:raise ValueError("Prior original name overlap changed")
 binomials=taxa.get("exact_matched_binomials",[])
 if len(binomials)!=38:raise ValueError("Wrong taxon manifest count")
 aliases={canon(v["survey_verified_binomial"]):v["original_529_binomial"] for v in binomials}
 if len(aliases)!=38:raise ValueError("Duplicate field taxon binomial names")
 studies=defaultdict(set)
 for z in geom.get("geography_only_candidate_studies",[]):
  iid=z["candidate_original_heldout_ID"]
  if iid not in TARGET:continue
  studies[iid].add(z["survey_id"])
 if any(len(studies[iid])!=n for iid,(name,n) in TARGET.items()):
  raise ValueError("Frozen four island camera panel source-study counts changed")
 if len(set().union(*studies.values()))!=78:raise ValueError("Duplicated study ID between candidate islands")
 by_study={survey_id:iid for iid,ids in studies.items() for survey_id in ids}
 survey_effort={}
 for z in dataset(metadata,{"survey_id","effort"}):
  sid=z["survey_id"]
  if sid not in by_study:continue
  if sid in survey_effort:raise ValueError("Duplicate source survey effort ID")
  value=float(z["effort"])
  if not math.isfinite(value) or value<0:raise ValueError("Invalid camera effort at selected survey")
  survey_effort[sid]=value
 if len(survey_effort)!=78:raise ValueError("Selected camera studies missing exact effort")
 state=defaultdict(lambda:defaultdict(lambda:{"records":0,"studies":set(),"non_domestic_records":0,"non_domestic_studies":set(),"unknown_domestic_records":0}))
 domestic_categories=Counter()
 matching_event_rows=0
 for z in dataset(capture,{"survey_id","records","class","binomial_verified","taxonomic_level","domestic"}):
  sid=z["survey_id"]
  if sid not in by_study:continue
  if (z["class"] or "").strip().casefold()!="mammalia":continue
  key=canon(z["binomial_verified"] or "")
  if key not in aliases:continue
  text=(z["records"] or "").strip()
  try:count=float(text)
  except ValueError:raise ValueError("Matched focal capture count not numeric")
  if not math.isfinite(count) or count<0 or count!=int(count):
   raise ValueError("Matched photographic count not valid integer")
  if not count:continue
  count=int(count);matching_event_rows+=1
  kind=(z["domestic"] or "").strip().casefold()
  domestic_categories[kind if kind else "(blank)"]+=1
  r=state[by_study[sid]][aliases[key]]
  r["records"]+=count;r["studies"].add(sid)
  if kind in SAFE_WILD:
   r["non_domestic_records"]+=count;r["non_domestic_studies"].add(sid)
  elif kind not in DOMESTIC:
   r["unknown_domestic_records"]+=count
 results=[]
 for iid,(name,n) in TARGET.items():
  taxa_on_island=state[iid]
  results.append({
   "original_heldout_ID":iid,"geography_candidate_island":name,
   "source_camera_survey_studies":n,
   "total_camera_trap_effort_from_public_metadata":sum(survey_effort[sid] for sid in studies[iid]),
   "original_529_shared_taxa_with_positive_field_photo_records":len(taxa_on_island),
   "original_529_shared_taxa_with_positive_records_in_2plus_surveys":
      sum(len(v["studies"])>=2 for v in taxa_on_island.values()),
   "survey_studies_with_at_least_one_focal_taxon_positive":
      len(set().union(*(v["studies"] for v in taxa_on_island.values()))) if taxa_on_island else 0,
   "total_independent_camera_photo_records_in_focal_taxa":
      sum(v["records"] for v in taxa_on_island.values()),
   "taxa_with_confidently_non_domestic_positive_records":
      sum(v["non_domestic_records"]>0 for v in taxa_on_island.values()),
   "focal_taxon_positive_evidence":[{"species":taxon,"records":v["records"],"survey_count":len(v["studies"]),
      "confident_non_domestic_records":v["non_domestic_records"],
      "unknown_domestic_records":v["unknown_domestic_records"]} for taxon,v in sorted(taxa_on_island.items())]
  })
 return {
  "schema":"structural.camtrapasia_four_candidate_island_camera_positive_result.v1_250",
  "status":"PASS_EXPLORATORY_FIELD_POSITIVE_ONLY_NO_MODEL_SCORE",
  "island_candidates":4,"original_independent_heldout_geographic_blocks":3,
  "eligible_source_camera_survey_centers":78,
  "published_photo_capture_rows_positive_in_original_529_shared_taxa":matching_event_rows,
  "source_domestic_metadata_labels_for_positive_focal_rows":dict(sorted(domestic_categories.items())),
  "per_island_camera_field_positive_summary":results,
  "zero_camera_capture_row_never_treated_as_absence":True,
  "published_source_photo_records_are_NOT_unique_animals":True,
  "source_site_geometry_is_candidate_not_original_polygon_UUID":True,
  "native_mammal_status_not_verified":True,
  "original_IUCN_heldout_response_values_read":0,
  "original_model_prediction_scores_read":0,
  "does_not_validate_GEB_global_spatial_graph_predictive_skill":True
 }
def main():
 p=argparse.ArgumentParser();p.add_argument("geo_receipt",type=Path);p.add_argument("taxon_receipt",type=Path)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 try:
  r=evidence(json.loads(a.geo_receipt.read_text()),json.loads(a.taxon_receipt.read_text()),
            fetch("CamTrapAsia_Captures_20231031.csv"),fetch("CamTrapAsia_Metadata_20231031.csv"))
 except HTTPError as e:r={"status":"STOP_OFFICIAL_CAMTRAP_SOURCE_HTTP","code":e.code}
 except Exception as e:r={"status":"STOP_FROZEN_CAMERA_PANEL_OR_CAPTURE_SCHEMA","reason_type":type(e).__name__}
 r.setdefault("schema","structural.camtrapasia_four_candidate_island_camera_positive_result.v1_250")
 r.setdefault("original_IUCN_heldout_response_values_read",0)
 r.setdefault("original_model_prediction_scores_read",0)
 a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
 print(json.dumps(r,sort_keys=True))
 if r["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
