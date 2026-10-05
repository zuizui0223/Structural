#!/usr/bin/env python3
"""Response-unopened Event-core audit for the Azores SLAM DwC-A.

The Occurrence extension may be hashed and physically line-counted as bytes, but
is never decoded. Only archive metadata XML and the Event core are semantically
opened.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import (
    Stop, parse_meta, parse_xml_bytes, parse_event_core, read_member,
    local_name, find_child_text, year_from, norm
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/azores_slam_event_core_audit_contract_v1_146.json"

def sha_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def candidate_key(rec,key,decimals):
    if key=="locationID":
        return norm(rec.get("locationID",""))
    if key=="parentEventID":
        return norm(rec.get("parentEventID",""))
    if key=="island_plus_locality":
        a=norm(rec.get("island",""));b=norm(rec.get("locality",""))
        return f"{a}|{b}" if a and b else ""
    if key=="rounded_latitude_longitude_plus_island":
        a=norm(rec.get("island",""))
        try:
            lat=round(float(norm(rec.get("decimalLatitude",""))),decimals)
            lon=round(float(norm(rec.get("decimalLongitude",""))),decimals)
        except Exception:
            return ""
        return f"{a}|{lat:.{decimals}f}|{lon:.{decimals}f}" if a else ""
    raise Stop(f"unknown site key {key}")

def island_name(rec):
    x=norm(rec.get("island",""))
    if x:return x
    # Fallback only for reporting; final island mapping must be frozen later.
    return norm(rec.get("islandGroup","")) or norm(rec.get("locality",""))

def physical_data_rows(raw:bytes,ignore_header_lines:int)->int:
    # Do not decode occurrence bytes. DwC-A extension rows are physical lines.
    lines=[x for x in raw.splitlines() if x.strip()]
    n=len(lines)-int(ignore_header_lines)
    if n<0:raise Stop("negative occurrence physical-row count")
    return n

def audit_site_key(rows,key,decimals,years,contract):
    # Response-independent site/year/event support.
    by_site_year=defaultdict(int)
    by_island_year=defaultdict(int)
    site_island={}
    nonblank=0
    for r in rows:
        y=year_from(r)
        k=candidate_key(r,key,decimals)
        isl=island_name(r)
        if y is None or not k or not isl:continue
        nonblank+=1
        by_site_year[(k,y)]+=1
        by_island_year[(isl,y)]+=1
        site_island.setdefault(k,isl)
        if site_island[k]!=isl:
            raise Stop(f"site key maps to multiple islands: {key} {k}")

    unique_sites=len({k for k,_ in by_site_year})
    unique_islands=len({i for i,_ in by_island_year})
    year_rows=[]
    for (site,y),n in sorted(by_site_year.items(),key=lambda z:(z[0][1],z[0][0])):
        year_rows.append({
          "candidate_key":key,"site_key":site,"island":site_island[site],
          "year":y,"event_rows":n
        })

    win=int(contract["event_coverage_audit"]["window_width_years"])
    min_evt=int(contract["event_coverage_audit"]["provisional_min_events_per_island_year"])
    min_isl=int(contract["event_coverage_audit"]["minimum_islands_per_window"])
    windows=[]
    if years:
        for start in range(min(years),max(years)-win+2):
            yrs=list(range(start,start+win))
            good_islands=[]
            for isl in sorted({i for i,_ in by_island_year}):
                if all(by_island_year.get((isl,y),0)>=min_evt for y in yrs):
                    good_islands.append(isl)
            core_sites=[]
            for site in sorted(site_island):
                if all(by_site_year.get((site,y),0)>0 for y in yrs):
                    core_sites.append(site)
            windows.append({
              "candidate_key":key,
              "start_year":start,
              "end_year":start+win-1,
              "islands_meeting_event_rule":len(good_islands),
              "island_names":";".join(good_islands),
              "sites_observed_all_years":len(core_sites),
              "eligible_provisional":len(good_islands)>=min_isl
            })
    return {
      "candidate_key":key,
      "nonblank_event_fraction": nonblank/len(rows) if rows else 0.0,
      "unique_sites":unique_sites,
      "unique_islands":unique_islands,
      "site_year_rows":year_rows,
      "windows":windows
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.azores_slam_event_core_audit_contract.v1_146":
        raise Stop("contract schema drift")

    req=urllib.request.Request(
      c["source"]["dwca_url"],
      headers={"User-Agent":"Structural-SLAM-event-audit/1.0"}
    )
    try:
        with urllib.request.urlopen(req,timeout=120) as resp:raw=resp.read()
    except Exception as e:
        raise Stop(f"DwC-A download failed: {e}") from e
    if not raw.startswith(b"PK"):raise Stop("download is not ZIP")
    z=zipfile.ZipFile(io.BytesIO(raw))
    infos=z.infolist()
    if not infos:raise Stop("empty archive")

    inventory=[]
    for info in infos:
        b=read_member(z,info.filename)
        inventory.append({
          "path":info.filename,
          "compressed_bytes":info.compress_size,
          "uncompressed_bytes":info.file_size,
          "crc32":f"{info.CRC:08x}",
          "sha256":sha_bytes(b)
        })

    meta_names=[x.filename for x in infos if Path(x.filename).name.lower()=="meta.xml"]
    if len(meta_names)!=1:raise Stop(f"expected one meta.xml, found {len(meta_names)}")
    meta_bytes=read_member(z,meta_names[0])
    core,exts=parse_meta(meta_bytes)
    if not core["rowType"].endswith(c["source"]["expected_core_row_type_suffix"]):
        raise Stop(f"core rowType is not Event: {core['rowType']}")
    occ=[e for e in exts if e["rowType"].endswith("/Occurrence")]
    if len(occ)!=1:raise Stop(f"expected one Occurrence extension, found {len(occ)}")
    occ_meta=occ[0]
    occ_bytes=read_member(z,occ_meta["location"])
    occ_rows=physical_data_rows(occ_bytes,occ_meta["ignoreHeaderLines"])
    if occ_rows not in {
        int(c["source"]["published_occurrence_extension_records"]),
        int(c["source"]["published_methods_occurrence_records"])
    }:
        raise Stop(f"Occurrence physical-row count does not resolve published discrepancy: {occ_rows}")

    event_bytes=read_member(z,core["location"])
    rows,index_to_name=parse_event_core(event_bytes,core)
    if len(rows)!=int(c["source"]["expected_event_records"]):
        raise Stop(f"Event record count drift: {len(rows)}")

    eml_candidates=[
      x.filename for x in infos
      if x.filename.lower().endswith(".xml") and Path(x.filename).name.lower()!="meta.xml"
    ]
    meta_root=parse_xml_bytes(meta_bytes)
    metadata_attr=meta_root.attrib.get("metadata")
    if metadata_attr and metadata_attr in {x.filename for x in infos}:
        eml_name=metadata_attr
    else:
        pref=[x for x in eml_candidates if "eml" in Path(x).name.lower()]
        if len(pref)!=1:raise Stop("cannot resolve unique EML metadata file")
        eml_name=pref[0]
    eml_bytes=read_member(z,eml_name)
    eml_root=parse_xml_bytes(eml_bytes)

    years=[year_from(r) for r in rows if year_from(r) is not None]
    if not years:raise Stop("no Event years")
    if min(years)>int(c["event_coverage_audit"]["expected_program_year_min"]):
        raise Stop("Event minimum year later than frozen program start")
    if max(years)<int(c["event_coverage_audit"]["expected_program_year_max_at_least"]):
        raise Stop("Event maximum year earlier than frozen minimum")

    fields=sorted({k for r in rows for k in r})
    field_manifest=[
      {"field":k,
       "nonblank_rows":sum(bool(norm(r.get(k,""))) for r in rows),
       "unique_nonblank":len({norm(r.get(k,"")) for r in rows if norm(r.get(k,""))})}
      for k in fields
    ]

    protocols=Counter(norm(r.get("samplingProtocol","")) for r in rows)
    islands=Counter(island_name(r) for r in rows if island_name(r))
    year_counts=Counter(year_from(r) for r in rows if year_from(r) is not None)

    audits=[]
    site_year_rows=[]
    window_rows=[]
    dec=int(c["site_key_audit"]["coordinate_rounding_decimals"])
    for key in c["site_key_audit"]["candidate_keys"]:
        q=audit_site_key(rows,key,dec,years,c)
        audits.append({k:v for k,v in q.items() if k not in {"site_year_rows","windows"}})
        site_year_rows.extend(q["site_year_rows"])
        window_rows.extend(q["windows"])

    eligible_by_key={}
    for q in audits:
        key=q["candidate_key"]
        eligible_by_key[key]=sum(
          1 for w in window_rows
          if w["candidate_key"]==key and w["eligible_provisional"]
        )

    result={
      "schema":"structural.azores_slam_event_core_audit_result.v1_146",
      "status":"SLAM_EVENT_CORE_RESPONSE_UNOPENED_AUDIT_COMPLETE",
      "archive_bytes":len(raw),
      "archive_sha256":sha_bytes(raw),
      "archive_member_count":len(inventory),
      "meta_xml_path":meta_names[0],
      "meta_xml_sha256":sha_bytes(meta_bytes),
      "eml_path":eml_name,
      "eml_sha256":sha_bytes(eml_bytes),
      "event_core_path":core["location"],
      "event_core_sha256":sha_bytes(event_bytes),
      "event_records":len(rows),
      "event_year_min":min(years),
      "event_year_max":max(years),
      "event_distinct_years":sorted(set(years)),
      "event_rows_by_year":dict(sorted(year_counts.items())),
      "event_rows_by_island":dict(sorted(islands.items())),
      "sampling_protocol_counts":dict(sorted(protocols.items())),
      "occurrence_extension_path":occ_meta["location"],
      "occurrence_extension_sha256_opaque_bytes":sha_bytes(occ_bytes),
      "occurrence_extension_physical_data_rows":occ_rows,
      "published_row_count_discrepancy_resolved_to":occ_rows,
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,
      "taxon_occurrence_values_opened":0,
      "candidate_site_key_audits":audits,
      "provisional_eligible_three_year_windows_by_key":eligible_by_key,
      "final_site_key_selected":False,
      "temporal_windows_selected":False,
      "eml_title":find_child_text(eml_root,"title"),
      "eml_pub_date":find_child_text(eml_root,"pubDate"),
      "source_loss_effects_computed":0,
      "confirmatory_eligible":False,
      "next_gate":"freeze one deterministic site key and the earliest/latest non-overlapping eligible three-year windows from Event data only; Occurrence extension remains sealed"
    }

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    with (out/"archive_inventory.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["path","compressed_bytes","uncompressed_bytes","crc32","sha256"],lineterminator="\n")
        w.writeheader();w.writerows(inventory)
    meta_manifest={"core":core,"extensions":exts,"metadata_file":eml_name}
    (out/"meta_manifest.json").write_text(json.dumps(meta_manifest,indent=2,sort_keys=True)+"\n")
    with (out/"event_field_manifest.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["field","nonblank_rows","unique_nonblank"],lineterminator="\n")
        w.writeheader();w.writerows(field_manifest)
    with (out/"site_key_candidates.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["candidate_key","nonblank_event_fraction","unique_sites","unique_islands"],lineterminator="\n")
        w.writeheader();w.writerows(audits)
    with (out/"site_year_coverage.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["candidate_key","site_key","island","year","event_rows"],lineterminator="\n")
        w.writeheader();w.writerows(site_year_rows)
    with (out/"three_year_window_candidates.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["candidate_key","start_year","end_year","islands_meeting_event_rule","island_names","sites_observed_all_years","eligible_provisional"],lineterminator="\n")
        w.writeheader();w.writerows(window_rows)
    (out/"event_core_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
