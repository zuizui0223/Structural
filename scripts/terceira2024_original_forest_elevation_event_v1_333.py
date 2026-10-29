#!/usr/bin/env python3
"""v1.333: original 2024 Terceira 20 forest plots vs ELEVATION common support.

The only source bytes decompressed are original v1.6 meta.xml and the
326-row Darwin Core EVENT member. The 2,399 original occurrence/species
responses are NEVER read. A balanced 10/10 native/exotic habitat design
is not enough to estimate a forest effect when elevation ranges do not
overlap. No extrapolation, original site migration, or post-Event taxon read.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,unicodedata,urllib.request,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=azores_forest_arthropods&v=1.6"
SHA="c4dcf060bc2554be7fe49fb569f2fd7a8514ba3a888db673b40cb65aad60ef21"
CAP=400000

def local(t):return t.rsplit("}",1)[-1]
def term(t):return t.rstrip("/").split("/")[-1].split("#")[-1]
def normalize(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).casefold().strip()
def canonical(s):
    return " ".join(re.sub(r"[^a-z0-9]+"," ",normalize(s)).split())
def locationID(s):
    return "".join(c for c in canonical(s).upper() if "A"<=c<="Z" or "0"<=c<="9")
def habitat(s,p):
    text=canonical(s)
    labels=p["author_site_design"]
    natives={canonical(x) for x in labels["source_habitat_native_exact"]}
    exotica={canonical(x) for x in labels["source_habitat_exotic_exact"]}
    return ("native" if text in natives else "exotic" if text in exotica else "unknown")
def method(s):
    s=canonical(s)
    sl="slam" in s or "malaise" in s or "flight interception" in s
    pt="pitfall" in s or "pit fall" in s or "epigean" in s
    if sl and pt:return "ambiguous"
    if sl:return "SLAM"
    if pt:return "Pitfall"
    return "unknown"
def vertical(event,method_label):
    source=" ".join(canonical(event.get(k)) for k in ("eventRemarks","locationRemarks","samplingProtocol"))
    if method_label=="Pitfall":return "EPI"
    if method_label!="SLAM":return "UNKNOWN"
    labels={
        "GRD":("grd","ground","0 percent","0%"),
        "UND":("und","understorey","understory","50 percent","50%"),
        "CAN":("can","canopy","75 percent","75%"),
    }
    found=[]
    for name,words in labels.items():
        if any(re.search(r"(?<![a-z0-9])"+re.escape(canonical(w))+r"(?![a-z0-9])",source)
               for w in words if canonical(w)):
            found.append(name)
    return found[0] if len(found)==1 else "UNKNOWN"
def event_date(d):
    s=str(d or "").strip()
    m=re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:$|[/T\s])",s)
    if not m:
        raise ValueError("Original 2024 forest Event date not ISO YYYY-MM-DD")
    y,mo,day=map(int,m.groups())
    if y!=2024 or not 1<=mo<=12 or not 1<=day<=31:
        raise ValueError("Original forest Event outside field year 2024")
    return y,mo

def read_event_core_only(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        if len(cores)!=1:
            raise ValueError("Original dataset lacks unique Event source core")
        node=cores[0];fields={};ids=None;locations=[]
        for x in node.iter():
            key=local(x.tag)
            if key=="field" and "index" in x.attrib and x.attrib.get("term"):
                fields[term(x.attrib["term"])]=int(x.attrib["index"])
            elif key=="location" and x.text:
                locations.append(x.text.strip())
            elif key=="id" and "index" in x.attrib:
                ids=int(x.attrib["index"])
        required={"eventID","eventDate","locationID","habitat","samplingProtocol",
                  "minimumElevationInMeters","decimalLatitude","decimalLongitude"}
        if ids is None or len(locations)!=1 or not required.issubset(fields):
            raise ValueError("Original 2024 source Event site/altitude/habitat metadata insufficient")
        delim=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        skip=int(node.attrib.get("ignoreHeaderLines","0"))
        if len(delim)!=1 or skip not in (0,1):
            raise ValueError("Original 2024 source TSV serialization unknown")
        rows=[]
        with z.open(locations[0]) as original_event:
            with io.TextIOWrapper(original_event,encoding="utf-8-sig",newline="") as f:
                rd=csv.reader(f,delimiter=delim)
                for _ in range(skip):next(rd,None)
                for row in rd:
                    if not row or not any(row):continue
                    if max(ids,*(fields[x] for x in required))>=len(row):
                        raise ValueError("Original source Event field index out of bounds")
                    entry={name:row[idx] for name,idx in fields.items() if idx<len(row)}
                    entry["__author_original_coreid"]=row[ids]
                    rows.append(entry)
        return rows

def audit_source(events,p):
    if len(events)!=326:
        raise ValueError("Original v1.6 forest source Event denominator not 326")
    sites=defaultdict(list);seen=set();problems=Counter()
    for e in events:
        core=str(e.get("__author_original_coreid","")).strip()
        if not core or core in seen:
            raise ValueError("Original Event source coreID duplicated or empty")
        seen.add(core)
        site=locationID(e.get("locationID"))
        if not site:
            problems["missing_physical_locationID"]+=1;continue
        event_date(e.get("eventDate"))
        k=habitat(e.get("habitat"),p)
        method_type=method(e.get("samplingProtocol"))
        strat=vertical(e,method_type)
        try:
            elev=float(e.get("minimumElevationInMeters"))
            lat=float(e.get("decimalLatitude"))
            lon=float(e.get("decimalLongitude"))
        except (ValueError,TypeError):
            elev=lat=lon=math.nan
        if not all(math.isfinite(x) for x in (elev,lat,lon)):
            problems["invalid_original_plot_elevation_or_coordinates"]+=1
        sites[site].append({
            "core":core,"habitat":k,"method":method_type,
            "stratum":strat,"elevation":elev,"lat":lat,"lon":lon
        })
    site_habitats={}
    site_elev={}
    source_strata=Counter()
    source_methods=Counter()
    conflicts=Counter()
    for site,records in sites.items():
        habitats={x["habitat"] for x in records}
        if len(habitats)!=1 or "unknown" in habitats:
            conflicts["inconsistent_or_unknown_author_forest_class"]+=1
            continue
        typ=next(iter(habitats))
        first=records[0]
        for x in records:
            source_strata[(x["method"],x["stratum"],typ)]+=1
            source_methods[x["method"]]+=1
            if (not math.isfinite(x["elevation"]) or not math.isfinite(first["elevation"])
                or abs(x["elevation"]-first["elevation"])>5):
                conflicts["repeated_site_elevation_inconsistent"]+=1
            if (not math.isfinite(x["lat"]) or not math.isfinite(x["lon"])
                or max(abs(x["lat"]-first["lat"]),abs(x["lon"]-first["lon"]))>0.0003):
                conflicts["repeated_site_coordinates_inconsistent"]+=1
        site_habitats[site]=typ
        site_elev[site]=first["elevation"]
    category_sites=defaultdict(list)
    for site,typ in site_habitats.items():
        category_sites[typ].append(site)
    native=[site_elev[s] for s in category_sites["native"] if math.isfinite(site_elev[s])]
    exotic=[site_elev[s] for s in category_sites["exotic"] if math.isfinite(site_elev[s])]
    overlap=None
    overlap_n={"native":0,"exotic":0}
    if native and exotic:
        lo=max(min(native),min(exotic))
        hi=min(max(native),max(exotic))
        if lo<=hi:
            overlap=[lo,hi]
            overlap_n={
                "native":sum(lo<=x<=hi for x in native),
                "exotic":sum(lo<=x<=hi for x in exotic)}
    grd_sites=defaultdict(set)
    for site,rec in sites.items():
        for e in rec:
            if e["method"]=="SLAM" and e["stratum"]=="GRD":
                grd_sites[e["habitat"]].add(site)
    counts={kind:len(category_sites[kind]) for kind in ("native","exotic")}
    source_raw_good=(
        not problems and not conflicts
        and len(sites)==20
        and counts=={"native":10,"exotic":10}
        and source_methods.get("ambiguous",0)==0
    )
    overlap_good=(
        overlap is not None
        and overlap_n["native"]>=2 and overlap_n["exotic"]>=2
    )
    trapping_good=(
        len(grd_sites["native"])>=8 and len(grd_sites["exotic"])>=8
    )
    if not source_raw_good:
        status="TERMINAL_2024_ORIGINAL_PHYSICAL_SITE_HABITAT_ELEVATION_QUALITY"
    elif not overlap_good:
        status="TERMINAL_2024_FOREST_ELEVATION_NO_COMMON_SUPPORT"
    elif not trapping_good:
        status="TERMINAL_2024_SLAM_GROUND_EFFORT_NOT_ESTIMABLE"
    else:
        status="ORIGINAL_2024_NATIVE_EXOTIC_SAME_STRATUM_ELEVATION_SUPPORT_ADMITTED_SPECIES_SEALED"
    source_grd=[min(x["core"] for x in rows if x["stratum"]=="GRD" and x["method"]=="SLAM")
                for site,rows in sorted(sites.items())
                if site in grd_sites[site_habitats.get(site,"")]]
    return {
        "schema":"structural.terceira2024_original_environment_identifiability.v1_333",
        "status":status,
        "original_source_zip_SHA256":SHA,
        "original_Event_rows_examined":len(events),
        "original_Occurrence_rows_opened":0,
        "author_original_physical_plot_id_count":len(sites),
        "author_original_native_exotic_plot_counts":counts,
        "native_plot_elevation_range_m":[min(native),max(native)] if native else None,
        "exotic_plot_elevation_range_m":[min(exotic),max(exotic)] if exotic else None,
        "original_native_exotic_common_elevation_interval_m":overlap,
        "original_physical_sites_inside_common_elevation_support":overlap_n,
        "forest_type_elevation_common_support_sufficient":overlap_good,
        "original_plot_source_method_events":dict(sorted(source_methods.items())),
        "source_vertical_method_habitat_Event_counts":{
            f"{method}|{strat}|{hab}":n for (method,strat,hab),n in sorted(source_strata.items())},
        "SLAM_ground_physical_plot_sites_by_forest_type":{
            "native":len(grd_sites["native"]),"exotic":len(grd_sites["exotic"])},
        "matched_source_ground_SLAM_original_Event_ids_SHA256":hashlib.sha256(
            "\n".join(sorted(source_grd)).encode()).hexdigest(),
        "source_metadata_problems":dict(sorted(problems.items())),
        "source_site_metadata_conflicts":dict(sorted(conflicts.items())),
        "original_site_names_raw_geographic_coordinates_and_biota_not_exported":True,
        "source_environment_identifiability_status":"NO_CREDIBLE_HABITAT_ONLY_EFFECT"
            if not overlap_good else "COMMON_ELEVATION_SUPPORT_EXISTS",
        "original_species_response_scoring_allowed":status.startswith("ORIGINAL_2024_NATIVE_EXOTIC_"),
        "v332_original_Event_and_Occurrence_rows_previously_unopened":True,
        "BALA_PRIBES_older_SLAM_Madeira_species_rows_reopened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text())
    if (c.get("schema")!="structural.terceira2024_habitat_elevation_event_identifiability.v1_333"
        or c.get("status")!="SOURCE_EVENT_ONLY_IDENTIFIABILITY_PREDECLARED_BEFORE_ANY_2024_ORIGINAL_EVENT_VALUES"
        or c["source"]["official_original_v1_6_archive"]!=SOURCE
        or c["source"]["source_original_SHA256"]!=SHA):
        raise ValueError("Original 2024 source elevation comparison not frozen")
    result={
        "schema":"structural.terceira2024_original_environment_identifiability.v1_333",
        "status":"SOURCE_OR_EVENT_READER_TECHNICAL_STOP",
        "original_Event_rows_examined":0,
        "original_Occurrence_rows_opened":0,
        "BALA_PRIBES_older_SLAM_Madeira_species_rows_reopened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={
            "User-Agent":"Structural-Terceira2024-forest-elevation-EventOnly-v1.333"})
        with urllib.request.urlopen(req,timeout=65) as f:
            raw=f.read(CAP+1)
        if len(raw)>CAP or hashlib.sha256(raw).hexdigest()!=SHA:
            raise ValueError("Official source archive identity changed")
        result=audit_source(read_event_core_only(raw),c)
    except Exception as error:
        result["stop_type"]=type(error).__name__
        result["stop_reason"]=str(error)[:320]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_plot_count":result.get("author_original_physical_plot_id_count"),
        "original_habitat_plot_counts":result.get("author_original_native_exotic_plot_counts"),
        "native_elevation_range_m":result.get("native_plot_elevation_range_m"),
        "exotic_elevation_range_m":result.get("exotic_plot_elevation_range_m"),
        "common_elevation_interval_m":result.get("original_native_exotic_common_elevation_interval_m"),
        "original_source_ground_SLAM_sites":result.get("SLAM_ground_physical_plot_sites_by_forest_type"),
        "Occur_rows_opened":result["original_Occurrence_rows_opened"],
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="SOURCE_OR_EVENT_READER_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":
    main()
