#!/usr/bin/env python3
"""Global forest sampling-event NETWORK discovery from the GBIF registry.

Not a species data analysis: results are metadata-level *candidates*, not
geolocated independent forest sampling sites. Publishing country is NEVER
substituted for sampling country. No eBird, and no original Occurrence reads.

Scans fixed globally relevant forest/sampling phrases; returns dataset UUID,
title/DOI/license/publisher and conservative forest-keyword classification.
Downstream forest coverage must open original Event metadata and assess sites,
dates, methods, geographic location, deduplication and licensing separately.
"""
from __future__ import annotations
import argparse,csv,json,re,time,urllib.parse,urllib.request
from collections import Counter
from pathlib import Path

SEARCH_TERMS=(
    "forest", "rainforest", "woodland", "tropical forest",
    "temperate forest", "boreal forest", "forest arthropods",
    "forest monitoring", "forest plots", "canopy"
)
BASE="https://api.gbif.org/v1/dataset/search"
FOREST_PATTERN=re.compile(r"\b(forest|forests|woodland|rainforest|canopy|laurel forest|mangrove|taiga|boreal)\b",re.I)
EXCLUDE_PATTERN=re.compile(r"\bebird\b|e-bird|ebird\.org",re.I)
MAX_PAGES=3
PER_PAGE=100

def fetch_page(query:str,offset:int=0,limit:int=PER_PAGE)->dict:
    query_params=urllib.parse.urlencode({"type":"SAMPLING_EVENT","q":query,
        "limit":limit,"offset":offset})
    request=urllib.request.Request(f"{BASE}?{query_params}",
        headers={"User-Agent":"Structural-Forest-Macro-Registry-Discovery/1.0"})
    with urllib.request.urlopen(request,timeout=35) as response:
        if response.status!=200:raise ValueError(f"GBIF registry API status {response.status}")
        raw=response.read(2_000_000)
    if len(raw)>=2_000_000:raise ValueError("GBIF registry response length cap exceeded")
    result=json.loads(raw)
    if not isinstance(result.get("results"),list):
        raise ValueError("GBIF expected dataset search results array missing")
    return result

def first_str(x):
    if isinstance(x,str):return x
    if x is None:return ""
    if isinstance(x,list):return "|".join(str(y) for y in x[:4])
    return str(x)

def candidate(row,query):
    ds_id=row.get("key")
    if not ds_id:return None
    name=first_str(row.get("title"))
    abstract=first_str(row.get("description"))
    if EXCLUDE_PATTERN.search(name+" "+abstract):return None
    typ=first_str(row.get("type"))
    if typ and typ.upper()!="SAMPLING_EVENT":return None
    forest_title=bool(FOREST_PATTERN.search(name))
    forest_described=bool(FOREST_PATTERN.search(abstract))
    return {
        "gbif_dataset_uuid":str(ds_id),
        "source_registry_type":typ,
        "name":name,
        "source_doi":first_str(row.get("doi")),
        "source_license":first_str(row.get("license")),
        "source_publishing_country_NOT_sampling_country":
            first_str(row.get("publishingCountry")),
        "source_record_count_NOT_site_count":row.get("recordCount"),
        "source_publication_date_NOT_sampling_year":
            first_str(row.get("pubDate")),
        "source_modified":first_str(row.get("modified")),
        "forest_keyword_in_title":forest_title,
        "forest_keyword_in_description":forest_described,
        "status":"FOREST_METADATA_CANDIDATE_ONLY" if forest_title or forest_described
                  else "SEARCH_RESULT_FOREST_SITE_NOT_VERIFIED",
        "matched_search_terms":[query],
        "gbif_registry_url":f"https://www.gbif.org/dataset/{ds_id}",
        "original_site_count_verified":False,
        "original_event_method_verified":False,
        "site_geolocation_verified":False,
        "source_data_acquired":False,
    }

def collect(queries=SEARCH_TERMS,fetch=fetch_page,delay=.25):
    data={};counts={};excluded=0
    for term in queries:
        seen=0
        for page in range(MAX_PAGES):
            offset=page*PER_PAGE
            payload=fetch(term,offset,PER_PAGE)
            results=payload["results"]
            seen+=len(results)
            for row in results:
                item=candidate(row,term)
                if item is None:
                    excluded+=1
                    continue
                key=item["gbif_dataset_uuid"]
                if key in data:
                    if term not in data[key]["matched_search_terms"]:
                        data[key]["matched_search_terms"].append(term)
                else:data[key]=item
            if not results or bool(payload.get("endOfRecords",False)) or len(results)<PER_PAGE:
                break
            if delay:time.sleep(delay)
        counts[term]={"raw_registry_results_returned":seen,
                      "capped_at":MAX_PAGES*PER_PAGE,
                      "exhaustive":seen<MAX_PAGES*PER_PAGE}
        if delay:time.sleep(delay)
    rows=sorted(data.values(),key=lambda r:r["gbif_dataset_uuid"])
    for r in rows:r["matched_search_terms"]="|".join(r["matched_search_terms"])
    report={
        "schema":"structural.forest_macro_GBIF_sampling_event_registry.v1",
        "scope":"metadata_only_global_sampling_event_forest_query_discovery",
        "search_terms":list(queries),
        "per_term_results_limit":PER_PAGE*MAX_PAGES,
        "per_query_counts":counts,
        "n_distinct_GBIF_dataset_UUIDs":len(rows),
        "n_candidate_title_or_abstract_forest_keyword":
            sum(r["status"]=="FOREST_METADATA_CANDIDATE_ONLY" for r in rows),
        "search_row_rejections_excluding_ebird_or_non_events_or_empty_ids":excluded,
        "n_original_source_Event_rows_read":0,
        "n_original_source_Occurrence_rows_read":0,
        "n_unique_sampled_sites_verified":0,
        "geographic_coverage_study_country_not_verified":True,
        "publishing_country_is_not_sampling_location":True,
        "dataset_recordCount_is_NOT_forest_plot_sample_size":True,
        "not_a_global_biodiversity_effect_estimate":True,
        "source_license_requires_individual_verification":True,
        "eBird_used":False,
    }
    return rows,report

def save(out,rows,report):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    filename=out/"GBIF_forest_sampling_event_candidates_METADATA_ONLY.csv"
    if rows:
        with filename.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    (out/"GBIF_forest_source_registry_audit.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    rows,report=collect()
    save(args.out,rows,report)
    print(json.dumps({k:v for k,v in report.items() if k!="per_query_counts"},indent=2))
