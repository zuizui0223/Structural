#!/usr/bin/env python3
"""SLAM v1.326 original 893 Event rows ONLY: author forest-habitat balance.

Strict original source SHA, 42 actual forest trap IDs, island/date/season,
sampling method, per-plot invariant habitat category and geographic matching.
Original 14,922 species/status Occurrence rows are NEVER read.
No post-Event habitat relabel or source-site subset rescue is authorised.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,unicodedata,urllib.request,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=arthropods_slam_azores&v=1.7"
SHA="b86f7fad6468d2fb9aa9473849effe41ba2c4405c786357b6f50d66d9ef552a0"
MAX_BYTES=1_600_000

def local(s):return s.rsplit("}",1)[-1]
def term(s):return s.rstrip("/").split("/")[-1].split("#")[-1]
def normalize(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).casefold().strip()
def siteid(s):
    text=normalize(s).upper()
    return "".join(c for c in text if ("A"<=c<="Z" or "0"<=c<="9"))
def mode(s):return " ".join(normalize(s).split())
def habitat(s,ontology):
    key=" ".join(normalize(s).replace("_"," ").replace("-"," ").split())
    options={
        group:{" ".join(normalize(x).replace("_"," ").replace("-"," ").split())
               for x in strings}
        for group,strings in ontology.items() if group in ("native","mixed","exotic")
    }
    matched=[group for group,candidates in options.items() if key in candidates]
    return matched[0] if len(matched)==1 else None
def _island(value,aliases):
    key=siteid(value)
    for island,variants in aliases.items():
        if any(siteid(name)==key for name in variants):return island
    return None
def _calendar(value):
    value=str(value or "").strip()
    match=re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:$|[/T\s])",value)
    if not match:raise ValueError("Non ISO original SLAM eventDate; cannot invent year/season")
    year,month,day=map(int,match.groups())
    if not (2012<=year<=2022 and 1<=month<=12 and 1<=day<=31):
        raise ValueError("Original Event date outside frozen 2012-2022")
    return year,(month-1)//3+1

def event_core_only(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        if len(cores)!=1:raise ValueError("Original SLAM source missing sole Event core")
        node=cores[0]
        cols={};data=[];idx=None
        for child in node.iter():
            tag=local(child.tag)
            if tag=="field" and "index" in child.attrib and "term" in child.attrib:
                cols[term(child.attrib["term"])]=int(child.attrib["index"])
            elif tag=="location" and child.text:data.append(child.text.strip())
            elif tag=="id" and "index" in child.attrib:idx=int(child.attrib["index"])
        expected={"eventID","eventDate","island","samplingProtocol","locationID",
                  "habitat","decimalLatitude","decimalLongitude"}
        if idx is None or len(data)!=1 or not expected.issubset(cols):
            raise ValueError("Original source has no author physical site/forest habitat/geographic Event variables")
        sep=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        skip=int(node.attrib.get("ignoreHeaderLines","0"))
        if len(sep)!=1 or skip not in (0,1):
            raise ValueError("Unsupported Event serialization in original SLAM zip")
        rows=[]
        with z.open(data[0]) as source:
            with io.TextIOWrapper(source,encoding="utf-8-sig",newline="") as s:
                reader=csv.reader(s,delimiter=sep)
                for _ in range(skip):next(reader,None)
                for row in reader:
                    if not row or not any(row):continue
                    if max(idx,*(cols[k] for k in expected))>=len(row):
                        raise ValueError("Malformed original Event row")
                    r={k:row[v] for k,v in cols.items() if v<len(row)}
                    r["__original_coreid"]=row[idx]
                    rows.append(r)
        return rows

def audit(events,contract):
    if len(events)!=893:raise ValueError("Original v1.7 event row count not 893")
    site_recs=defaultdict(list)
    islands=contract["fixed_island_aliases"]
    habitatdict=contract["habitat_ontology_frozen"]
    source_methods=Counter()
    years=Counter()
    unknown_hab=Counter()
    seen=set()
    problems=Counter()
    for row in events:
        core=str(row.get("__original_coreid","")).strip()
        if not core or core in seen:
            raise ValueError("Original Event ID missing or duplicate")
        seen.add(core)
        isl=_island(row.get("island"),islands)
        if isl is None:
            problems["unrecognized_original_island"]+=1
            continue
        ident=siteid(row.get("locationID"))
        if not ident:
            problems["empty_original_plot_locationID"]+=1
            continue
        yr,q=_calendar(row.get("eventDate"))
        if str(row.get("year","")).strip() and str(row["year"]).strip()!=str(yr):
            problems["original_source_year_date_mismatch"]+=1
        try:
            lat=float(row.get("decimalLatitude"))
            lon=float(row.get("decimalLongitude"))
        except (TypeError,ValueError):
            lat=lon=float("nan")
        if not (math.isfinite(lat) and math.isfinite(lon)):
            problems["original_source_missing_coordinate"]+=1
        met=mode(row.get("samplingProtocol"))
        if not met:problems["missing_original_samplingProtocol"]+=1
        category=habitat(row.get("habitat"),habitatdict)
        if category is None:
            # Report only hash and aggregated unknown source string frequency.
            digest=hashlib.sha256(mode(row.get("habitat")).encode()).hexdigest()[:12]
            unknown_hab[digest]+=1
        source_methods[met]+=1
        years[(yr,q)]+=1
        site_recs[(isl,ident)].append({
            "core":core,"year":yr,"quarter":q,"category":category,
            "method":met,"lat":lat,"lon":lon
        })
    physical_site_n=len(site_recs)
    per_island_habitat=defaultdict(Counter)
    changed_site_categories=0
    coordinate_site_outlier_n=0
    unclassified_site_count=0
    qualified_sites={}
    for (isl,ident),rows in site_recs.items():
        categories={r["category"] for r in rows if r["category"]}
        if len(categories)>1:
            changed_site_categories+=1
            continue
        category=next(iter(categories)) if categories else None
        if category is None:
            unclassified_site_count+=1
        else:
            per_island_habitat[isl][category]+=1
        first=rows[0]
        if any(not math.isfinite(v["lat"]) or not math.isfinite(v["lon"])
               or max(abs(v["lat"]-first["lat"]),abs(v["lon"]-first["lon"]))>0.0003
               for v in rows):
            coordinate_site_outlier_n+=1
        qualified_sites[(isl,ident)]=category
    if len(per_island_habitat)>7:raise AssertionError("More than seven Azores island contexts")
    # Freeze dominant original source method by metadata-only Event frequency.
    # Any ties resolve lexicographically, before taxonomic rows are open.
    source_mode=min(
        [m for m,n in source_methods.items() if m and n==max(source_methods.values())],
        default=None
    )
    strata=defaultdict(lambda:defaultdict(set))
    windows_by_island=defaultdict(list)
    if source_mode:
        for (isl,ident),rows in site_recs.items():
            category=qualified_sites.get((isl,ident))
            if category is None:continue
            stratum="native" if category=="native" else "altered"
            for row in rows:
                if row["method"]==source_mode:
                    strata[(isl,row["year"],row["quarter"])][stratum].add((isl,ident))
        for (isl,yr,q),groups in sorted(strata.items()):
            n_native=len(groups.get("native",set()))
            n_altered=len(groups.get("altered",set()))
            if n_native>=2 and n_altered>=2:
                windows_by_island[isl].append((yr,q,n_native,n_altered))
    selected=[]
    selected_site_ids=set()
    for (isl,yr,q),groups in sorted(strata.items()):
        if not (len(groups.get("native",set()))>=2 and len(groups.get("altered",set()))>=2):
            continue
        for kind in ("native","altered"):
            for site in sorted(groups[kind]):
                chosen=min(
                    (r["core"] for r in site_recs[site]
                     if (r["year"],r["quarter"],r["method"])==(yr,q,source_mode)),
                    default=None
                )
                if not chosen:raise AssertionError("Source site-season match has no original core ID")
                selected.append(chosen)
                selected_site_ids.add(site)
    supporting_islands=sorted(k for k,v in windows_by_island.items() if v)
    target=contract["critical_sampling_and_comparison_gate"]
    if not (
      physical_site_n==42 and len(per_island_habitat)>=1
      and physical_site_n-unclassified_site_count-changed_site_categories>=30
      and not problems and not changed_site_categories and not coordinate_site_outlier_n
      and len(supporting_islands)>=2
    ):
        status="TERMINAL_NO_TWO_ISLAND_NATIVE_VS_ALTERED_SAME_WINDOW_REPLICATION"
    else:
        status="ORIGINAL_SLAM_FOREST_HABITAT_STRATA_ELIGIBLE_TAXON_RESPONSES_SEALED"
    return {
      "schema":"structural.slam_original_forest_habitat_event_only_result.v1_326",
      "status":status,
      "original_Event_rows_opened":len(events),
      "original_Occurrence_rows_opened":0,
      "source_original_SHA256":SHA,
      "original_distinct_author_island_site_keys":physical_site_n,
      "original_source_event_year_quarter_counts":{
         f"{year}-Q{quarter}":count for (year,quarter),count in sorted(years.items())
      },
      "source_samplingProtocol_vocabulary_anonymized_SHA_counts":{
         hashlib.sha256(m.encode()).hexdigest()[:12]:count
         for m,count in sorted(source_methods.items())
      },
      "source_dominant_original_method_SHA256":hashlib.sha256(source_mode.encode()).hexdigest() if source_mode else None,
      "source_recognized_native_mixed_exotic_independent_site_counts":{
         isl:{kind:per_island_habitat[isl].get(kind,0) for kind in ("native","mixed","exotic")}
         for isl in islands
      },
      "source_habitat_ontology_unrecognized_Event_value_hash_counts":dict(sorted(unknown_hab.items())),
      "source_unrecognized_habitat_physical_site_count":unclassified_site_count,
      "source_plot_conflicting_original_habitat_categories_count":changed_site_categories,
      "source_plot_coordinate_mismatch_above_0_0003_degrees_count":coordinate_site_outlier_n,
      "source_bad_Event_metadata_counts":dict(sorted(problems.items())),
      "islands_with_at_least_one_same_yearquarter_two_native_two_altered_forest_plot_stratum":supporting_islands,
      "source_original_island_year_quarter_eligible_strata":{
          isl:[{"year":yr,"quarter":q,"native_plots":nn,"altered_plots":na}
               for yr,q,nn,na in windows_by_island.get(isl,[])] for isl in islands
      },
      "source_selected_physical_plots_with_matched_habitat_period_method":len(selected_site_ids),
      "source_selected_original_Event_rows_in_matched_habitat_strata":len(selected),
      "source_selected_original_Event_coreids_SHA256":hashlib.sha256(
          "\n".join(sorted(selected)).encode()).hexdigest(),
      "source_selected_original_physical_plot_key_SHA256":hashlib.sha256(
          "\n".join(f"{isl}|{ident}" for isl,ident in sorted(selected_site_ids)).encode()).hexdigest(),
      "original_plot_ids_coordinates_species_habitat_unmapped_values_not_exported":True,
      "old_BALA_PRIBES_biology_source_reopened":False,
      "v325_original_Meta_source_identity_frozen":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.slam_forest_explicit_habitat_event_gate.v1_326"
        or c.get("status")!="FROZEN_BEFORE_FIRST_ORIGINAL_SLAM_EVENT_VALUES"
        or c["source"]["official_archive"]!=SOURCE
        or c["source"]["original_zip_SHA256"]!=SHA):
        raise ValueError("SLAM source habitat Event gate not frozen")
    result={
      "schema":"structural.slam_original_forest_habitat_event_only_result.v1_326",
      "status":"ORIGINAL_SLAM_SOURCE_OR_EVENT_READER_TECHNICAL_STOP",
      "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-SLAM-original-habitat-Event-only-v1.326"})
        with urllib.request.urlopen(req,timeout=70) as r:source=r.read(MAX_BYTES+1)
        if len(source)>MAX_BYTES or hashlib.sha256(source).hexdigest()!=SHA:
            raise ValueError("Original SLAM forest survey source SHA/cap mismatch")
        result=audit(event_core_only(source),c)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:330]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:result.get(k) for k in (
        "status","original_Event_rows_opened","original_distinct_author_island_site_keys",
        "source_recognized_native_mixed_exotic_independent_site_counts",
        "source_unrecognized_habitat_physical_site_count",
        "source_plot_conflicting_original_habitat_categories_count",
        "source_plot_coordinate_mismatch_above_0_0003_degrees_count",
        "islands_with_at_least_one_same_yearquarter_two_native_two_altered_forest_plot_stratum",
        "source_selected_original_Event_rows_in_matched_habitat_strata",
        "original_Occurrence_rows_opened","stop_reason"
    )},sort_keys=True))
    if result["status"]=="ORIGINAL_SLAM_SOURCE_OR_EVENT_READER_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
