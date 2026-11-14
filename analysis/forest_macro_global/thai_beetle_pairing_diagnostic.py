#!/usr/bin/env python3
"""Check spatial and temporal matching of Thai beetle canopy/understorey SLAM traps.

Only original geometry and Event metadata, no species data required for this
step. Raw coordinates/event identifiers remain in memory and are not exported.
"""
from __future__ import annotations
import argparse,hashlib,datetime,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path
from audit_thai_beetle_canopy_original import UID,API,fetch_json,get_archive_endpoint,download_small_archive
from thai_beetle_canopy_family_response import original_tables,protocol_category

def haversine_m(a,b):
    la,lo=map(math.radians,a);lb,lob=map(math.radians,b)
    x=math.sin((lb-la)/2)**2+math.cos(la)*math.cos(lb)*math.sin((lob-lo)/2)**2
    return 2*6371008.8*math.asin(min(1,math.sqrt(x)))

def campaigns(dates):
    keys=sorted({datetime.date.fromisoformat(d[:10]) for d in dates})
    if not keys:raise ValueError("original_sample_dates_missing")
    centers=[]
    for day in keys:
        if not centers or (day-max(centers[-1])).days>60:
            centers.append([day])
        else:centers[-1].append(day)
    return [{d:i for d in grp} for i,grp in enumerate(centers)],centers

def diagnose(data):
    es,_=original_tables(data)
    et=[e for e in es if protocol_category(e["samplingProtocol"])[0]=="SLAM"]
    if len(et)!=144:raise ValueError("SLAM_source_event_count_drift")
    forests=sorted({e["locationID"] for e in et})
    if len(forests)!=2:raise ValueError("exactly_two_forests_required")
    summary=[]
    for loc in forests:
        rows=[e for e in et if e["locationID"]==loc]
        layers=defaultdict(set)
        for e in rows:
            group,layer=protocol_category(e["samplingProtocol"])
            try:
                lat,lon=float(e["decimalLatitude"]),float(e["decimalLongitude"])
            except ValueError:raise ValueError("SLAM_sample_missing_coordinate")
            if not (-90<=lat<=90 and -180<=lon<=180):raise ValueError("SLAM_outside_valid_geo")
            layers[layer].add((round(lat,6),round(lon,6)))
        ca=sorted(layers["canopy"])
        under=sorted(layers["understorey"])
        if len(ca)!=9 or len(under)!=9:raise ValueError("expected_9_original_sites_per_stratum_per_forest")
        match=[]
        for i,coord in enumerate(ca):
            distances=[haversine_m(coord,z) for z in under]
            j=min(range(9),key=lambda k:distances[k])
            match.append((i,j,distances[j]))
        reciprocal=all(
            min(range(9),key=lambda k:haversine_m(under[j],ca[k]))==i
            for i,j,d in match
        ) and len({j for _,j,_ in match})==9
        site_dist=[p[2] for p in match]
        dates=[e["eventDate"] for e in rows]
        if any(len(d)<10 for d in dates):raise ValueError("malformed_original_eventDate")
        parts,clusters=campaigns(dates)
        temporal_count=len(clusters)
        per_protocol=Counter(e["samplingProtocol"] for e in rows)
        summary.append({
          "anonymous_forest":len(summary)+1,
          "SLAM_jar_events":len(rows),
          "distinct_canopy_horizontal_coordinate_candidates":len(ca),
          "distinct_understorey_horizontal_coordinate_candidates":len(under),
          "reciprocal_unique_nearest_spatial_pairs":reciprocal,
          "pair_horizontal_distance_m_min":min(site_dist),
          "pair_horizontal_distance_m_median":statistics.median(site_dist),
          "pair_horizontal_distance_m_max":max(site_dist),
          "pair_distances_all_le_60m":max(site_dist)<=60,
          "original_temporal_campaign_count_from_60day_gap":temporal_count,
          "original_campaign_event_counts":[sum(
              datetime.date.fromisoformat(e["eventDate"][:10]) in group
              for e in rows) for group in parts],
          "SLAM_jar_method_rows":dict(per_protocol)
        })
    return {
      "schema":"structural.thai_beetle_forestSLAM_spatial_temporal_pairing_v1",
      "source_archive_sha256":hashlib.sha256(data).hexdigest(),
      "forest_n":len(forests),
      "total_SLAM_jar_event_rows":len(et),
      "expected_station_pairs":18,
      "forest_pairing_diagnostics":summary,
      "biological_taxon_values_used_for_pairing":False,
      "all_pairs_unique_reciprocal_and_le_60m":all(
          z["reciprocal_unique_nearest_spatial_pairs"] and z["pair_distances_all_le_60m"]
          and z["original_temporal_campaign_count_from_60day_gap"]==2 for z in summary),
      "no_raw_coords_or_eventIDs_exported":True,
      "species_community_test_scored":False
    }

def run(out,request=fetch_json,download=download_small_archive):
    meta=request(API+UID)
    if str(meta.get("key"))!=UID:raise ValueError("dataset_identity_mismatch")
    d=download(get_archive_endpoint(meta))
    r=diagnose(d)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"thai_beetle_SLAM_spatial_pairing_diagnostic.json").write_text(
        json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2))
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.out)
