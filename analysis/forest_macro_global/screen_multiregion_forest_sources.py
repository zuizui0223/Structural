#!/usr/bin/env python3
"""Screen a FIXED cross-region terrestrial forest monitoring network.

GBIF registry is the universe of candidate sampling-event datasets. This
script reads only dataset metadata and occurrence *COUNTS* (limit=0) to
check which have any indexed records in 2019--2026. No occurrence results
or taxon values are returned; no site count inferred from records.
"""
from __future__ import annotations
import argparse,csv,json,time,urllib.parse,urllib.request
from collections import Counter
from pathlib import Path

FIXED_CANDIDATES={
"d59ccafb-251e-46cf-9319-37b58d88e7c5":"boreal_temperate_vegetation",
"0fe87daf-ed3c-4544-9d41-e187c408ee71":"mediterranean_forest_inventory",
"b471e8c8-237a-4444-b2ef-0d5ba1903ead":"east_asian_long_term_forest_plots",
"4e9d318a-5620-4639-9776-719664892cb3":"south_american_atlantic_forest",
"db1b8346-ce2a-4bf1-836d-3c496dfae8cc":"south_american_forest_soil_fauna",
"7ba1318c-04ed-4521-8369-63731e2867f7":"southeast_asian_canopy_understory_beetles",
"cd451e0f-789e-4416-94f4-e583e57f20ce":"southeast_asian_canopy_understory_hymenoptera",
"0740c09f-5cf6-48f0-8e94-abaa46f4b87b":"west_african_forest_reserve_plants",
"cd67c18a-98e2-4b8b-ad07-358b02b7812c":"west_african_high_forest_flora",
"a2e81790-9ba8-4d81-9da7-38e1d18dd4cc":"south_asian_tropical_forest_fragments",
"c90cdbff-495b-49ff-9930-c493225c984a":"south_asian_western_ghats",
"dc67ba75-6a7c-44ef-83f7-81bce6a7aef1":"east_african_forest_point_counts",
"90533959-8819-4641-96e6-1924a296f99a":"central_european_forest_fungi",
"b4934203-2d86-44a6-9fec-b55d7ab97749":"north_european_forest_floor",
"d6a5709f-1de0-4963-b9f9-a882026a968c":"north_american_forest_bees",
"6ef6360c-c904-4eab-87fe-7bd234cb5c42":"east_asian_secondary_forest_birds",
"931cb4c9-43b8-459d-b116-6d5be21e2b65":"north_european_forest_vegetation",
"bc1cb3f0-6bc8-473a-aa6b-a5606d52bde5":"west_african_forest_carbon_vegetation",
}
BASE="https://api.gbif.org/v1"

def get_json(path,params=None):
    url=BASE+path
    if params:url+="?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"Structural-Forest-Macro-Source-Network-Screen/1.0"})
    with urllib.request.urlopen(req,timeout=45) as response:
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("GBIF source metadata response too large")
    return json.loads(raw)

def countries_from_facets(src):
    matches=[]
    for facet in src.get("facets",[]):
        if str(facet.get("field","")).lower()=="country":
            matches.extend((str(item.get("name","")),int(item.get("count",0)))
                           for item in facet.get("counts",[]))
    return sorted(matches,key=lambda x:-x[1])

