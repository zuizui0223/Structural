#!/usr/bin/env python3
"""Freeze the BALA three-wave repeated core panel from Event metadata only."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request,zipfile
from collections import defaultdict
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_core_panel_contract_v1_129.json"
class Stop(RuntimeError): pass

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def site_key(r,dec=5):
    island=norm(r.get("island",""))
    try:
        lat=round(float(r.get("decimalLatitude","")),dec)
        lon=round(float(r.get("decimalLongitude","")),dec)
    except Exception:return ""
    if not island:return ""
    return f"{island}|{lat:.{dec}f}|{lon:.{dec}f}"

def phase_for_year(y,windows):
    hits=[p for p,(lo,hi) in windows.items() if y is not None and int(lo)<=y<=int(hi)]
    return hits[0] if len(hits)==1 else None

def csv_join(values):return ";".join(sorted(set(v for v in values if v)))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.bala_core_panel_contract.v1_129":raise Stop("contract schema drift")
    req=urllib.request.Request(c["source"]["dwca_url"],headers={"User-Agent":"Structural-BALA-core-panel/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:raw=resp.read()
    except Exception as e:raise Stop(f"DwC-A download failed: {e}") from e
    if sha_bytes(raw)!=c["source"]["archive_sha256"]:raise Stop("archive SHA drift")
    z=zipfile.ZipFile(io.BytesIO(raw))
    meta_names=[x.filename for x in z.infolist() if Path(x.filename).name.lower()=="meta.xml"]
    if len(meta_names)!=1:raise Stop("meta.xml resolution failed")
    core,exts=parse_meta(read_member(z,meta_names[0]))
    event_bytes=read_member(z,core["location"])
    if sha_bytes(event_bytes)!=c["source"]["event_core_sha256"]:raise Stop("Event core SHA drift")
    occ=[e for e in exts if e["rowType"].endswith("/Occurrence")]
    if len(occ)!=1:raise Stop("Occurrence extension resolution failed")
    occ_bytes=read_member(z,occ[0]["location"])
    if sha_bytes(occ_bytes)!=c["source"]["occurrence_extension_sha256_opaque_bytes"]:raise Stop("opaque Occurrence SHA drift")
    # Occurrence bytes are never decoded or parsed.
    del occ_bytes

    rows,_=parse_event_core(event_bytes,core)
    windows={k:tuple(v) for k,v in c["official_response_independent_metadata"]["phase_windows"].items()}
    dec=int(c["site_identity"]["rounding_decimals"])
    by_phase=defaultdict(set)
    for r in rows:
        y=year_from(r); ph=phase_for_year(y,windows); k=site_key(r,dec)
        if ph and k:by_phase[ph].add(k)
    common=set.intersection(*(by_phase[p] for p in ("BALA1","BALA2","BALA3")))
    if len(common)!=c["site_identity"]["expected_core_sites"]:raise Stop(f"core-site intersection !=30: {len(common)}")

    core_rows=[]
    for r in rows:
        y=year_from(r);ph=phase_for_year(y,windows);k=site_key(r,dec)
        if ph and k in common:
            rr=dict(r);rr["_phase"]=ph;rr["_site_key"]=k;rr["_year"]=y;core_rows.append(rr)
    if len(core_rows)!=c["core_event_rule"]["expected_total_events"]:
        raise Stop(f"core event total drift: {len(core_rows)}")

    islands=sorted({norm(r.get("island","")) for r in core_rows if norm(r.get("island",""))})
    if len(islands)!=c["site_identity"]["expected_core_islands"]:raise Stop(f"core island count drift: {len(islands)}")
    fragments=sorted({norm(r.get("locationRemarks","")) for r in core_rows if norm(r.get("locationRemarks",""))})
    if len(fragments)!=c["core_event_rule"]["expected_fragments_from_locationRemarks"]:
        raise Stop(f"fragment count drift from locationRemarks: {len(fragments)}")

    # Site-level fixed denominator.
    sites=[]
    site_phase=[]
    cross=[]
    multi=[]
    for k in sorted(common):
        rr=[r for r in core_rows if r["_site_key"]==k]
        island=sorted({norm(r.get("island","")) for r in rr})[0]
        lat=sorted({norm(r.get("decimalLatitude","")) for r in rr})[0]
        lon=sorted({norm(r.get("decimalLongitude","")) for r in rr})[0]
        frags=sorted({norm(r.get("locationRemarks","")) for r in rr if norm(r.get("locationRemarks",""))})
        habs=sorted({norm(r.get("habitat","")) for r in rr if norm(r.get("habitat",""))})
        sites.append({
          "site_key":k,"island":island,"decimalLatitude":lat,"decimalLongitude":lon,
          "locationRemarks":csv_join(frags),"habitat":csv_join(habs),
          "total_events":len(rr)
        })
        all_ids=defaultdict(set)
        for ph in ("BALA1","BALA2","BALA3"):
            pr=[r for r in rr if r["_phase"]==ph]
            if not pr:raise Stop(f"empty site-phase cell {k} {ph}")
            ids=sorted({norm(r.get("locationID","")) for r in pr if norm(r.get("locationID",""))})
            prots=sorted({norm(r.get("samplingProtocol","")) for r in pr if norm(r.get("samplingProtocol",""))})
            years=sorted({r["_year"] for r in pr})
            field_numbers=sorted({norm(r.get("fieldNumber","")) for r in pr if norm(r.get("fieldNumber",""))})
            for lid in ids:all_ids[ph].add(lid)
            site_phase.append({
              "site_key":k,"phase":ph,"event_rows":len(pr),"year_min":min(years),"year_max":max(years),
              "locationIDs":csv_join(ids),"locationID_count":len(ids),
              "samplingProtocols":csv_join(prots),"samplingProtocol_count":len(prots),
              "fieldNumber_unique":len(field_numbers)
            })
            if len(ids)>1:multi.append((k,ph,ids))
        cross.append({
          "site_key":k,
          "BALA1_locationIDs":csv_join(all_ids["BALA1"]),
          "BALA2_locationIDs":csv_join(all_ids["BALA2"]),
          "BALA3_locationIDs":csv_join(all_ids["BALA3"]),
          "unique_locationIDs_all_phases":len(set().union(*all_ids.values()))
        })

    # Event counts and coverage.
    phase_event_counts={p:sum(r["_phase"]==p for r in core_rows) for p in ("BALA1","BALA2","BALA3")}
    phase_site_counts={p:len({r["_site_key"] for r in core_rows if r["_phase"]==p}) for p in ("BALA1","BALA2","BALA3")}
    phase_locationID_counts={p:len({norm(r.get("locationID","")) for r in core_rows if r["_phase"]==p and norm(r.get("locationID",""))}) for p in ("BALA1","BALA2","BALA3")}
    protocols=sorted({norm(r.get("samplingProtocol","")) for r in core_rows if norm(r.get("samplingProtocol",""))})
    habitats=sorted({norm(r.get("habitat","")) for r in core_rows if norm(r.get("habitat",""))})

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    def write_csv(path,rows,fields):
        with path.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    write_csv(out/"core_panel_sites.csv",sites,["site_key","island","decimalLatitude","decimalLongitude","locationRemarks","habitat","total_events"])
    write_csv(out/"core_panel_site_phase.csv",site_phase,["site_key","phase","event_rows","year_min","year_max","locationIDs","locationID_count","samplingProtocols","samplingProtocol_count","fieldNumber_unique"])
    write_csv(out/"locationID_crosswalk.csv",cross,["site_key","BALA1_locationIDs","BALA2_locationIDs","BALA3_locationIDs","unique_locationIDs_all_phases"])

    result={
      "schema":"structural.bala_core_panel_result.v1_129",
      "status":"BALA_30_SITE_THREE_WAVE_CORE_PANEL_FROZEN_RESPONSE_UNOPENED",
      "core_sites":len(common),"core_islands":len(islands),"core_island_codes":islands,
      "core_fragments":len(fragments),"core_fragment_labels":fragments,
      "core_event_rows":len(core_rows),"event_rows_by_phase":phase_event_counts,
      "site_counts_by_phase":phase_site_counts,
      "locationID_counts_by_phase":phase_locationID_counts,
      "sites_with_multiple_locationIDs_in_any_phase":len({k for k,ph,ids in multi}),
      "multiple_locationID_site_phase_cases":[{"site_key":k,"phase":ph,"locationIDs":ids} for k,ph,ids in multi],
      "sampling_protocols":protocols,"habitats":habitats,
      "site_key_rule":c["site_identity"]["rule"],
      "phase_windows":c["official_response_independent_metadata"]["phase_windows"],
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,"taxon_occurrence_values_opened":0,
      "source_loss_effects_computed":0,"confirmatory_eligible":False,
      "next_gate":"freeze occurrence scientificName routing token and deterministic disjoint taxon partition; confirmatory event-by-taxon response remains sealed"
    }
    (out/"core_panel_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
