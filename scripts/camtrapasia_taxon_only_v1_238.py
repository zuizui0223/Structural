#!/usr/bin/env python3
"""Source species names only. No camera detections or pilot species incidence."""
import argparse,csv,hashlib,io,json,re,unicodedata
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
SOURCE="https://zenodo.org/api/records/10780971/files/Species_Traits_20231031.csv/content"
SOURCE_SIZE=67450
SOURCE_MD5="59e0748f8aaf59b23b936248f1e63fc9"
ORIGINAL_SHA="4f801eac218edb00f319cd04416af3c6e7d7a90e04b68868eeed47f4d403dfd9"
HOSTS={"zenodo.org","www.zenodo.org","files.zenodo.org","s3.cern.ch"}
def clean(x):
 return " ".join(unicodedata.normalize("NFC",x).replace("."," ").replace("_"," ").split()).casefold()
def fetch_source():
 req=Request(SOURCE,headers={"User-Agent":"Structural-taxon-names-only-v1.238"})
 with urlopen(req,timeout=45) as f:
  u=urlsplit(f.url)
  if u.scheme!="https" or u.hostname not in HOSTS:raise ValueError("Untrusted source redirect")
  raw=f.read(SOURCE_SIZE+1)
 if len(raw)!=SOURCE_SIZE or hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
  raise ValueError("Exact official species list bytes changed")
 return raw
def names(raw,orig):
 if hashlib.md5(raw).hexdigest()!=SOURCE_MD5 or len(raw)!=SOURCE_SIZE:
  raise ValueError("Species trait file identity drift")
 if hashlib.sha256(orig).hexdigest()!=ORIGINAL_SHA:
  raise ValueError("Original 529 name manifest SHA drift")
 with io.StringIO(raw.decode("utf-8-sig")) as f:
  reader=csv.DictReader(f)
  if not {"class","binomial_verified","taxonomic_level"}.issubset(reader.fieldnames or []):
   raise ValueError("Original species traits columns missing")
  mammal_labels=[]
  mammal_empty=0
  for r in reader:
   if (r["class"] or "").strip().casefold()!="mammalia":continue
   label=(r["binomial_verified"] or "").strip()
   if not label:mammal_empty+=1;continue
   mammal_labels.append(label)
 with io.StringIO(orig.decode("utf-8-sig")) as f:
  reader=csv.DictReader(f)
  if "species_name" not in (reader.fieldnames or []):raise ValueError("Missing original species names")
  reference=[r["species_name"] for r in reader]
 if len(reference)!=529 or len(set(map(clean,reference)))!=529:
  raise ValueError("Original 529-name canonical uniqueness changed")
 by_reference={clean(n):n for n in reference}
 unique={clean(t):t for t in mammal_labels if len(clean(t).split())==2}
 matched=[{"survey_verified_binomial":unique[k],"original_529_binomial":by_reference[k]}
          for k in sorted(unique) if k in by_reference]
 return {
  "schema":"structural.camtrapasia_taxon_names_only_result.v1_238",
  "status":"TAXON_OVERLAP_ONLY_PREGEOGRAPHY" if matched else "STOP_ZERO_TAXON_OVERLAP",
  "source_Mammalia_entries_with_verified_labels":len(mammal_labels),
  "source_Mammalia_missing_binomial_count":mammal_empty,
  "unique_valid_two_word_source_binomials":len(unique),
  "original_frozen_taxa_count":529,
  "exact_verified_taxon_overlaps":len(matched),
  "exact_matched_binomials":matched,
  "field_site_species_detection_values_opened":0,
  "original_mammal_pilot_occupancy_fields_read":0,
  "original_mammal_heldout_observations_read":0,
  "model_predictions_read":0,
  "external_ecological_validation_authorized":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("original_taxon_manifest",type=Path);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 try:r=names(fetch_source(),a.original_taxon_manifest.read_bytes())
 except HTTPError as e:r={"status":"STOP_ZENODO_TAXON_HTTP","http_status":e.code}
 except Exception as e:r={"status":"STOP_TAXON_SOURCE_IDENTITY_OR_FORMAT","reason_class":type(e).__name__}
 r.setdefault("schema","structural.camtrapasia_taxon_names_only_result.v1_238")
 r.setdefault("field_site_species_detection_values_opened",0)
 r.setdefault("original_mammal_heldout_observations_read",0)
 r.setdefault("external_ecological_validation_authorized",False)
 a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(r,sort_keys=True))
 if r["status"] in ("STOP_ZENODO_TAXON_HTTP","STOP_TAXON_SOURCE_IDENTITY_OR_FORMAT"):raise SystemExit(2)
if __name__=="__main__":main()
