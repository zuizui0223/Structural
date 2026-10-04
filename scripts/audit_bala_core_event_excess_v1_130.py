#!/usr/bin/env python3
"""Audit response-independent Event metadata inside the 30-site BALA geography.

The script reports candidate metadata discriminators for the 538 extra Event rows.
It does not select a final 4,929-row core rule and never decodes Occurrence rows.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_core_event_excess_audit_contract_v1_130.json"
class Stop(RuntimeError): pass

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def site_key(r,dec=5):
    island=norm(r.get("island",""))
    try:
        lat=round(float(r.get("decimalLatitude","")),dec)
        lon=round(float(r.get("decimalLongitude","")),dec)
    except Exception:return ""
    return f"{island}|{lat:.{dec}f}|{lon:.{dec}f}" if island else ""

def phase_for_year(y,windows):
    hits=[p for p,(lo,hi) in windows.items() if y is not None and int(lo)<=y<=int(hi)]
    return hits[0] if len(hits)==1 else None

def write_counter(path,rows,fields):
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.bala_core_event_excess_audit_contract.v1_130":raise Stop("contract schema drift")

    req=urllib.request.Request(c["source"]["dwca_url"],headers={"User-Agent":"Structural-BALA-event-excess-audit/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:raw=resp.read()
    except Exception as e:raise Stop(f"DwC-A download failed: {e}") from e
    if sha_bytes(raw)!=c["source"]["archive_sha256"]:raise Stop("archive SHA drift")
    z=zipfile.ZipFile(io.BytesIO(raw))
    meta_name=next((x.filename for x in z.infolist() if Path(x.filename).name.lower()=="meta.xml"),None)
    if not meta_name:raise Stop("meta.xml missing")
    core,exts=parse_meta(read_member(z,meta_name))
    event_bytes=read_member(z,core["location"])
    if sha_bytes(event_bytes)!=c["source"]["event_core_sha256"]:raise Stop("Event core SHA drift")
    occ=[e for e in exts if e["rowType"].endswith("/Occurrence")]
    if len(occ)!=1:raise Stop("Occurrence extension resolution failed")
    occ_bytes=read_member(z,occ[0]["location"])
    if sha_bytes(occ_bytes)!=c["source"]["occurrence_extension_sha256_opaque_bytes"]:raise Stop("Occurrence opaque SHA drift")
    del occ_bytes

    rows,_=parse_event_core(event_bytes,core)
    windows={k:tuple(v) for k,v in c["repeated_geography_rule"]["phase_windows"].items()}
    by_phase=defaultdict(set)
    for r in rows:
        y=year_from(r);ph=phase_for_year(y,windows);k=site_key(r)
        if ph and k:by_phase[ph].add(k)
    common=set.intersection(*(by_phase[p] for p in ("BALA1","BALA2","BALA3")))
    if len(common)!=c["repeated_geography_rule"]["expected_site_intersection"]:
        raise Stop(f"repeated geography drift: {len(common)}")

    subset=[]
    for r in rows:
        y=year_from(r);ph=phase_for_year(y,windows);k=site_key(r)
        if ph and k in common:
            rr=dict(r);rr["_phase"]=ph;rr["_site_key"]=k;rr["_year"]=y;subset.append(rr)
    if len(subset)!=c["repeated_geography_rule"]["observed_event_rows_before_discriminator"]:
        raise Stop(f"pre-discriminator row drift: {len(subset)}")

    phase_year=Counter((r["_phase"],r["_year"]) for r in subset)
    habitat=Counter((r["_phase"],norm(r.get("habitat","")) or "<blank>") for r in subset)
    protocol=Counter((r["_phase"],norm(r.get("samplingProtocol","")) or "<blank>") for r in subset)
    fragment=Counter((r["_phase"],norm(r.get("locationRemarks","")) or "<blank>") for r in subset)
    locid=Counter((r["_phase"],norm(r.get("locationID","")) or "<blank>") for r in subset)
    fieldno=Counter((r["_phase"],norm(r.get("fieldNumber","")) or "<blank>") for r in subset)

    site_phase=[]
    aliases=[]
    for k in sorted(common):
        for ph in ("BALA1","BALA2","BALA3"):
            rr=[r for r in subset if r["_site_key"]==k and r["_phase"]==ph]
            ids=sorted({norm(r.get("locationID","")) for r in rr if norm(r.get("locationID",""))})
            prots=sorted({norm(r.get("samplingProtocol","")) for r in rr if norm(r.get("samplingProtocol",""))})
            habs=sorted({norm(r.get("habitat","")) for r in rr if norm(r.get("habitat",""))})
            years=sorted({r["_year"] for r in rr})
            site_phase.append({
              "site_key":k,"phase":ph,"event_rows":len(rr),"year_min":min(years),"year_max":max(years),
              "locationIDs":";".join(ids),"locationID_count":len(ids),
              "samplingProtocols":";".join(prots),"samplingProtocol_count":len(prots),
              "habitats":";".join(habs),"habitat_count":len(habs)
            })
            if len(ids)>1:
                aliases.append({"site_key":k,"phase":ph,"locationIDs":";".join(ids),"locationID_count":len(ids),"event_rows":len(rr)})

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write_counter(out/"phase_year_counts.csv",
      [{"phase":p,"year":y,"event_rows":n} for (p,y),n in sorted(phase_year.items())],
      ["phase","year","event_rows"])
    write_counter(out/"habitat_phase_counts.csv",
      [{"phase":p,"habitat":v,"event_rows":n} for (p,v),n in sorted(habitat.items())],
      ["phase","habitat","event_rows"])
    write_counter(out/"protocol_phase_counts.csv",
      [{"phase":p,"samplingProtocol":v,"event_rows":n} for (p,v),n in sorted(protocol.items())],
      ["phase","samplingProtocol","event_rows"])
    write_counter(out/"fragment_phase_counts.csv",
      [{"phase":p,"locationRemarks":v,"event_rows":n} for (p,v),n in sorted(fragment.items())],
      ["phase","locationRemarks","event_rows"])
    write_counter(out/"locationID_phase_counts.csv",
      [{"phase":p,"locationID":v,"event_rows":n} for (p,v),n in sorted(locid.items())],
      ["phase","locationID","event_rows"])
    write_counter(out/"fieldNumber_phase_counts.csv",
      [{"phase":p,"fieldNumber":v,"event_rows":n} for (p,v),n in sorted(fieldno.items())],
      ["phase","fieldNumber","event_rows"])
    write_counter(out/"site_phase_event_counts.csv",site_phase,
      ["site_key","phase","event_rows","year_min","year_max","locationIDs","locationID_count","samplingProtocols","samplingProtocol_count","habitats","habitat_count"])
    write_counter(out/"locationID_alias_cases.csv",aliases,
      ["site_key","phase","locationIDs","locationID_count","event_rows"])

    phase_totals={p:sum(r["_phase"]==p for r in subset) for p in ("BALA1","BALA2","BALA3")}
    unique_habitats=sorted({norm(r.get("habitat","")) for r in subset if norm(r.get("habitat",""))})
    unique_protocols=sorted({norm(r.get("samplingProtocol","")) for r in subset if norm(r.get("samplingProtocol",""))})
    unique_fragments=sorted({norm(r.get("locationRemarks","")) for r in subset if norm(r.get("locationRemarks",""))})
    result={
      "schema":"structural.bala_core_event_excess_audit_result.v1_130",
      "status":"BALA_EVENT_METADATA_EXCESS_AUDIT_COMPLETE_RESPONSE_UNOPENED",
      "repeated_coordinate_sites":len(common),
      "event_rows_before_discriminator":len(subset),
      "official_foundational_core_event_rows":c["repeated_geography_rule"]["official_foundational_core_event_rows"],
      "excess_event_rows":len(subset)-c["repeated_geography_rule"]["official_foundational_core_event_rows"],
      "event_rows_by_phase":phase_totals,
      "unique_habitats":unique_habitats,
      "unique_sampling_protocols":unique_protocols,
      "unique_fragment_labels":len(unique_fragments),
      "sites_with_multiple_locationIDs_in_phase":len({x["site_key"] for x in aliases}),
      "multiple_locationID_site_phase_cases":len(aliases),
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,
      "taxon_occurrence_values_opened":0,
      "source_loss_effects_computed":0,
      "final_core_rule_selected":False,
      "confirmatory_eligible":False,
      "next_gate":"use Event/EML semantics to freeze one non-outcome-based discriminator; do not optimize field combinations to hit 4929"
    }
    (out/"event_excess_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
