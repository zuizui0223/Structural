#!/usr/bin/env python3
"""Exact original Obs linkage of Brisbane beetle traps to canopy/ground habitat.

Only source metadata and environmental columns; species abundance matrix
NEVER accessed here. Source CC0 Stone et al. 2018 workbook MD5-pinned. The
one absent canopy environment row is localized to its original stratum/edge
design cell without exporting Obs code, site numbers or coordinates.
No effects estimated or posthoc zero cover imputation.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,statistics,zipfile
from collections import Counter,defaultdict
from pathlib import Path

from audit_brisbane_canopy_ground_original_xlsx import (
    SOURCE_MD5,SOURCE_DOI,content_types,shared_text)
from audit_brisbane_stratum_env_grain import read_first_columns

def original_id_fields(x):
    m=re.fullmatch(r"([A-Za-z]+)([0-9]+)([GC])([0-9]+)([A-Za-z]+)",str(x or ""))
    if m is None:raise ValueError("original_Brisbane_source_field_Obs_identity_unrecognized")
    prefix,site,layer,edge,suffix=m.groups()
    return (prefix,site),("Ground" if layer=="G" else "Canopy"),int(edge)

def numeric(raw):
    if not str(raw or "").strip():return None
    try:val=float(raw)
    except ValueError:return None
    return val if math.isfinite(val) else None

def inspect(rows):
    bio,ground,canopy=rows
    if (len(bio),len(ground),len(canopy))!=(81,51,30):
        raise ValueError("Brisbane_original_source_sheet_row_count_changed")
    if [bio[0].get(i) for i in range(5)]!=["Obs","Abundance","Richness","Edge.dist","Height"]:
        raise ValueError("beetle_original_source_first5_fields_drift")
    def env_fields(items):
        return {v:i for i,v in items[0].items() if v}
    gb=env_fields(ground);cb=env_fields(canopy)
    if "Can.cov" not in gb or "Can.cov" not in cb or "Trap.height" not in cb:
        raise ValueError("Brisbane_original_environment_canopy_field_missing")
    original={}
    layer_counts=Counter()
    for row in bio[1:]:
        oid=row.get(0,"")
        site,layer,edge=original_id_fields(oid)
        if row.get(4)!=layer:
            raise ValueError("source_original_Highly_Obs_layer_conflict")
        if numeric(row.get(3))!=edge:
            raise ValueError("source_original_Edge_dist_Obs_conflict")
        if oid in original:raise ValueError("source_duplicate_original_beetle_Obs")
        original[oid]=(site,layer,edge)
        layer_counts[layer,edge]+=1
    if len(original)!=80 or len({x[0] for x in original.values()})!=10:
        raise ValueError("source_original_site_trap_design_not_80")
    original_by_layer=defaultdict(set)
    for obs,(site,layer,edge) in original.items():
        original_by_layer[layer].add(obs)
    env={}
    out_of_bio=0
    bylayer=Counter()
    cover=defaultdict(list)
    logheight=[]
    numeric_coverage=Counter()
    for layer,table,columns in (
        ("Ground",ground,gb),
        ("Canopy",canopy,cb)
    ):
        for row in table[1:]:
            obs=row.get(0,"")
            if not obs or obs in env:
                raise ValueError("source_env_row_Obs_missing_or_duplicate")
            meta=original.get(obs)
            if meta is None or meta[1]!=layer:
                raise ValueError("source_environment_row_unmatched_to_original_stratum")
            _,_,edge=meta
            env[obs]=(layer,edge)
            bylayer[layer,edge]+=1
            c=numeric(row.get(columns["Can.cov"]))
            if c is not None:
                cover[layer].append(c)
                numeric_coverage[layer,"Can.cov"]+=1
            if layer=="Canopy":
                h=numeric(row.get(columns["Trap.height"]))
                if h is not None:
                    logheight.append(h)
                    numeric_coverage[layer,"Trap.height"]+=1
    if len(env)!=79 or any(not original_by_layer[l].issuperset(
        {obs for obs,v in env.items() if v[0]==l}) for l in original_by_layer):
        raise ValueError("source_environment_source_grain_not_79_original_traps")
    missing=set(original)-set(env)
    if len(missing)!=1:raise ValueError("source_missing_environment_not_unique")
    absent=next(iter(missing))
    _,layer,edge=original[absent]
    complete_pair=Counter()
    for oid,(site,level,dist) in original.items():
        if dist in (1,16,256) and level=="Canopy":
            ground_ids=[g for g,(g_site,g_layer,g_edge) in original.items()
                        if g_site==site and g_layer=="Ground" and g_edge==dist]
            if len(ground_ids)!=1:raise ValueError("source_ground_canopy_trap_pair_invalid")
            complete_pair[dist]+=int(oid in env and ground_ids[0] in env)
    return {
      "schema":"structural.Brisbane_original_80beetle_to79canopy_ground_environment_source_obs_join.v1",
      "source_DOI":SOURCE_DOI,
      "source_workbook_verified_MD5":SOURCE_MD5,
      "original_beetle_traps":len(original),
      "original_ground_environment_records":len(ground)-1,
      "original_canopy_environment_records":len(canopy)-1,
      "environment_rows_with_exact_original_Obs_matched_and_stratum_checked":len(env),
      "source_original_missing_environment_trap_count":len(missing),
      "missing_environment_stratum_type":layer,
      "missing_environment_edge_distance_m":edge,
      "original_biological_10sites_30_layer_pair_opportunities":30,
      "source_pairwise_ground_and_canopy_environment_join_by_edge_m":{
          str(d):{"complete_pairs":complete_pair[d],"expected_pairs":10}
          for d in (1,16,256)},
      "source_env_cover_original_numeric_support_by_stratum":{
          l:{"nonmissing":len(v),"min":min(v) if v else None,
             "median":statistics.median(v) if v else None,
             "max":max(v) if v else None}
          for l,v in cover.items()},
      "source_canopy_Trap_height_field_original_numeric_count":len(logheight),
      "source_canopy_Trap_height_source_range_RAW_TRANSFORM_UNVERIFIED":{
          "min":min(logheight) if logheight else None,
          "max":max(logheight) if logheight else None},
      "original_Trap_height_is_original_recorded_measure_not_confirmed_meters":True,
      "original_species_taxon_columns_read":0,
      "source_canopy_environment_missingness_not_imputed":True,
      "new_species_environment_effect_calculated":False,
      "no_source_Obs_trap_site_IDs_or_species_names_exported":True,
    }

def run(source,out):
    fp=Path(source)
    if hashlib.md5(fp.read_bytes()).hexdigest()!=SOURCE_MD5:
        raise ValueError("Brisbane_original_source_wkbk_version_hash_changed")
    with zipfile.ZipFile(fp) as z:
        names=dict(content_types(z))
        strings=shared_text(z)
        r=[read_first_columns(z,names[x],strings,cutoff=13)
           for x in ("Beetle data","Ground level enviros","Canopy level enviros")]
    report=inspect(r)
    d=Path(out);d.mkdir(parents=True,exist_ok=True)
    (d/"Brisbane_field_layer_environment_Obs_join_metadata.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    o=p.parse_args()
    run(o.source,o.out)
