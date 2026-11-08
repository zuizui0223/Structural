#!/usr/bin/env python3
"""Thai forest beetles: paired vertical versus horizontal community distance.

Exploratory reanalysis of data also examined by the original 2024 authors.
Question: Is the across-stratum compositional difference at corresponding
sampling stations larger than the within-stratum difference across stations?

Only family-level abundance, because GBIF occurrence taxon ranks are mixed.
Original field event, species, coordinates, and site IDs never exported.
No independent-forest or causal inference from station-level comparisons.
"""
from __future__ import annotations
import argparse, datetime, hashlib, itertools, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path

from thai_beetle_canopy_family_response import (
    UID, API, fetch_json, get_archive_endpoint, download_small_archive,
    original_tables, protocol_category, valid_family, bray_relative,
)
from thai_beetle_pairing_diagnostic import haversine_m, campaigns

EXPECTED_SHA="1565cf6d7f1e7289e28756367e3d137f64723dc1fa0a06d799f6abdb523e1339"


def compare(original_events, occurrences):
    sampling=[r for r in original_events if protocol_category(r["samplingProtocol"])[0]=="SLAM"]
    if len(sampling)!=144:
        raise ValueError("expected_144_source_SLAM_jar_events")
    forests=sorted({e["locationID"] for e in sampling})
    if len(forests)!=2 or any(not f for f in forests):
        raise ValueError("expected_2_original_forests")
    geometry={}
    phase={}
    pair_offsets=[]
    horiz_coords={}
    for f in forests:
        ef=[e for e in sampling if e["locationID"]==f]
        locations={}
        for layer in ("canopy","understorey"):
            coords=sorted({
                (round(float(e["decimalLatitude"]),6),round(float(e["decimalLongitude"]),6))
                for e in ef if protocol_category(e["samplingProtocol"])[1]==layer
            })
            if len(coords)!=9:
                raise ValueError("expected_9_station_coordinates_per_forest_and_layer")
            locations[layer]=coords
        a,b=locations["canopy"],locations["understorey"]
        destinations=[]
        for i,coord in enumerate(a):
            j=min(range(9),key=lambda k:haversine_m(coord,b[k]))
            d=haversine_m(coord,b[j])
            if d>60 or min(range(9),key=lambda k:haversine_m(b[j],a[k]))!=i:
                raise ValueError("source_canopy_understorey_station_pairing_not_reciprocal")
            geometry[f,"canopy",coord]=(f,i)
            geometry[f,"understorey",b[j]]=(f,i)
            horiz_coords[f,"canopy",i]=coord
            horiz_coords[f,"understorey",i]=b[j]
            destinations.append(j)
            pair_offsets.append(d)
        if len(set(destinations))!=9:
            raise ValueError("source_pairing_not_one_to_one")
        groups,clust=campaigns([e["eventDate"] for e in ef])
        if len(groups)!=2:raise ValueError("two_source_sampling_campaigns_required")
        for i,mapping in enumerate(groups):
            for day in mapping:phase[f,day]=i
    core_to_key={}
    effort=defaultdict(Counter)
    for e in sampling:
        f=e["locationID"]
        _,layer=protocol_category(e["samplingProtocol"])
        c=(round(float(e["decimalLatitude"]),6),round(float(e["decimalLongitude"]),6))
        site=geometry.get((f,layer,c))
        p=phase.get((f,datetime.date.fromisoformat(e["eventDate"][:10])))
        if site is None or p is None:raise ValueError("source_event_lacks_station_or_campaign")
        kind=e["samplingProtocol"].strip().lower()
        jar="top" if "top jar" in kind else "bottom" if "bottom jar" in kind else None
        if jar is None:raise ValueError("not_valid_SLAM_jar_protocol")
        key=(site,p,layer,jar)
        if key in core_to_key.values():
            raise ValueError("duplicate_SLAM_jar_at_station_campaign")
        core_to_key[e["_core_id"]]=key
        effort[layer][(e.get("sampleSizeValue"),e.get("sampleSizeUnit"),e.get("samplingEffort"))]+=1
    if effort["canopy"]!=effort["understorey"]:
        raise ValueError("original_strata_effort_not_equivalent")
    if len(core_to_key)!=144:raise ValueError("not_all_source_jars_mapped")
    for f in forests:
        for i,p,layer,jar in itertools.product(range(9),range(2),
                                                 ("canopy","understorey"),("top","bottom")):
            if ((f,i),p,layer,jar) not in core_to_key.values():
                raise ValueError("missing_original_jar_in_complete_pair")
    by_station=defaultdict(Counter)
    total=0
    invalid_family_specimens=0
    for occ in occurrences:
        core=occ["_core_id"]
        if core not in core_to_key:
            raise ValueError("non_SLAM_beetle_records_not_expected")
        n=float(occ["individualCount"])
        if not n.is_integer() or n<=0:
            raise ValueError("invalid_original_beetle_individual_count")
        n=int(n)
        total+=n
        fam=valid_family(occ["family"])
        if fam:
            k=core_to_key[core]
            by_station[k[0],k[1],k[2]][fam]+=n
        else:
            invalid_family_specimens+=n
    if total!=1622:raise ValueError("original_beetle_total_drift")
    rows=[]
    allvertical=[]
    allhorizontal=[]
    horiz_dist=[]
    for f in forests:
        for p in range(2):
            V=[]
            H=[]
            D=[]
            for i in range(9):
                v=bray_relative(by_station[(f,i),p,"canopy"],
                                by_station[(f,i),p,"understorey"])
                if v is not None:V.append(v)
            for layer in ("canopy","understorey"):
                for i,j in itertools.combinations(range(9),2):
                    val=bray_relative(by_station[(f,i),p,layer],
                                      by_station[(f,j),p,layer])
                    if val is not None:
                        H.append(val)
                        D.append(haversine_m(horiz_coords[f,layer,i],
                                             horiz_coords[f,layer,j]))
            if len(V)<5 or len(H)<20:
                raise ValueError("insufficient_family_composition_pairs")
            allvertical.extend(V);allhorizontal.extend(H);horiz_dist.extend(D)
            rows.append({
                "anonymous_forest":forests.index(f)+1,
                "sampling_campaign":p+1,
                "vertical_station_pairs_with_taxa":len(V),
                "within_stratum_between_station_pairs_with_taxa":len(H),
                "mean_vertical_family_relative_BrayCurtis":statistics.mean(V),
                "mean_horizontal_family_relative_BrayCurtis":statistics.mean(H),
                "vertical_minus_horizontal_BrayCurtis":statistics.mean(V)-statistics.mean(H),
                "vertical_to_horizontal_BrayCurtis_ratio":(
                    statistics.mean(V)/statistics.mean(H) if statistics.mean(H)>0 else None),
                "mean_horizontal_separation_m":statistics.mean(D)
            })
    allv=statistics.mean(allvertical);allh=statistics.mean(allhorizontal)
    out={
       "schema":"structural.thai_beetle_vertical_vs_horizontal_family_beta.v1",
       "original_source_sha256":EXPECTED_SHA,
       "original_arthropod_forest_study_n":len(forests),
       "original_physical_station_pair_n":18,
       "seasonal_rounds_per_forest":2,
       "source_original_SLAM_jar_events":len(core_to_key),
       "source_beetle_individual_count":total,
       "invalid_family_identification_specimens_excluded_from_family_beta":invalid_family_specimens,
       "pooled_vertical_within_station_family_BrayCurtis_mean":allv,
       "pooled_horizontal_within_stratum_family_BrayCurtis_mean":allh,
       "pooled_vertical_minus_horizontal_BrayCurtis":allv-allh,
       "vertical_horizontal_beta_ratio":allv/allh if allh>0 else None,
       "vertical_comparisons_n":len(allvertical),
       "horizontal_comparisons_n_NOT_independent":len(allhorizontal),
       "forest_campaign_direction_count_vertical_greater_than_horizontal":sum(
           row["vertical_minus_horizontal_BrayCurtis"]>0 for row in rows),
       "paired_canopy_understorey_horizontal_offset_m_median":statistics.median(pair_offsets),
       "within_stratum_between_station_horizontal_distance_m_median":statistics.median(horiz_dist),
       "forest_campaign_summaries":rows,
       "original_study_2024_already_tested_vertical_and_horizontal_beta_diversity":True,
       "new_global_effect_or_mechanistic_claim":False,
       "not_abundance_corrected_to_equal_individual_coverage":True,
       "horizontal_and_vertical_distance_not_matched":True,
       "forest_site_n_not_36_or_288":2,
       "raw_ids_coordinates_and_family_labels_not_exported":True
    }
    return out

def run(out,request=fetch_json,download=download_small_archive):
    ds=request(API+UID)
    if str(ds.get("key"))!=UID:raise ValueError("dataset_identity_changed")
    license=str(ds.get("license","")).lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("original_source_license_changed")
    data=download(get_archive_endpoint(ds))
    if hashlib.sha256(data).hexdigest()!=EXPECTED_SHA:
        raise ValueError("original_source_archive_version_changed")
    events,occs=original_tables(data)
    report=compare(events,occs)
    p=Path(out);p.mkdir(parents=True,exist_ok=True)
    (p/"thai_beetle_vertical_vs_horizontal_family_beta.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    arg=argparse.ArgumentParser();arg.add_argument("--out",required=True)
    a=arg.parse_args();run(a.out)
