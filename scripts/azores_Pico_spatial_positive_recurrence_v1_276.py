#!/usr/bin/env python3
"""Pico S1 historical-loss taxa documented at a same GPS proxy across years.

Exploratory same-place *positive records* only; original PRIBES Event/Occurrence
SHA-locked data have already been opened for the v1.271/274 observational pilot.
No absences, individual IDs, genetic identity, reproduction or immigration.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import zipfile
import xml.etree.ElementTree as ET

from azores_2016_dwca_structure_v1_267 import summarize_archive
from azores_PRIBES_crossisland_field_v1_271 import (
    get_original,field_columns,_table_records
)
from azores_Pico_event_site_revisit_v1_275 import parse_author_event_day
from azores2016_s1_loss_presence_crosswalk_v1_268 import (
    canonical_binomial,normalized_locality,normalized_text
)
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

SCHEMA="structural.azores_Pico_spatial_S1_positive_recurrence.v1_276"
YEARS={"2020":171,"2021":1603,"2022":898,"2024":129}
PICO_SHA="82406dbcb48e188cca6bca116437b951a80f613faadf44a173ddd5d9b92e4a02"
S1_SHA="767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1"
S1_URL="https://digital.csic.es/bitstream/10261/377677/5/Extinct_species_biogeographical_variables_%26_biological_traits_Macaronesian_flora.xlsx"


def gps_round_site_key(lat,lon,precision):
    if lat is None or lon is None:return None
    try:
        a=float(lat);b=float(lon)
    except (ValueError,TypeError):return None
    if not (math.isfinite(a) and math.isfinite(b) and -90<=a<=90 and -180<=b<=180):
        return None
    if precision not in (3,4,5):
        raise ValueError("GPS precision not frozen in current original protocol")
    return (f"{a:.{precision}f}",f"{b:.{precision}f}")


def aggregate_positive_site_year(rows,loss_taxa):
    if not loss_taxa:
        raise ValueError("Fixed historical case list must contain at least one taxon")
    years_by_tax=defaultdict(set)
    by_site_year={p:defaultdict(set) for p in (5,4,3)}
    missing_geo=0
    uncertainty=[]
    target_rows=0
    for obs in rows:
        name=obs["name"]
        if name not in loss_taxa:continue
        target_rows+=1
        year=int(obs["year"])
        if year not in (2020,2021,2022,2024):
            raise ValueError("Original field positive record year not source verified")
        years_by_tax[name].add(year)
        if obs.get("lat") is None or obs.get("lon") is None:
            missing_geo+=1
        for p in (5,4,3):
            key=gps_round_site_key(obs.get("lat"),obs.get("lon"),p)
            if key is not None:
                by_site_year[p][(name,key)].add(year)
        try:
            u=float(obs.get("uncertainty_m")) if obs.get("uncertainty_m") is not None else None
        except (TypeError,ValueError):
            u=None
        if u is not None and math.isfinite(u) and u>=0:
            uncertainty.append(u)
    repeated={}
    for p in (5,4,3):
        repeated[p]={name for (name,key),yrs in by_site_year[p].items()
                     if len(yrs)>=2}
    site_repeated5=sum(len(v)>=2 for v in by_site_year[5].values())
    year_counts=Counter(yr for years in years_by_tax.values() for yr in years)
    histogram=Counter(len(years) for years in years_by_tax.values())
    uncertainty.sort()
    return {
        "fixed_S1_loss_taxa":len(loss_taxa),
        "S1_field_positive_rows_after_filtering":target_rows,
        "S1_field_records_with_missing_geocoordinates":missing_geo,
        "Pico_taxa_positive_any_year":len(years_by_tax),
        "Pico_taxa_seen_in_2plus_distinct_years":sum(len(x)>=2 for x in years_by_tax.values()),
        "Pico_taxa_seen_in_only_one_year":histogram[1],
        "Pico_positive_taxon_year_pairs":sum(len(x) for x in years_by_tax.values()),
        "Pico_S1_taxa_by_distinct_positive_years":{str(k):v for k,v in sorted(histogram.items())},
        "Pico_affected_taxa_positive_by_year":{str(k):v for k,v in sorted(year_counts.items())},
        "GPS5_S1_taxa_positive_at_same_site_in_2plus_years":len(repeated[5]),
        "GPS4_S1_taxa_positive_at_same_site_in_2plus_years":len(repeated[4]),
        "GPS3_S1_taxa_positive_at_same_site_in_2plus_years":len(repeated[3]),
        "GPS5_S1_taxon_site_proxies_repeated_in_2plus_years":site_repeated5,
        "source_positive_uncertainty_count":len(uncertainty),
        "source_positive_uncertainty_median_m":statistics.median(uncertainty) if uncertainty else None,
        "source_positive_uncertainty_range_m":[min(uncertainty),max(uncertainty)] if uncertainty else None,
        "source_positive_uncertainty_le100m_count":sum(u<=100 for u in uncertainty),
        "GPS_precision_only_not_verified_permanent_plot":True,
        "record_missing_never_called_absent":True,
        "no_breeding_or_demographic_rescue_inference":True,
        "source_taxon_or_site_ids_exported":False,
    }


def read_source_rows(original_zip):
    schema=summarize_archive(original_zip,"Pico PRIBES v1.7")
    c=schema["core"]
    ext=[x for x in schema["extensions"] if x["rowtype"].endswith("/Occurrence")]
    if not c["rowtype"].endswith("/Event") or len(ext)!=1:
        raise ValueError("Expected one source Event and one Occurrence extension")
    ec=field_columns(c);oc=field_columns(ext[0])
    if not {"island","eventDate","decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters"}<=set(ec):
        raise ValueError("No original Event GPS or date fields")
    if not {"scientificName","taxonRank"}<=set(oc):
        raise ValueError("No original species-rank field")
    with zipfile.ZipFile(io.BytesIO(original_zip)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        core_meta=[x for x in root if x.tag.endswith("}core")]
        extension_meta=[x for x in root if x.tag.endswith("}extension") and x.attrib.get("rowType","").endswith("/Occurrence")]
        if len(core_meta)!=1 or len(extension_meta)!=1:
            raise ValueError("Original Event/Occurrence source key schema inconsistent")
        eid=[x for x in core_meta[0] if x.tag.endswith("}id")]
        oid=[x for x in extension_meta[0] if x.tag.endswith("}coreid")]
        if len(eid)!=1 or len(oid)!=1 or eid[0].attrib.get("index")!="0" or oid[0].attrib.get("index")!="0":
            raise ValueError("Do not join original Event core to Occurrence on taxon ID")
        events=list(_table_records(z,c,ec))
        occurrence=list(_table_records(z,ext[0],oc))
    if len(events)!=2801 or len(occurrence)!=11023:
        raise ValueError("Frozen original Pico Event/Occurrence population changed")
    e_by_id={}
    hist=Counter()
    for rec in events:
        if rec["coreid"] in e_by_id:
            raise ValueError("Duplicate source event core ID")
        yr=parse_author_event_day(rec).year
        if normalized_locality(rec.get("island"))!="Pico":
            raise ValueError("Pico original source has another island")
        hist[str(yr)]+=1
        lat=rec.get("decimalLatitude")
        lon=rec.get("decimalLongitude")
        try:
            lat=float(lat) if lat not in (None,"") else None
            lon=float(lon) if lon not in (None,"") else None
        except ValueError:
            lat=lon=None
        uncert=rec.get("coordinateUncertaintyInMeters")
        e_by_id[rec["coreid"]]={"year":yr,"lat":lat,"lon":lon,
                                "uncertainty_m":uncert}
    if dict(sorted(hist.items()))!=YEARS:
        raise ValueError("Source years differ from 2801 source-only author MDY gate")
    return e_by_id,occurrence


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if c.get("schema")!="structural.azores_Pico_spatially_repeated_loss_taxa.v1_276":
        raise ValueError("Pico S1 spatial study not frozen")
    m=json.loads((Path(__file__).resolve().parents[1]/
        "development/azores_PRIBES_original_source_manifest_v1_270.json").read_text())
    pico=next(x for x in m["sources"] if x["label"]=="Pico PRIBES")
    if pico["sha256"]!=PICO_SHA or c["authority"]["Pico_sha256"]!=PICO_SHA or c["authority"]["S1_sha256"]!=S1_SHA:
        raise ValueError("Original Pico/S1 source fingerprints changed")
    output={
        "schema":SCHEMA,"status":"SOURCE_STOP_NO_SITE_POSITIVE_RESULT",
        "Pico_sha256":PICO_SHA,"S1_sha256":S1_SHA,
        "S2_S3_S4_values_opened":0,
        "original_mammal_BioTIME_RLS_holdouts_opened":0,
        "GEB_scientific_HOLD":True,"eBird_off":False is True else False,
        "new_confirmatory_systems":0,
    }
    output["eBird_off"]=True
    try:
        source=get_original(pico)
        s1=download_original(S1_URL,332776,5_000_000)
        if hashlib.sha256(s1).hexdigest()!=S1_SHA:
            raise ValueError("Published original 2025 S1 workbook checksum mismatch")
        cases=parse_sheet_s1(s1)
        azores=[r for r in cases if
                normalized_text(r.get("Archipelago"))=="azores"
                and normalized_text(r.get("Extinction category"))=="extirpation (island level)"
                and normalized_text(r.get("Category"))=="well-supported"]
        taxa={canonical_binomial(r.get("Species")) for r in azores}
        if len(azores)!=24 or len(taxa)!=20 or None in taxa:
            raise ValueError("Frozen S1 24 Azores loss cases / 20 taxon source universe mismatch")
        e_by_id,occurrences=read_source_rows(source)
        positive=[]
        excluded=Counter()
        for obs in occurrences:
            meta=e_by_id.get(obs["coreid"])
            if meta is None:
                excluded["unmatched_original_Event_coreid"]+=1
                continue
            if normalized_text(obs.get("taxonRank"))!="species":
                excluded["non_species_rank"]+=1
                continue
            if normalized_text(obs.get("occurrenceStatus"))=="absent":
                excluded["explicit_absence"]+=1
                continue
            name=canonical_binomial(obs.get("scientificName"))
            if name not in taxa:continue
            positive.append({"name":name,**meta})
        summary=aggregate_positive_site_year(positive,taxa)
        if (summary["Pico_taxa_positive_any_year"]!=11
            or summary["Pico_taxa_seen_in_2plus_distinct_years"]!=8
            or summary["Pico_positive_taxon_year_pairs"]!=21):
            raise ValueError("Previously validated Pico S1 11/8/21 positive cohort changed")
        output.update({
            "status":"ORIGINAL_PICO_S1_EXACT_GPS_TAXON_POSITIVE_AUDIT",
            "Pico_original_Event_rows":len(e_by_id),
            "Pico_original_Occurrence_rows":len(occurrences),
            "original_source_join_exclusions":dict(sorted(excluded.items())),
            "positive_summary":summary,
            "no_per_taxon_or_coordinate_output":True,
        })
    except Exception as exc:
        output["stop_type"]=type(exc).__name__
        output["stop_reason"]=str(exc)[:500]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":output["status"],
        "taxa_repeating_on_exact_GPS_5dp":output.get("positive_summary",{}).get("GPS5_S1_taxa_positive_at_same_site_in_2plus_years"),
        "taxa_repeating_on_GPS_4dp":output.get("positive_summary",{}).get("GPS4_S1_taxa_positive_at_same_site_in_2plus_years"),
        "stop":output.get("stop_reason"),
    },sort_keys=True))
    if output["status"]!="ORIGINAL_PICO_S1_EXACT_GPS_TAXON_POSITIVE_AUDIT":
        raise SystemExit(2)


if __name__=="__main__":
    main()
