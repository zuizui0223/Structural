#!/usr/bin/env python3
"""Screen original field metadata in a 200-record GBIF sample per recent source.

This does NOT count independent sites; for million-record sources the
first 200 indexed occurrences may be highly concentrated in one event.
Taxon identities and abundance are intentionally ignored and never exported.
The 7 source datasets are fixed upstream by registry+year count, not biology.
"""
from __future__ import annotations
import argparse,csv,json,math,time,urllib.parse,urllib.request
from pathlib import Path

BASE="https://api.gbif.org/v1/occurrence/search"
LIMIT=200

def request(uid):
    qs=urllib.parse.urlencode({"datasetKey":uid,"year":"2019,2026","limit":LIMIT})
    req=urllib.request.Request(BASE+"?"+qs,headers={"User-Agent":"Structural-Forest-Macro-Source-Field-Assessment/1.0"})
    with urllib.request.urlopen(req,timeout=45) as fd:
        raw=fd.read(3_000_001)
    if len(raw)>3_000_000:raise ValueError("GBIF source field screening exceeds response cap")
    return json.loads(raw)

def valid_coord(r):
    try:
        lat=float(r["decimalLatitude"]);lon=float(r["decimalLongitude"])
        return math.isfinite(lat) and math.isfinite(lon) and abs(lat)<=90 and abs(lon)<=180
    except (KeyError,TypeError,ValueError):return False

def precision_known(r):
    try:
        x=float(r["coordinateUncertaintyInMeters"])
        return math.isfinite(x) and x>=0
    except (KeyError,TypeError,ValueError):return False

def summarize(candidate,response):
    results=response.get("results")
    if not isinstance(results,list):raise ValueError("GBIF original occurrence source search missing results")
    n=len(results)
    if n<1:raise ValueError("2019+ source has 0 sample rows despite recent registry count")
    seen=lambda field:sum(bool(str(r.get(field) or "").strip()) for r in results)
    countries=sorted(set(str(r.get("country") or "") for r in results)-{""})
    years=sorted(set(int(r["year"]) for r in results if str(r.get("year") or "").isdigit()))
    events=[str(r.get("eventID") or "").strip() for r in results]
    event_ids={e for e in events if e}
    site_keys=[str(r.get("locationID") or "").strip() for r in results]
    valid_sites={v for v in site_keys if v}
    # This is a SAMPLE diagnostic ONLY, not an estimate of full site count.
    return {
       "dataset_uuid":candidate["dataset_uuid"],
       "source_network_role":candidate["predefined_source_role_NOT_geography_proven"],
       "source_name":candidate["title"],
       "gbif_source_2019_2026_indexed_occurrence_count_NOT_sites":
            int(candidate["indexed_occurrence_count_2019_2026_NOT_sites"]),
       "metadata_sample_indexed_occurrence_rows_downloaded":n,
       "sample_eventID_present_count":len([e for e in events if e]),
       "sample_eventID_distinct_lower_bound_NOT_full_site_count":len(event_ids),
       "sample_locationID_present_count":len([x for x in site_keys if x]),
       "sample_locationID_distinct_lower_bound_NOT_full_site_count":len(valid_sites),
       "sample_samplingProtocol_present_count":seen("samplingProtocol"),
       "sample_habitat_present_count":seen("habitat"),
       "sample_locality_present_count":seen("locality"),
       "sample_years": "|".join(map(str,years)),
       "sample_actual_occurrence_country_codes":"|".join(countries),
       "sample_coordinate_valid_n":sum(valid_coord(r) for r in results),
       "sample_coordinate_uncertainty_reported_n":sum(precision_known(r) for r in results),
       "sample_geodetic_datum_reported_n":seen("geodeticDatum"),
       "actual_independent_forest_plots_verified":0,
       "original_sampling_effort_and_forest_habitat_compatibility_verified":False,
       "requires_full_original_Event_table_and_licensing_review":True,
       "taxon_identifiers_or_occurrence_counts_not_used_for_source_selection":True,
    }

def run(source_csv,out,fetch=request):
    rows=list(csv.DictReader(open(source_csv,encoding="utf-8",newline="")))
    candidates=[r for r in rows if r["source_2020_canopy_alignment_status"]==
                "RECENT_OCCURRENCE_CANDIDATE_NOT_SITE_VERIFIED"]
    if len(candidates)!=7:raise ValueError("Source original recent 7-dataset cohort drift")
    result=[]
    for row in candidates:
        try:
            result.append(summarize(row,fetch(row["dataset_uuid"])))
        except Exception as e:
            result.append({"dataset_uuid":row["dataset_uuid"],
                "source_network_role":row["predefined_source_role_NOT_geography_proven"],
                "metadata_status":"FIELD_SAMPLE_API_OR_SOURCE_STOP",
                "error_class":type(e).__name__,"error_message":str(e)[:150],
                "actual_independent_forest_plots_verified":0,
                "requires_full_original_Event_table_and_licensing_review":True})
        time.sleep(.3)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in result for k in r))
    with (out/"seven_recent_forest_networks_original_field_coverage_sample.csv").open(
        "w",newline="",encoding="utf-8") as fd:
        writer=csv.DictWriter(fd,fieldnames=keys);writer.writeheader();writer.writerows(result)
    report={
        "schema":"structural.global_forest_recent_original_source_field_quality.v1",
        "predefined_source_dataset_n":len(candidates),
        "sampled_source_dataset_n":len(result),
        "source_datasets_with_successful_metadata_sample":
            sum("metadata_sample_indexed_occurrence_rows_downloaded" in r for r in result),
        "source_datasets_with_nonempty_sample_eventID":
            sum(r.get("sample_eventID_present_count",0)>0 for r in result),
        "source_datasets_with_nonempty_sample_samplingProtocol":
            sum(r.get("sample_samplingProtocol_present_count",0)>0 for r in result),
        "original_occurrence_records_downloaded_as_FIELD_METADATA_sample":
            sum(r.get("metadata_sample_indexed_occurrence_rows_downloaded",0) for r in result),
        "species_names_abundance_values_stored_or_scored":0,
        "full_source_or_independent_plot_counts_verified":0,
        "sample_bias_first_indexed_records_not_representative":True,
        "no_biodiversity_effects_calculated":True,
        "no_2020_canopy_height_linkage_claim":True,
        "eBird_used":False
    }
    (out/"source_original_field_QC_manifest.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args();run(a.source,a.out)
