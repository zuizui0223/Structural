#!/usr/bin/env python3
"""Response-unopened audit of a publication-defined BALA pitfall-only repeated core."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_pitfall_core_audit_contract_v1_133.json"
FIELD_RE=re.compile(r"^([A-Za-z]+)-S0*([1-9][0-9]*)$")

class Stop(RuntimeError): pass

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def phase_for_year(y,windows):
    hits=[p for p,(lo,hi) in windows.items() if y is not None and int(lo)<=y<=int(hi)]
    return hits[0] if len(hits)==1 else None

def lineage_for(code,c):
    old=c["official_core_codes"]["BALA1_replaced_site_code"]
    new=c["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
    return "FAI-NFCF-REPLACED-LINEAGE" if code in (old,new) else code

def phase_allowed(code,phase,c):
    unchanged=set(c["official_core_codes"]["unchanged_29"])
    old=c["official_core_codes"]["BALA1_replaced_site_code"]
    new=c["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
    if code in unchanged:return phase in {"BALA1","BALA2","BALA3"}
    if code==old:return phase=="BALA1"
    if code==new:return phase in {"BALA2","BALA3"}
    return False

def parse_field(field):
    s=norm(field)
    m=FIELD_RE.fullmatch(s)
    if not m:return None
    return m.group(1).upper(),int(m.group(2))

def island_code(code):
    return code.split("-",1)[0] if "-" in code else code[:3]

def write(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.bala_pitfall_core_audit_contract.v1_133":
        raise Stop("contract schema drift")

    req=urllib.request.Request(c["source"]["dwca_url"],headers={"User-Agent":"Structural-BALA-pitfall-core-audit/1.0"})
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
    windows={k:tuple(v) for k,v in c["phase_windows"].items()}
    pit_label=c["event_semantics"]["pitfall_samplingProtocol"]
    beat_label=c["event_semantics"]["beating_samplingProtocol"]
    tur_family=set(c["event_semantics"]["turquin_prefix_family"])
    lo,hi=map(int,c["event_semantics"]["pitfall_position_range"])
    expected=int(c["event_semantics"]["expected_positions_per_site_phase"])
    beatmax=int(c["event_semantics"]["beating_expected_max_events_per_site_phase"])

    selected=[]
    for r in rows:
        y=year_from(r);ph=phase_for_year(y,windows);code=norm(r.get("locationID",""))
        if ph and phase_allowed(code,ph,c):
            rr=dict(r);rr["_phase"]=ph;rr["_year"]=y;rr["_code"]=code
            rr["_lineage"]=lineage_for(code,c);rr["_island"]=island_code(code)
            rr["_protocol"]=norm(r.get("samplingProtocol","")) or "<blank>"
            rr["_field"]=norm(r.get("fieldNumber","")) or "<blank>"
            selected.append(rr)

    by_site_phase=defaultdict(list)
    for r in selected:by_site_phase[(r["_lineage"],r["_phase"])].append(r)
    if len(by_site_phase)!=90:raise Stop(f"expected 90 conceptual site-phases, observed {len(by_site_phase)}")

    site_rows=[];anomalies=[];beating_excess=[]
    island_phase=defaultdict(lambda:{"pitfall_rows":0,"parseable_positions":0,"sites":0,"malformed_rows":0})
    all_even_ethy_odd_tur_mismatch=0
    all_odd_ethy_even_tur_mismatch=0
    total_pit=0;total_beat=0;total_malformed=0;total_duplicate_positions=0
    max_unique_positions=0

    for (lin,ph),rr in sorted(by_site_phase.items()):
        pit=[r for r in rr if r["_protocol"]==pit_label]
        beat=[r for r in rr if r["_protocol"]==beat_label]
        total_pit+=len(pit);total_beat+=len(beat)
        parsed=[];malformed=[]
        for r in pit:
            pf=parse_field(r["_field"])
            if pf is None:
                malformed.append(r);continue
            prefix,n=pf
            if not (lo<=n<=hi):
                malformed.append(r);continue
            family="ETHY" if prefix=="ETHY" else ("TUR" if prefix in tur_family else "OTHER")
            if family=="OTHER":
                malformed.append(r);continue
            parsed.append((r,prefix,family,n))

        pos_counts=Counter(n for _,_,_,n in parsed)
        unique_positions=len(pos_counts)
        max_unique_positions=max(max_unique_positions,unique_positions)
        duplicate_positions=sum(n-1 for n in pos_counts.values() if n>1)
        total_duplicate_positions+=duplicate_positions
        total_malformed+=len(malformed)

        even_ethy_odd_tur_mismatch=sum(
          not ((family=="ETHY" and n%2==0) or (family=="TUR" and n%2==1))
          for _,_,family,n in parsed)
        odd_ethy_even_tur_mismatch=sum(
          not ((family=="ETHY" and n%2==1) or (family=="TUR" and n%2==0))
          for _,_,family,n in parsed)
        all_even_ethy_odd_tur_mismatch+=even_ethy_odd_tur_mismatch
        all_odd_ethy_even_tur_mismatch+=odd_ethy_even_tur_mismatch

        for r in malformed:
            anomalies.append({
              "phase":ph,"lineage":lin,"locationID":r["_code"],"eventID":norm(r.get("eventID","")) or "<blank>",
              "year":r["_year"],"fieldNumber":r["_field"],"reason":"unparseable_or_nonstandard_pitfall_position"
            })

        excess=max(0,len(beat)-beatmax)
        if excess:
            pref=Counter()
            for r in beat:
                pf=parse_field(r["_field"])
                pref[pf[0] if pf else "<unparseable>"]+=1
            beating_excess.append({
              "phase":ph,"lineage":lin,"beating_event_rows":len(beat),
              "events_above_published_30":excess,
              "prefix_counts":";".join(f"{k}:{v}" for k,v in sorted(pref.items()))
            })

        island=rr[0]["_island"]
        key=(island,ph)
        island_phase[key]["pitfall_rows"]+=len(pit)
        island_phase[key]["parseable_positions"]+=unique_positions
        island_phase[key]["malformed_rows"]+=len(malformed)
        island_phase[key]["sites"]+=1

        site_rows.append({
          "phase":ph,"lineage":lin,"island":island,
          "pitfall_event_rows":len(pit),"parseable_pitfall_rows":len(parsed),
          "unique_parseable_positions":unique_positions,
          "duplicate_parseable_position_rows":duplicate_positions,
          "malformed_or_unmapped_pitfall_rows":len(malformed),
          "nominal_positions":expected,
          "event_row_effort_fraction":len(pit)/expected,
          "parseable_position_fraction":unique_positions/expected,
          "even_ETHY_odd_TUR_mismatches":even_ethy_odd_tur_mismatch,
          "odd_ETHY_even_TUR_mismatches":odd_ethy_even_tur_mismatch,
          "beating_event_rows":len(beat),"beating_events_above_30":excess
        })

    island_rows=[]
    phases={"BALA1","BALA2","BALA3"}
    islands=sorted({k[0] for k in island_phase})
    for island in islands:
        for ph in sorted(phases):
            x=island_phase[(island,ph)]
            nominal=x["sites"]*expected
            island_rows.append({
              "island":island,"phase":ph,"core_sites":x["sites"],
              "pitfall_event_rows":x["pitfall_rows"],
              "nominal_pitfall_positions":nominal,
              "event_row_effort_fraction":x["pitfall_rows"]/nominal if nominal else 0,
              "unique_parseable_positions_sum":x["parseable_positions"],
              "malformed_or_unmapped_pitfall_rows":x["malformed_rows"]
            })

    beat_excess_sum=sum(r["events_above_published_30"] for r in beating_excess)
    reported=int(c["publication_basis"]["foundational_core_events_reported"])
    selected_minus_reported=len(selected)-reported
    all_lineages={lin for lin,_ in by_site_phase}
    lineages_all_three=sum(all((lin,p) in by_site_phase for p in phases) for lin in all_lineages)
    islands_all_three=sum(all((isl,p) in island_phase and island_phase[(isl,p)]["sites"]>0 for p in phases) for isl in islands)

    # Alternating orientation is audited, not assumed. One orientation should dominate.
    preferred_orientation=(
      "ETHY_even_TUR_odd" if all_even_ethy_odd_tur_mismatch<all_odd_ethy_even_tur_mismatch
      else "ETHY_odd_TUR_even")
    preferred_mismatches=min(all_even_ethy_odd_tur_mismatch,all_odd_ethy_even_tur_mismatch)

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write(out/"pitfall_site_phase_effort.csv",site_rows,
      ["phase","lineage","island","pitfall_event_rows","parseable_pitfall_rows","unique_parseable_positions",
       "duplicate_parseable_position_rows","malformed_or_unmapped_pitfall_rows","nominal_positions",
       "event_row_effort_fraction","parseable_position_fraction","even_ETHY_odd_TUR_mismatches",
       "odd_ETHY_even_TUR_mismatches","beating_event_rows","beating_events_above_30"])
    write(out/"pitfall_island_phase_effort.csv",island_rows,
      ["island","phase","core_sites","pitfall_event_rows","nominal_pitfall_positions",
       "event_row_effort_fraction","unique_parseable_positions_sum","malformed_or_unmapped_pitfall_rows"])
    write(out/"pitfall_label_anomalies.csv",anomalies,
      ["phase","lineage","locationID","eventID","year","fieldNumber","reason"])
    write(out/"beating_excess_site_phase.csv",beating_excess,
      ["phase","lineage","beating_event_rows","events_above_published_30","prefix_counts"])

    min_site_effort=min(r["event_row_effort_fraction"] for r in site_rows)
    min_island_effort=min(r["event_row_effort_fraction"] for r in island_rows)
    result={
      "schema":"structural.bala_pitfall_core_audit_result.v1_133",
      "status":"BALA_PITFALL_ONLY_CORE_AUDIT_COMPLETE_RESPONSE_UNOPENED",
      "publication_defined_selected_event_rows":len(selected),
      "reported_foundational_core_events":reported,
      "selected_minus_reported":selected_minus_reported,
      "total_pitfall_event_rows":total_pit,
      "total_beating_event_rows":total_beat,
      "beating_excess_rows_above_30_per_site_phase":beat_excess_sum,
      "beating_excess_exactly_explains_selected_minus_reported":beat_excess_sum==selected_minus_reported,
      "site_phases":len(site_rows),
      "conceptual_lineages":len(all_lineages),
      "lineages_with_all_three_phases":lineages_all_three,
      "core_islands":len(islands),
      "islands_with_all_three_phases":islands_all_three,
      "minimum_site_phase_pitfall_event_effort_fraction":min_site_effort,
      "minimum_island_phase_pitfall_event_effort_fraction":min_island_effort,
      "pitfall_malformed_or_unmapped_event_rows":total_malformed,
      "pitfall_duplicate_parseable_position_rows":total_duplicate_positions,
      "maximum_unique_parseable_positions_in_site_phase":max_unique_positions,
      "alternating_preservative_orientation":preferred_orientation,
      "alternating_preservative_mismatches":preferred_mismatches,
      "pitfall_only_core_structurally_qualified_for_quality_threshold_gate":(
        lineages_all_three==30 and len(islands)==7 and islands_all_three==7 and
        max_unique_positions<=30 and min_island_effort>0
      ),
      "surveyed_zero_quality_threshold_selected":False,
      "final_taxon_partition_selected":False,
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,
      "taxon_occurrence_values_opened":0,
      "source_loss_effects_computed":0,
      "confirmatory_eligible":False,
      "next_gate":"freeze a response-independent pitfall effort/coverage rule for surveyed zeros and a stable taxon routing token before any Occurrence semantic access"
    }
    (out/"pitfall_core_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
