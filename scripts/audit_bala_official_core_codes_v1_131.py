#!/usr/bin/env python3
"""Audit publication-defined BALA core codes and response-independent sample slots."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_official_core_code_audit_contract_v1_131.json"
SOURCE_CONTRACT=ROOT/"development/bala_core_event_excess_audit_contract_v1_130.json"
class Stop(RuntimeError): pass

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def phase_for_year(y,windows):
    hits=[p for p,(lo,hi) in windows.items() if y is not None and int(lo)<=y<=int(hi)]
    return hits[0] if len(hits)==1 else None

def prefix(field):
    s=norm(field)
    if not s:return "<blank>"
    m=re.match(r"^(.*?)-S\d+$",s,re.I)
    if m:return m.group(1)
    m=re.match(r"^([A-Za-z]+)",s)
    return m.group(1) if m else s

def lineage_for(code,contract):
    old=contract["official_core_codes"]["BALA1_replaced_site_code"]
    new=contract["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
    if code in (old,new):return "FAI-NFCF-REPLACED-LINEAGE"
    return code

def phase_allowed(code,phase,c):
    unchanged=set(c["official_core_codes"]["unchanged_29"])
    old=c["official_core_codes"]["BALA1_replaced_site_code"]
    new=c["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
    if code in unchanged:return phase in {"BALA1","BALA2","BALA3"}
    if code==old:return phase=="BALA1"
    if code==new:return phase in {"BALA2","BALA3"}
    return False

def write(path,rows,fields):
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    sc=json.loads(SOURCE_CONTRACT.read_text())
    if c.get("schema")!="structural.bala_official_core_code_audit_contract.v1_131":raise Stop("contract schema drift")

    # Contract itself must contain 31 publication-defined physical codes.
    all_codes=set(c["official_core_codes"]["unchanged_29"])
    all_codes.add(c["official_core_codes"]["BALA1_replaced_site_code"])
    all_codes.add(c["official_core_codes"]["BALA2_BALA3_replacement_site_code"])
    if len(all_codes)!=31:raise Stop(f"publication core-code count drift: {len(all_codes)}")

    req=urllib.request.Request(sc["source"]["dwca_url"],headers={"User-Agent":"Structural-BALA-official-core-audit/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:raw=resp.read()
    except Exception as e:raise Stop(f"DwC-A download failed: {e}") from e
    if sha_bytes(raw)!=sc["source"]["archive_sha256"]:raise Stop("archive SHA drift")
    z=zipfile.ZipFile(io.BytesIO(raw))
    meta_name=next((x.filename for x in z.infolist() if Path(x.filename).name.lower()=="meta.xml"),None)
    if not meta_name:raise Stop("meta.xml missing")
    core,exts=parse_meta(read_member(z,meta_name))
    event_bytes=read_member(z,core["location"])
    if sha_bytes(event_bytes)!=sc["source"]["event_core_sha256"]:raise Stop("Event core SHA drift")
    occ=[e for e in exts if e["rowType"].endswith("/Occurrence")]
    if len(occ)!=1:raise Stop("Occurrence extension resolution failed")
    occ_bytes=read_member(z,occ[0]["location"])
    if sha_bytes(occ_bytes)!=sc["source"]["occurrence_extension_sha256_opaque_bytes"]:raise Stop("opaque Occurrence SHA drift")
    del occ_bytes

    rows,_=parse_event_core(event_bytes,core)
    windows={k:tuple(v) for k,v in c["phase_windows"].items()}
    selected=[]
    for r in rows:
        y=year_from(r);ph=phase_for_year(y,windows);code=norm(r.get("locationID",""))
        if ph and phase_allowed(code,ph,c):
            rr=dict(r);rr["_phase"]=ph;rr["_year"]=y;rr["_code"]=code
            rr["_lineage"]=lineage_for(code,c);rr["_prefix"]=prefix(r.get("fieldNumber",""))
            rr["_protocol"]=norm(r.get("samplingProtocol","")) or "<blank>"
            rr["_field"]=norm(r.get("fieldNumber","")) or "<blank>"
            selected.append(rr)

    code_counts=Counter((r["_phase"],r["_code"]) for r in selected)
    code_rows=[{"phase":p,"locationID":code,"event_rows":n} for (p,code),n in sorted(code_counts.items())]

    by_lp=defaultdict(list)
    for r in selected:by_lp[(r["_lineage"],r["_phase"])].append(r)
    site_phase=[]
    slot_counts=Counter()
    for r in selected:
        slot=(r["_phase"],r["_lineage"],r["_protocol"],r["_field"])
        slot_counts[slot]+=1
    for (lin,ph),rr in sorted(by_lp.items()):
        slots={(r["_protocol"],r["_field"]) for r in rr}
        site_phase.append({
          "lineage":lin,"phase":ph,"event_rows":len(rr),"unique_sample_slots":len(slots),
          "duplicate_rows_above_unique_slots":len(rr)-len(slots),
          "year_min":min(r["_year"] for r in rr),"year_max":max(r["_year"] for r in rr),
          "protocols":";".join(sorted({r["_protocol"] for r in rr})),
          "field_prefixes":";".join(sorted({r["_prefix"] for r in rr}))
        })

    pref=Counter((r["_phase"],r["_prefix"],r["_protocol"]) for r in selected)
    pref_rows=[{"phase":p,"fieldNumber_prefix":f,"samplingProtocol":prot,"event_rows":n}
               for (p,f,prot),n in sorted(pref.items())]

    dup_rows=[]
    for (ph,lin,prot,field),n in sorted(slot_counts.items()):
        if n>1:
            dup_rows.append({
              "phase":ph,"lineage":lin,"samplingProtocol":prot,"fieldNumber":field,
              "event_rows":n,"duplicate_rows_above_one":n-1
            })

    phase_totals=Counter(r["_phase"] for r in selected)
    unique_slots=len(slot_counts)
    duplicate_excess=sum(n-1 for n in slot_counts.values() if n>1)
    reported=int(c["publication_semantics"]["foundational_core_events_reported"])

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write(out/"official_code_phase_counts.csv",code_rows,["phase","locationID","event_rows"])
    write(out/"official_core_site_phase_counts.csv",site_phase,
          ["lineage","phase","event_rows","unique_sample_slots","duplicate_rows_above_unique_slots","year_min","year_max","protocols","field_prefixes"])
    write(out/"official_core_fieldprefix_counts.csv",pref_rows,
          ["phase","fieldNumber_prefix","samplingProtocol","event_rows"])
    write(out/"duplicate_sample_slots.csv",dup_rows,
          ["phase","lineage","samplingProtocol","fieldNumber","event_rows","duplicate_rows_above_one"])

    result={
      "schema":"structural.bala_official_core_code_audit_result.v1_131",
      "status":"BALA_PUBLICATION_CORE_CODE_AUDIT_COMPLETE_RESPONSE_UNOPENED",
      "publication_core_physical_codes":len(all_codes),
      "conceptual_core_lineages":30,
      "selected_event_rows":len(selected),
      "selected_event_rows_by_phase":dict(phase_totals),
      "reported_foundational_core_event_rows":reported,
      "selected_minus_reported":len(selected)-reported,
      "unique_standardized_sample_slots":unique_slots,
      "duplicate_rows_above_unique_slots":duplicate_excess,
      "unique_slots_minus_reported":unique_slots-reported,
      "duplicate_sample_slot_count":len(dup_rows),
      "publication_noncore_alias_codes_present_in_selected":sorted(set(c["official_core_codes"]["explicitly_not_publication_core_codes"]) & {r["_code"] for r in selected}),
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,
      "taxon_occurrence_values_opened":0,
      "source_loss_effects_computed":0,
      "final_core_rule_selected":False,
      "confirmatory_eligible":False,
      "next_gate":"interpret residual sample-slot duplication using BALA protocol semantics; freeze a final core Event rule only if justified without occurrence outcomes"
    }
    (out/"official_core_code_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
