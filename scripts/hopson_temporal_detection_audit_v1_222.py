#!/usr/bin/env python3
"""Hopson/Fox 2016 source-locked RETROSPECTIVE detection/transition support audit.

This is NOT a colonization, extinction, connectivity, or rescue analysis.
One whole experiment is already published and its outcomes already exposed.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

FILES = {
    "observations": ("Summer 2016 Data - 8.26.csv", "76de51cecdee69e87138c469a93b35a9"),
    "layout": ("Summer 2016 treatment layout.csv", "6957db366d97aa5a15fd7107b2429ac3"),
}
BASE = "https://zenodo.org/records/4960267/files/"
OBS_HEADER = ["date","day","jar.no","samp.vol","dil.vol","sub.samp.vol","eupl","tet"]
LAYOUT_HEADER = ["jar.no","metapop.no","patch.no","trt","time.block"]
GROUPS = ("nn","sw")

def download_locked(which):
    filename, expected = FILES[which]
    url = BASE + quote(filename, safe="") + "?download=1"
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"StructuralResearch/1.222"}),timeout=35) as response:
        data = response.read(1000000)
    found=hashlib.md5(data).hexdigest()
    if found!=expected:
        raise ValueError("source MD5 drift: "+which+": "+found)
    return data

def rows_locked(raw, expected_cols):
    d=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if d.fieldnames!=expected_cols:
        raise ValueError("source CSV header drift")
    for row in d:
        if None in row: raise ValueError("Unparsed extra CSV values")
        yield row

def intish(value, kind):
    x=float(value)
    if not math.isfinite(x) or x<0 or x!=int(x):
        raise ValueError("invalid nonnegative integer "+kind)
    return int(x)

def optional_count(value, name):
    if value is None or value.strip().casefold() in ("", "na", "nan"):
        return None
    return intish(value,name)

def layout_index(raw):
    layout={}
    metablocks=defaultdict(set)
    for r in rows_locked(raw,LAYOUT_HEADER):
        jar=intish(r["jar.no"],"jar")
        meta=intish(r["metapop.no"],"metapop")
        patch=intish(r["patch.no"],"patch")
        block=intish(r["time.block"],"block")
        trt=r["trt"].strip().lower()
        if jar in layout or not(1<=patch<=15 and 1<=meta<=14 and block in (1,2) and trt in GROUPS):
            raise ValueError("invalid/duplicate/unknown layout row")
        layout[jar]=(meta,patch,trt,block)
        metablocks[meta].add((trt,block))
    if (len(layout)!=210 or set(layout)!=set(range(1,211))
        or set(metablocks)!=set(range(1,15))
        or any(len(x)!=1 for x in metablocks.values())):
        raise ValueError("14 x 15 layout geometry fails")
    for meta in range(1,15):
        j=[(patch,trl,b) for m,patch,trl,b in layout.values() if m==meta]
        if len(j)!=15 or {v[0] for v in j}!=set(range(1,16)):
            raise ValueError("unequal or duplicate ring patch units")
    balance=Counter(next(iter(metablocks[m])) for m in metablocks)
    if balance!=Counter({("sw",1):4,("nn",1):3,("sw",2):3,("nn",2):4}):
        raise ValueError("published block/treatment assignment drift")
    return layout

def summarize(obs,lay):
    layout=layout_index(lay)
    byjar=defaultdict(list)
    aggregate=defaultdict(lambda:Counter())
    volume_by_group=defaultdict(list)
    transition_gaps=Counter()
    missing_reasons=Counter()
    for row in rows_locked(obs,OBS_HEADER):
        jar=intish(row["jar.no"],"jar")
        if jar not in layout: raise ValueError("observed jar missing from layout")
        day=intish(row["day"],"day")
        # eupl uses the UNDILUTED sample volume; tet requires different volume scaling
        count=optional_count(row["eupl"],"eupl")
        volume = optional_count(None,"unused") if False else float(row["samp.vol"])
        if not math.isfinite(volume) or volume<0: raise ValueError("invalid sample volume")
        meta,patch,trt,block=layout[jar]
        k=(block,trt)
        aggregate[k]["source_rows"]+=1
        if count is None or volume==0:
            aggregate[k]["unusable_eupl_rows"]+=1
            missing_reasons["missing_eupl" if count is None else "zero_sample_volume"]+=1
            byjar[jar].append((day,None,volume))
            continue
        aggregate[k]["usable_eupl_rows"]+=1
        aggregate[k]["positive_samples"]+=int(count>0)
        aggregate[k]["zero_samples"]+=int(count==0)
        volume_by_group[k].append(volume)
        byjar[jar].append((day,int(count>0),volume))
    if set(byjar)!=set(layout):
        raise ValueError("some experimental jars never sampled")
    jar_sizes={}
    for jar,series in byjar.items():
        series=sorted(series,key=lambda z:z[0])
        days=[s[0] for s in series]
        if len(days)!=len(set(days)):
            raise ValueError("duplicate jar-day measurements")
        meta,patch,trt,block=layout[jar];k=(block,trt)
        jar_sizes[jar]=len(series)
        for a,b in zip(series,series[1:]):
            aggregate[k]["adjacent_observation_pairs"]+=1
            if b[0]<=a[0]:raise ValueError("nonpositive time interval")
            transition_gaps[b[0]-a[0]]+=1
            if a[1] is None or b[1] is None:
                aggregate[k]["unusable_adjacent_pairs"]+=1
                continue
            aggregate[k]["usable_adjacent_pairs"]+=1
            aggregate[k][("negative" if a[1]==0 else "positive")+"_to_"+("negative" if b[1]==0 else "positive")]+=1
    # No inference from nonexistent observations or imputation of absent biological rows.
    result={}
    for block in (1,2):
        for trt in GROUPS:
            k=(block,trt);d=aggregate[k]
            vols=volume_by_group[k]
            result[f"block_{block}_{trt}"]={
                "unique_metapopulations":len({layout[j][0] for j in byjar if layout[j][2]==trt and layout[j][3]==block}),
                "source_rows":d["source_rows"],
                "usable_eupl_rows":d["usable_eupl_rows"],
                "unusable_eupl_rows":d["unusable_eupl_rows"],
                "zero_samples":d["zero_samples"],
                "positive_samples":d["positive_samples"],
                "median_sample_volume_ml":statistics.median(vols) if vols else None,
                "min_sample_volume_ml":min(vols) if vols else None,
                "max_sample_volume_ml":max(vols) if vols else None,
                "adjacent_observation_pairs":d["adjacent_observation_pairs"],
                "usable_adjacent_pairs":d["usable_adjacent_pairs"],
                "unusable_adjacent_pairs":d["unusable_adjacent_pairs"],
                "zero_then_positive_REDETECTION":d["negative_to_positive"],
                "positive_then_zero_LOSS_OF_DETECTION":d["positive_to_negative"],
                "zero_then_zero":d["negative_to_negative"],
                "positive_then_positive":d["positive_to_positive"]
            }
            if sum(d[x] for x in ("negative_to_positive","positive_to_negative","negative_to_negative","positive_to_positive"))!=d["usable_adjacent_pairs"]:
                raise ValueError("unreconciled detection pairs")
    return {
        "schema":"structural.hopson_temporal_observation_support.v1_222",
        "status":"RETROSPECTIVE_EXPLORATORY_PUBLISHED_OUTCOME_NOT_COLONIZATION",
        "source_md5":{k:v[1] for k,v in FILES.items()},
        "source_sha256":{"observations":hashlib.sha256(obs).hexdigest(),"layout":hashlib.sha256(lay).hexdigest()},
        "original_source_row_count":sum(x["source_rows"] for x in result.values()),
        "independent_experimental_metapopulations":14,
        "jars":len(byjar),
        "sampling_visits_by_jar_min_max":[min(jar_sizes.values()),max(jar_sizes.values())],
        "observed_intervisit_day_gaps":{str(k):v for k,v in sorted(transition_gaps.items())},
        "excluded_row_reasons":dict(missing_reasons),
        "per_block_treatment":result,
        "zero_then_positive_is_documented_redetection_NOT_true_colonization":True,
        "positive_then_zero_is_documented_nondetection_NOT_true_extinction":True,
        "no_target_recolonization_or_rescue_estimated":True,
        "no_independent_directed_displacement_records":True,
        "known_assignment": "15-patch ring, nearest-neighbour vs small-world kernel, not observed individual paths",
        "status_as_confirmatory_evidence":False,
        "Wolfe_original_data_reopened":False,
        "original_Global_mammal_heldout_reopened":False,
        "eBird_used":False,
        "GEB_scientific_HOLD":True
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=summarize(download_locked("observations"),download_locked("layout"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
