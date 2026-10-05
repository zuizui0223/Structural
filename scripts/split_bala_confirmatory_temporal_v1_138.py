#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_confirmatory_temporal_firewall_contract_v1_138.json"

class Stop(RuntimeError):
    pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def raw_body(line:bytes)->bytes:
    if line.endswith(b"\r\n"): return line[:-2]
    if line.endswith((b"\n",b"\r")): return line[:-1]
    return line

def load_phase_map(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h:
        rows=list(csv.DictReader(h))
    if not rows: raise Stop("pitfall event map empty")
    required={"phase","eventID"}
    if not required.issubset(rows[0]): raise Stop("pitfall event map schema drift")
    out={}
    counts=Counter()
    for r in rows:
        phase=str(r["phase"]).strip()
        if phase not in {"BALA1","BALA2","BALA3"}: raise Stop("unexpected phase")
        eid=str(r["eventID"]).strip()
        if not eid: raise Stop("blank eventID")
        key=eid.encode("utf-8")
        if key in out and out[key]!=phase: raise Stop("eventID phase conflict")
        out[key]=phase;counts[phase]+=1
    if set(counts)!={"BALA1","BALA2","BALA3"}: raise Stop("phase coverage drift")
    return out,counts

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("confirmatory_surface",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--preoutcome",type=Path,required=True)
    ap.add_argument("--t2",type=Path,required=True)
    ap.add_argument("--irrelevant",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.bala_confirmatory_temporal_firewall_contract.v1_138":
            raise Stop("contract schema drift")
        if sha(a.confirmatory_surface)!=c["input"]["confirmatory_surface_sha256"]:
            raise Stop("confirmatory surface SHA drift")
        if sha(a.pitfall_position_recovery)!=c["input"]["pitfall_position_recovery_sha256"]:
            raise Stop("pitfall recovery SHA drift")

        phase_map,event_counts=load_phase_map(a.pitfall_position_recovery)
        lines=a.confirmatory_surface.read_bytes().splitlines(keepends=True)
        if len(lines)<2: raise Stop("confirmatory surface empty")
        header=lines[0];data=lines[1:]
        if len(data)!=c["input"]["confirmatory_rows"]: raise Stop("confirmatory row-count drift")

        nfields=int(c["input"]["physical_field_count"]);coreidx=int(c["input"]["coreid_field_index"])
        pre=bytearray(header);t2=bytearray(header);irrelevant=bytearray(header)
        row_counts=Counter()
        matched=0
        for rn,line in enumerate(data,1):
            fields=raw_body(line).split(b"\t")
            if len(fields)!=nfields: raise Stop(f"physical field-count drift row {rn}")
            coreid=fields[coreidx].strip()
            phase=phase_map.get(coreid)
            if phase in {"BALA1","BALA2"}:
                pre.extend(line);row_counts[phase]+=1;matched+=1
            elif phase=="BALA3":
                t2.extend(line);row_counts[phase]+=1;matched+=1
            elif phase is None:
                irrelevant.extend(line);row_counts["NONPITFALL_OR_OUTSIDE_FROZEN_MAP"]+=1
            else:
                raise Stop("unreachable phase routing state")

        if sum(row_counts.values())!=len(data): raise Stop("row conservation failed")
        if matched != row_counts["BALA1"]+row_counts["BALA2"]+row_counts["BALA3"]:
            raise Stop("matched-row arithmetic failed")
        if row_counts["BALA1"]+row_counts["BALA2"]<=0 or row_counts["BALA3"]<=0:
            raise Stop("required temporal surface empty")

        for p,b in ((a.preoutcome,pre),(a.t2,t2),(a.irrelevant,irrelevant)):
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(bytes(b))

        result={
          "schema":"structural.bala_confirmatory_temporal_firewall_result.v1_138",
          "status":"BALA_CONFIRMATORY_TEMPORAL_BYTE_FIREWALL_COMPLETE",
          "input_confirmatory_rows":len(data),
          "pitfall_event_ids_in_safe_map":len(phase_map),
          "safe_event_rows_by_phase":dict(sorted(event_counts.items())),
          "routed_occurrence_rows_by_phase":dict(sorted(row_counts.items())),
          "preoutcome_t0_t1_rows":row_counts["BALA1"]+row_counts["BALA2"],
          "t2_rows":row_counts["BALA3"],
          "irrelevant_rows":row_counts["NONPITFALL_OR_OUTSIDE_FROZEN_MAP"],
          "rows_conserved":sum(row_counts.values())==len(data),
          "preoutcome_sha256":sha(a.preoutcome),
          "t2_sha256":sha(a.t2),
          "irrelevant_sha256":sha(a.irrelevant),
          "confirmatory_MF_tokens_opened":0,
          "confirmatory_quantity_values_opened":0,
          "confirmatory_taxonomy_values_opened":0,
          "confirmatory_t2_outcomes_opened":0,
          "source_leverage_values_computed":0,
          "candidate_minus_reference_effects_computed":0,
          "counts_as_empirical_support_or_non_support":False,
          "advance_authorized":True
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.bala_confirmatory_temporal_firewall_result.v1_138",
          "status":"STOP",
          "reason":str(e),
          "confirmatory_MF_tokens_opened":0,
          "confirmatory_quantity_values_opened":0,
          "confirmatory_taxonomy_values_opened":0,
          "confirmatory_t2_outcomes_opened":0,
          "source_leverage_values_computed":0,
          "candidate_minus_reference_effects_computed":0,
          "counts_as_empirical_support_or_non_support":False,
          "advance_authorized":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