def build_row(uid,role,registr,metadata,all_records,recent_records):
    if metadata.get("key")!=uid or str(metadata.get("type","")).upper()!="SAMPLING_EVENT":
        raise ValueError("Original GBIF dataset identity/type not as registry declared")
    countries=countries_from_facets(all_records)
    n_recent=int(recent_records["count"])
    return {
        "dataset_uuid":uid,
        "predefined_source_role_NOT_geography_proven":role,
        "title":str(metadata.get("title") or registr["name"]),
        "doi":str(metadata.get("doi") or registr.get("source_doi","")),
        "license":str(metadata.get("license") or registr.get("source_license","")),
        "indexed_occurrence_count_total_NOT_sites":int(all_records["count"]),
        "indexed_occurrence_count_2019_2026_NOT_sites":n_recent,
        "actual_occurrence_country_facet_top5":"|".join(x[0] for x in countries[:5]),
        "actual_occurrence_country_facets_n":len(countries),
        "publisher_country_NOT_sampling_country":str(metadata.get("publishingCountry") or ""),
        "source_modified":str(metadata.get("modified") or ""),
        "original_Event_site_ids_visited":0,
        "original_occurrence_species_rows_visited":0,
        "georeferenced_independent_forest_plots_verified":False,
        "habitat_methods_sampling_effort_verified":False,
        "source_2020_canopy_alignment_status":(
            "RECENT_OCCURRENCE_CANDIDATE_NOT_SITE_VERIFIED" if n_recent>0
            else "NO_INDEXED_2019_2026_OCCURRENCE_NOT_CONTEMPORARY")
    }

def screen(registry,request=get_json,delay=.25):
    by_id={r["gbif_dataset_uuid"]:r for r in registry}
    missing=sorted(set(FIXED_CANDIDATES)-set(by_id))
    if missing:raise ValueError("Pre-fixed forest registry candidates disappeared: "+str(missing))
    output=[]
    for uid,role in FIXED_CANDIDATES.items():
        if "ebird" in by_id[uid]["name"].lower():
            raise ValueError("eBird excluded from original forest sampling network")
        try:
            metadata=request(f"/dataset/{uid}")
            all_count=request("/occurrence/search",{"datasetKey":uid,"limit":0,"facet":"country","facetLimit":100})
            newer=request("/occurrence/search",{"datasetKey":uid,"limit":0,"year":"2019,2026"})
            row=build_row(uid,role,by_id[uid],metadata,all_count,newer)
        except Exception as exc:
            row={"dataset_uuid":uid,"predefined_source_role_NOT_geography_proven":role,
                 "title":by_id[uid]["name"],
                 "source_2020_canopy_alignment_status":"SOURCE_METADATA_OR_API_STOP",
                 "source_error_type":type(exc).__name__,
                 "source_error_message":str(exc)[:160],
                 "original_Event_site_ids_visited":0,
                 "original_occurrence_species_rows_visited":0,
                 "georeferenced_independent_forest_plots_verified":False,
                 "habitat_methods_sampling_effort_verified":False}
        output.append(row)
        if delay:time.sleep(delay)
    return output

def save(out,rows):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for d in rows for k in d))
    with (out/"GBIF_multiregion_original_forest_monitoring_screen.csv").open(
        "w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=keys);writer.writeheader();writer.writerows(rows)
    statuses=Counter(r["source_2020_canopy_alignment_status"] for r in rows)
    report={
        "schema":"structural.forest_macro_multiregion_source_screen.v1",
        "original_global_registry_fixed_source_candidates":len(FIXED_CANDIDATES),
        "statuses":dict(statuses),
        "candidate_datasets_with_recent_indexed_occurrences_not_sites":
            statuses.get("RECENT_OCCURRENCE_CANDIDATE_NOT_SITE_VERIFIED",0),
        "sampled_study_locations_qualified_for_2020_canopy_height":0,
        "actual_original_forest_plot_site_counts_verified":0,
        "source_original_Event_rows_read":0,
        "source_original_Occurrence_species_rows_read":0,
        "only_indexed_occurrence_count_API_limit_0":True,
        "source_publishing_country_never_used_as_sampling_country":True,
        "different_original_source_methods_not_equivalent":True,
        "not_a_global_forest_biodiversity_or_canopy_effect":True,
        "eBird_used":False
    }
    (out/"multiregion_source_screen_manifest.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--registry",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    with Path(a.registry).open(encoding="utf-8",newline="") as fd:
        reg=list(csv.DictReader(fd))
    result=save(a.out,screen(reg))
    print(json.dumps(result,indent=2))
