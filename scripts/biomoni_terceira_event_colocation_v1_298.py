#!/usr/bin/env python3
"""v1.298: Two matched published Terceira forest-plot sources, Event-only.

This source-level exact site crosswalk opens no original woody or beetle
Occurrence body; 308 beetle Event rows are repeated method observations, never
treated as 308 independent forest sites. Never export site IDs or coordinates.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,urllib.request,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path

SOURCE={
 "woody":("https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7",
          "4574d02727654ec5a319f6d1218ff9243080b0128c517d01c905065cbefd6f82"),
 "beetle":("https://ipt.gbif.pt/ipt/archive.do?r=biomoni_beetles&v=1.3",
           "e518beb6f529067cc2f38013e03c4f833e86133fddface1df6f9ba7c532885e8")
}
MAX_BYTES=500000

def local(s):return s.rsplit("}",1)[-1]
def term(s):return s.rstrip("/").split("/")[-1].split("#")[-1]
def normalized_site(s):return re.sub(r"[^A-Z0-9]","",str(s or "").upper())
def norm(s):return " ".join(str(s or "").casefold().strip().split())

def extract_event_core_only(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        core=next(v for v in root if local(v.tag)=="core")
        columns={};loc=None;idx=None
        for v in core.iter():
            if local(v.tag)=="field" and "term" in v.attrib and "index" in v.attrib:
                columns[term(v.attrib["term"])]=int(v.attrib["index"])
            elif local(v.tag)=="location" and v.text:loc=v.text.strip()
            elif local(v.tag)=="id" and "index" in v.attrib:idx=int(v.attrib["index"])
        required={"locationID","island","decimalLatitude","decimalLongitude","eventDate","samplingProtocol"}
        if idx is None or not loc or not required.issubset(columns):
            raise ValueError("Missing frozen location, location coordinates or method columns in source Event")
        separator=core.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(separator)!=1:raise ValueError("Unexpected source Event separator")
        skip=int(core.attrib.get("ignoreHeaderLines","0"))
        if skip<0 or skip>2:raise ValueError("Unusual source header count")
        out=[]
        with z.open(loc) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as f:
                rdr=csv.reader(f,delimiter=separator)
                for _ in range(skip):next(rdr,None)
                for row in rdr:
                    if not row or not any(row):continue
                    if max(idx,*[columns[k] for k in required])>=len(row):
                        raise ValueError("Source Event row incomplete")
                    item={k:row[v] for k,v in columns.items() if v<len(row)}
                    item["source_coreid"]=row[idx]
                    out.append(item)
        return out

def summarize_site_samples(events,kind):
    keyed=defaultdict(list)
    seen=set()
    for rec in events:
        core=str(rec.get("source_coreid","")).strip()
        if not core or core in seen:raise ValueError("Original Event row coreid is missing or duplicate")
        seen.add(core)
        island=norm(rec.get("island"))
        if island!="terceira":continue
        key=normalized_site(rec.get("locationID"))
        if not key or not key.startswith("TER"):raise ValueError("Terceira site identifier absent or unsupported")
        try:
            lat=float(rec.get("decimalLatitude"))
            lon=float(rec.get("decimalLongitude"))
        except (TypeError,ValueError):
            raise ValueError("Original source plot coordinates missing")
        if not all(map(math.isfinite,(lat,lon))):
            raise ValueError("Nonfinite Terceira sampling coordinates")
        date=str(rec.get("eventDate","")).strip()
        yr=date[:4]
        if yr not in ("2012","2013"):
            raise ValueError("Terceira original sampling not in 2012/2013")
        if str(rec.get("year","")).strip() and str(rec.get("year","")).strip()!=yr:
            raise ValueError("Original Event year and date mismatch")
        mode=norm(rec.get("samplingProtocol"))
        if not mode: raise ValueError("Event sampling mode unspecified")
        keyed[key].append({"core":core,"lat":lat,"lon":lon,"year":int(yr),"method":mode})
    if len(keyed)!=10:
        raise ValueError(f"Original {kind} source yields {len(keyed)} Terceira plot keys, not 10")
    return keyed

def qualify(tree,beetle,contract):
    expected=contract["original_published_counts"]
    if len(tree)!=expected["woody_Event"] or len(beetle)!=expected["beetle_Event"]:
        raise ValueError("Published original Event source size changed")
    t=summarize_site_samples(tree,"woody")
    b=summarize_site_samples(beetle,"beetle")
    if len(t)!=10 or len(b)!=10 or set(t)!=set(b):
        raise ValueError("Exact normalized original author Terceira plot bijection fails")
    if any(len(v)!=1 for v in t.values()):
        raise ValueError("Tree original Event has duplicate physical plot rows")
    coordinate_diffs=[];year_gaps=[];methods=[]
    for key in sorted(t):
        tv=t[key];bv=b[key]
        tr=tv[0]
        bcoords_lat=[v["lat"] for v in bv]
        bcoords_lon=[v["lon"] for v in bv]
        # Any within-original-plot inconsistent coordinates is a scientific STOP.
        latdiff=max(abs(x-tr["lat"]) for x in bcoords_lat)
        londiff=max(abs(x-tr["lon"]) for x in bcoords_lon)
        coordinate_diffs.append((latdiff,londiff))
        year_gaps.append(min(abs(tr["year"]-x["year"]) for x in bv))
        methods.append(Counter(x["method"] for x in bv))
    most_diff=max(max(x) for x in coordinate_diffs)
    effort=[sum(x.values()) for x in methods]
    common=set.intersection(*[set(v) for v in methods]) if methods else set()
    maxeffort=max(effort);mineffort=min(effort)
    thresh=contract["site_join"]
    coords_ok=most_diff<=0.0003
    date_ok=max(year_gaps)<=2
    effort_ok=(mineffort>=8 and maxeffort/mineffort<=1.5 and len(common)>=4)
    matched_pairs=[
      str(k)+"|"+str(t[k][0]["core"])+"|"+",".join(sorted(x["core"] for x in b[k]))
      for k in sorted(t)]
    joined_fingerprint=hashlib.sha256("\n".join(matched_pairs).encode()).hexdigest()
    return {
        "schema":"structural.biomoni_terceira_site_crosswalk_result.v1_298",
        "status":("EXACT_TEN_COLOCATED_PLOTS_METHODS_COMPARABLE_RESPONSES_SEALED"
                  if coords_ok and date_ok and effort_ok else
                  "TERMINAL_COORDINATES_DATES_OR_METHOD_EFFORT_NOT_COMPARABLE"),
        "source_original_sha256":{k:SOURCE[k][1] for k in SOURCE},
        "original_woody_Event_rows_examined":len(tree),
        "original_beetle_Event_rows_examined":len(beetle),
        "unique_tree_Terceira_sites":len(t),
        "unique_beetle_Terceira_sites":len(b),
        "exact_author_plot_bijection":True,
        "all_ten_tree_sites_one_original_Event_each":all(len(x)==1 for x in t.values()),
        "max_coordinate_absolute_degree_difference":most_diff,
        "paired_coordinate_difference_below_0_0003_deg":coords_ok,
        "max_year_offset_for_paired_sites":max(year_gaps),
        "date_pair_gap_qualifies":date_ok,
        "minimum_beetle_sample_events_per_plot":mineffort,
        "maximum_beetle_sample_events_per_plot":maxeffort,
        "beetle_event_effort_max_min_ratio":maxeffort/mineffort,
        "beetle_sampling_modes_common_to_all_plots":len(common),
        "common_beetle_method_counts_anonymized":[
             {"method_code":f"M{i}","original_site_min_count":min(x[m] for x in methods),
              "original_site_max_count":max(x[m] for x in methods)}
             for i,m in enumerate(sorted(common),1)],
        "methods_effort_meet_source_only_gate":effort_ok,
        "matched_original_coreids_sha256":joined_fingerprint,
        "geographic_identifiers_coords_and_taxon_names_exported":False,
        "Original_tree_Occurrence_rows_opened":0,
        "Original_beetle_Occurrence_rows_opened":0,
        "source_only_qualified_to_freeze_new_response_scoring":coords_ok and date_ok and effort_ok,
        "independent_geographies":1,
        "independent_physical_plots":10,
        "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.biomoni_colocated_terceira_event_crosswalk.v1_298"
        or cfg["status"]!="FROZEN_BEFORE_ORIGINAL_TREE_BEETLE_EVENT_VALUE_ACCESS"
        or any(cfg["source_hashes"][k]!=SOURCE[k][1] for k in SOURCE)
        or any(cfg["source_urls"][k]!=SOURCE[k][0] for k in SOURCE)):
        raise ValueError("Original Terceira two-source crosswalk not frozen")
    result={"schema":"structural.biomoni_terceira_site_crosswalk_result.v1_298",
            "status":"SOURCE_ONLY_TRANSPORT_OR_EVENT_STRUCTURE_STOP",
            "Original_tree_Occurrence_rows_opened":0,"Original_beetle_Occurrence_rows_opened":0,
            "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False}
    try:
        events={}
        for kind,(url,sha) in SOURCE.items():
            request=urllib.request.Request(url,headers={"User-Agent":"Structural-BioMonI-Terceira-Exact-Plot-Join-v1.298"})
            with urllib.request.urlopen(request,timeout=55) as response:
                raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES or hashlib.sha256(raw).hexdigest()!=sha:
                raise ValueError("Original source ZIP SHA256 mismatch")
            events[kind]=extract_event_core_only(raw)
        result=qualify(events["woody"],events["beetle"],cfg)
    except Exception as error:
        result["stop_type"]=type(error).__name__;result["stop_reason"]=str(error)[:300]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
       "status":result["status"],
       "tree_site_n":result.get("unique_tree_Terceira_sites"),
       "beetle_site_n":result.get("unique_beetle_Terceira_sites"),
       "max_latlon_difference":result.get("max_coordinate_absolute_degree_difference"),
       "beetle_method_events_range":[result.get("minimum_beetle_sample_events_per_plot"),
                                     result.get("maximum_beetle_sample_events_per_plot")],
       "common_methods_n":result.get("beetle_sampling_modes_common_to_all_plots"),
       "tree_beetle_occurrence_rows_opened":0,
       "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_ONLY_TRANSPORT_OR_EVENT_STRUCTURE_STOP":
        raise SystemExit(2)

if __name__=="__main__":main()
