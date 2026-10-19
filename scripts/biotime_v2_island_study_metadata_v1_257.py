#!/usr/bin/env python3
"""Published BioTIME v2 STUDY_ID 373/375 metadata-only admission; never RDS responses."""
import argparse
import csv
import io
import json
import math
from pathlib import Path

from biotime_v2_metadata_preflight_v1_249 import source_bytes, EXPECTED_MD5

TARGET_IDS=("373","375")
COLUMNS=(
 "STUDY_ID","REALM","TITLE","HABITAT","TAXA","ORGANISMS",
 "START_YEAR","END_YEAR","NUMBER_LAT_LONG","NUMBER_OF_SAMPLES",
 "NUMBER_OF_SPECIES","CEN_LATITUDE","CEN_LONGITUDE","CENT_LAT",
 "CENT_LONG","GRAIN_SIZE_TEXT","METHODS","SUMMARY_METHODS",
 "SAMPLE_DESC_NAME","AB_BIO","WEB_LINK"
)
LONG_FIELDS={"METHODS","SUMMARY_METHODS","AB_BIO"}
MAX_NOTE_CHARS=2000


def normalize(row):
    output={}
    for k in COLUMNS:
        v=(row.get(k) or "").strip()
        if k in LONG_FIELDS:
            output[k]=v[:MAX_NOTE_CHARS]
            output[f"{k}_text_truncated"]=len(v)>MAX_NOTE_CHARS
        else:
            output[k]=v[:700]
    return output


def centroid(row):
    for lat,lon in (("CEN_LATITUDE","CEN_LONGITUDE"),("CENT_LAT","CENT_LONG")):
        try:
            a,b=float(row.get(lat,"")),float(row.get(lon,""))
        except (TypeError,ValueError):
            continue
        if math.isfinite(a) and math.isfinite(b) and -90<=a<=90 and -180<=b<=180:
            return (a,b,lat,lon)
    return None


def central_distance_km(a,b):
    p1,p2=math.radians(a[0]),math.radians(b[0])
    dphi=p2-p1
    dlambda=math.radians(b[1]-a[1])
    q=math.sin(dphi/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dlambda/2)**2
    return 6371.0088*2*math.asin(min(1,math.sqrt(q)))


def audit(raw:bytes,contract:dict):
    if contract.get("schema")!="structural.biotime_island_study_metadata_admission.v1_257":
        raise ValueError("Frozen metadata-only protocol schema mismatch")
    if contract["studied_ids"]!=list(TARGET_IDS):
        raise ValueError("Unanticipated post-outcome changes to source-study selection")
    if contract["authority"]["expected_md5"]!=EXPECTED_MD5:
        raise ValueError("Published metadata source MD5 differs from pre-frozen original")
    text=raw.decode("utf-8-sig")
    csv_reader=csv.DictReader(io.StringIO(text,newline=""))
    if not csv_reader.fieldnames or not set(COLUMNS)<=set(csv_reader.fieldnames):
        raise ValueError("Expected original published metadata schema missing")
    rows=list(csv_reader)
    if len(rows)!=708 or len({r.get("STUDY_ID") for r in rows})!=708:
        raise ValueError("BioTIME v2 canonical 708-study metadata universe mismatch")
    selected={r["STUDY_ID"]:r for r in rows if r["STUDY_ID"] in TARGET_IDS}
    if set(selected)!=set(TARGET_IDS):
        raise ValueError("One or both original GSHHG study IDs missing; no relabeling")
    regions={sid:centroid(row) for sid,row in selected.items()}
    dist=(central_distance_km(regions["373"],regions["375"])
          if all(regions.values()) else None)
    return {
        "schema":"structural.biotime_island_metadata_result.v1_257",
        "doi":contract["authority"]["canonical_source_doi"],
        "exact_published_metadata_md5":EXPECTED_MD5,
        "total_unique_studies_in_publisher_metadata":len(rows),
        "study_selection_fixed_before_metadata":list(TARGET_IDS),
        "chosen_studies":{sid:normalize(selected[sid]) for sid in TARGET_IDS},
        "centroid_distance_km":round(dist,3) if dist is not None else None,
        "study_centers_prove_archipelago_independence":False,
        "geological_oceanic_vs_continental_origin_confirmed":False,
        "species_or_site_year_responses_read":False,
        "future_33_reserved_study_species_queries":0,
        "cannot_infer_colonization_or_successful_dispersal":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False,
        "evidence_class":"SOURCE_AUTHENTICATED_STUDY_METADATA_ONLY"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    contract=json.loads(args.protocol.read_text(encoding="utf-8"))
    raw,source_url,failures=source_bytes()
    from hashlib import md5
    if md5(raw).hexdigest()!=EXPECTED_MD5:
        raise RuntimeError("Source original published metadata changed")
    res=audit(raw,contract)
    res["source_url"]=source_url
    res["earlier_transport_failures"]=failures
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"original_ids":res["study_selection_fixed_before_metadata"],
                      "metadata_centroid_distance_km":res["centroid_distance_km"],
                      "source_validated":True,
                      "taxa_response_accesses":0},sort_keys=True))


if __name__=="__main__":main()
