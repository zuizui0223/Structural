#!/usr/bin/env python3
"""Audit BALA publication-core Event rows against the published sampling grammar.

Occurrence-extension bytes are hash-verified and discarded without semantic
parsing. This audit does not select the final 4,929-event denominator.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_protocol_grammar_audit_contract_v1_132.json"

class Stop(RuntimeError): pass

def sha_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def phase_for_year(y,windows):
    hits=[p for p,(lo,hi) in windows.items() if y is not None and int(lo)<=y<=int(hi)]
    return hits[0] if len(hits)==1 else None

def lineage_for(code,c):
    old=c["official_core_codes"]["BALA1_replaced_site_code"]
    new=c["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
    if code in (old,new):
        return "FAI-NFCF-REPLACED-LINEAGE"
    return code

def phase_allowed(code,phase,c):
    unchanged=set(c["official_core_codes"]["unchanged_29"])
    old=c["official_core_codes"]["BALA1_replaced_site_code"]
    new=c["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
    if code in unchanged:
        return phase in {"BALA1","BALA2","BALA3"}
    if code==old:
        return phase=="BALA1"
    if code==new:
        return phase in {"BALA2","BALA3"}
    return False

FIELD_RE=re.compile(r"^([A-Za-z]+)-S0*([1-9][0-9]*)$")

def parse_field(field):
    s=norm(field)
    m=FIELD_RE.fullmatch(s)
    if not m:
        return None
    return m.group(1).upper(),int(m.group(2))

def write(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n")
        w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.bala_protocol_grammar_audit_contract.v1_132":
        raise Stop("contract schema drift")

    req=urllib.request.Request(c["source"]["dwca_url"],headers={"User-Agent":"Structural-BALA-protocol-grammar-audit/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:
            raw=resp.read()
    except Exception as e:
        raise Stop(f"DwC-A download failed: {e}") from e
    if sha_bytes(raw)!=c["source"]["archive_sha256"]:
        raise Stop("archive SHA drift")

    z=zipfile.ZipFile(io.BytesIO(raw))
    meta_name=next((x.filename for x in z.infolist() if Path(x.filename).name.lower()=="meta.xml"),None)
    if not meta_name:
        raise Stop("meta.xml missing")
    core,exts=parse_meta(read_member(z,meta_name))
    event_bytes=read_member(z,core["location"])
    if sha_bytes(event_bytes)!=c["source"]["event_core_sha256"]:
        raise Stop("Event core SHA drift")

    occ=[e for e in exts if e["rowType"].endswith("/Occurrence")]
    if len(occ)!=1:
        raise Stop("Occurrence extension resolution failed")
    occ_bytes=read_member(z,occ[0]["location"])
    if sha_bytes(occ_bytes)!=c["source"]["occurrence_extension_sha256_opaque_bytes"]:
        raise Stop("opaque Occurrence SHA drift")
    del occ_bytes

    rows,_=parse_event_core(event_bytes,core)
    windows={k:tuple(v) for k,v in c["phase_windows"].items()}
    pit_label=c["event_protocol_labels"]["pitfall"]
    beat_label=c["event_protocol_labels"]["beating"]
    pit_lo,pit_hi=map(int,c["field_number_grammar"]["pitfall_sample_number_range"])
    beat_lo,beat_hi=map(int,c["field_number_grammar"]["beating_sample_number_range"])

    selected=[]
    for r in rows:
        y=year_from(r)
        ph=phase_for_year(y,windows)
        code=norm(r.get("locationID",""))
        if ph and phase_allowed(code,ph,c):
            rr=dict(r)
            rr["_phase"]=ph
            rr["_year"]=y
            rr["_code"]=code
            rr["_lineage"]=lineage_for(code,c)
            rr["_protocol"]=norm(r.get("samplingProtocol","")) or "<blank>"
            rr["_field"]=norm(r.get("fieldNumber","")) or "<blank>"
            parsed=parse_field(rr["_field"])
            rr["_prefix"]=parsed[0] if parsed else None
            rr["_sample_no"]=parsed[1] if parsed else None
            selected.append(rr)

    invalid=[]
    strict_valid=[]
    for r in selected:
        reason=None
        if r["_protocol"] not in (pit_label,beat_label):
            reason="unknown_sampling_protocol"
        elif r["_prefix"] is None:
            reason="unparseable_fieldNumber"
        elif r["_protocol"]==pit_label and not (pit_lo<=r["_sample_no"]<=pit_hi):
            reason="pitfall_sample_number_out_of_range"
        elif r["_protocol"]==beat_label and not (beat_lo<=r["_sample_no"]<=beat_hi):
            reason="beating_sample_number_out_of_range"

        if reason:
            invalid.append({
                "phase":r["_phase"],"lineage":r["_lineage"],"locationID":r["_code"],
                "eventID":norm(r.get("eventID","")) or "<blank>",
                "year":r["_year"],"samplingProtocol":r["_protocol"],
                "fieldNumber":r["_field"],"reason":reason
            })
        else:
            strict_valid.append(r)

    # Exact standardized slot: phase+conceptual lineage+protocol+raw fieldNumber.
    slot_counts=Counter((r["_phase"],r["_lineage"],r["_protocol"],r["_field"]) for r in strict_valid)
    duplicates=[
      {"phase":ph,"lineage":lin,"samplingProtocol":prot,"fieldNumber":field,
       "event_rows":n,"duplicate_rows_above_one":n-1}
      for (ph,lin,prot,field),n in sorted(slot_counts.items()) if n>1
    ]

    # Prefix-level and site-phase summaries. These are diagnostics only: no aliases are merged.
    prefix_groups=defaultdict(list)
    site_phase=defaultdict(list)
    for r in strict_valid:
        prefix_groups[(r["_phase"],r["_lineage"],r["_protocol"],r["_prefix"])].append(r)
        site_phase[(r["_phase"],r["_lineage"])].append(r)

    prefix_rows=[]
    prefix_capacity_violations=0
    for (ph,lin,prot,prefix),rr in sorted(prefix_groups.items()):
        unique_numbers=sorted({r["_sample_no"] for r in rr})
        cap=pit_hi if prot==pit_label else beat_hi
        exceeds=len(unique_numbers)>cap
        if exceeds:
            prefix_capacity_violations+=1
        prefix_rows.append({
          "phase":ph,"lineage":lin,"samplingProtocol":prot,"prefix":prefix,
          "event_rows":len(rr),"unique_sample_numbers":len(unique_numbers),
          "sample_number_min":min(unique_numbers),"sample_number_max":max(unique_numbers),
          "protocol_cap":cap,"exceeds_protocol_cap":str(exceeds).lower()
        })

    site_rows=[]
    site_prefix_count_violations=0
    for (ph,lin),rr in sorted(site_phase.items()):
        pit=[r for r in rr if r["_protocol"]==pit_label]
        beat=[r for r in rr if r["_protocol"]==beat_label]
        pit_prefixes=sorted({r["_prefix"] for r in pit})
        beat_prefixes=sorted({r["_prefix"] for r in beat})
        pit_unique={(r["_prefix"],r["_sample_no"]) for r in pit}
        beat_unique={(r["_prefix"],r["_sample_no"]) for r in beat}
        pit_prefix_violation=len(pit_prefixes)>int(c["publication_basis"]["pitfall_protocol"]["preservative_classes"])
        beat_prefix_violation=len(beat_prefixes)>int(c["publication_basis"]["beating_protocol"]["tree_species_per_site_phase_max"])
        if pit_prefix_violation or beat_prefix_violation:
            site_prefix_count_violations+=1
        site_rows.append({
          "phase":ph,"lineage":lin,
          "pitfall_event_rows":len(pit),"pitfall_unique_slots":len(pit_unique),
          "pitfall_prefixes":";".join(pit_prefixes),"pitfall_prefix_count":len(pit_prefixes),
          "pitfall_prefix_count_violation":str(pit_prefix_violation).lower(),
          "beating_event_rows":len(beat),"beating_unique_slots":len(beat_unique),
          "beating_prefixes":";".join(beat_prefixes),"beating_prefix_count":len(beat_prefixes),
          "beating_prefix_count_violation":str(beat_prefix_violation).lower(),
          "strict_valid_event_rows":len(rr),
          "strict_valid_unique_slots":len({(r["_protocol"],r["_field"]) for r in rr})
        })

    strict_unique=len(slot_counts)
    duplicate_excess=sum(n-1 for n in slot_counts.values() if n>1)
    reported=int(c["publication_basis"]["core_events_reported"])
    invalid_reasons=Counter(r["reason"] for r in invalid)

    out=a.output_dir
    write(out/"protocol_invalid_rows.csv",invalid,
          ["phase","lineage","locationID","eventID","year","samplingProtocol","fieldNumber","reason"])
    write(out/"site_phase_protocol_summary.csv",site_rows,
          ["phase","lineage","pitfall_event_rows","pitfall_unique_slots","pitfall_prefixes","pitfall_prefix_count",
           "pitfall_prefix_count_violation","beating_event_rows","beating_unique_slots","beating_prefixes",
           "beating_prefix_count","beating_prefix_count_violation","strict_valid_event_rows","strict_valid_unique_slots"])
    write(out/"prefix_slot_summary.csv",prefix_rows,
          ["phase","lineage","samplingProtocol","prefix","event_rows","unique_sample_numbers",
           "sample_number_min","sample_number_max","protocol_cap","exceeds_protocol_cap"])
    write(out/"duplicate_protocol_slots.csv",duplicates,
          ["phase","lineage","samplingProtocol","fieldNumber","event_rows","duplicate_rows_above_one"])

    result={
      "schema":"structural.bala_protocol_grammar_audit_result.v1_132",
      "status":"BALA_PUBLICATION_PROTOCOL_GRAMMAR_AUDIT_COMPLETE_RESPONSE_UNOPENED",
      "publication_core_selected_event_rows":len(selected),
      "strict_grammar_valid_event_rows":len(strict_valid),
      "strict_grammar_invalid_event_rows":len(invalid),
      "invalid_reason_counts":dict(sorted(invalid_reasons.items())),
      "strict_grammar_unique_slots":strict_unique,
      "strict_grammar_duplicate_rows_above_unique_slots":duplicate_excess,
      "strict_unique_slots_minus_reported_4929":strict_unique-reported,
      "prefix_capacity_violation_groups":prefix_capacity_violations,
      "site_phase_prefix_count_violation_cases":site_prefix_count_violations,
      "final_core_rule_selected":False,
      "grammar_alone_exactly_recovers_reported_core":strict_unique==reported,
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,
      "taxon_occurrence_values_opened":0,
      "source_loss_effects_computed":0,
      "confirmatory_eligible":False,
      "next_gate":"interpret any remaining protocol-prefix/count violations using publication/EML/Event semantics only; freeze a final core rule in a new contract only if non-outcome justification is unique"
    }
    (out/"protocol_grammar_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
