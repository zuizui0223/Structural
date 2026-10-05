#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_confirmatory_preaccess_contract_v1_138.json"
class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def load_event_map(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    out={}
    for r in rows:
        eid=str(r["eventID"]).strip();phase=str(r["phase"]).strip()
        if not eid or phase not in {"BALA1","BALA2","BALA3"}: raise Stop("pitfall event map drift")
        if eid in out and out[eid]!=phase: raise Stop("eventID phase conflict")
        out[eid]=phase
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sealed_surface",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--t0t1-output",type=Path,required=True)
    ap.add_argument("--t2-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.bala_confirmatory_preaccess_contract.v1_138": raise Stop("contract schema drift")
        if sha(a.sealed_surface)!=c["confirmatory_input"]["sealed_surface_sha256"]: raise Stop("confirmatory sealed surface SHA drift")
        emap=load_event_map(a.pitfall_position_recovery)
        raw=a.sealed_surface.read_bytes();lines=raw.splitlines(keepends=True)
        if len(lines)<2: raise Stop("sealed confirmatory surface empty")
        header=lines[0];data=lines[1:]
        if len(data)!=c["confirmatory_input"]["confirmatory_occurrence_rows"]: raise Stop("confirmatory row-count drift")
        t01=bytearray(header);t2=bytearray(header)
        t01_rows=t2_rows=nonpitfall=0
        for rn,line in enumerate(data,1):
            body=line[:-2] if line.endswith(b"\r\n") else line[:-1] if line.endswith((b"\n",b"\r")) else line
            fields=body.split(b"\t")
            if len(fields)!=32: raise Stop(f"physical field-count drift row {rn}")
            try: coreid=fields[0].decode("utf-8").strip()
            except UnicodeDecodeError as e: raise Stop("coreid UTF-8 decode failed") from e
            phase=emap.get(coreid)
            if phase in {"BALA1","BALA2"}:
                t01.extend(line);t01_rows+=1
            elif phase=="BALA3":
                t2.extend(line);t2_rows+=1
            else:
                nonpitfall+=1
        if t01_rows+t2_rows+nonpitfall!=len(data): raise Stop("phase routing row conservation failed")
        a.t0t1_output.parent.mkdir(parents=True,exist_ok=True)
        a.t0t1_output.write_bytes(bytes(t01));a.t2_output.write_bytes(bytes(t2))
        result={
          "schema":"structural.bala_confirmatory_phase_routing_result.v1_138",
          "status":"BALA_CONFIRMATORY_PHASE_BYTE_ROUTING_COMPLETE",
          "input_rows":len(data),"t0_t1_pitfall_rows":t01_rows,"t2_pitfall_rows":t2_rows,
          "nonpitfall_rows_ignored":nonpitfall,
          "t0_t1_surface_sha256":sha(a.t0t1_output),"t2_surface_sha256":sha(a.t2_output),
          "decoded_fields":["coreid"],
          "MF_tokens_decoded":0,"organismQuantity_values_decoded":0,"taxonomy_values_decoded":0,
          "t2_semantically_opened":False,"source_loss_effects_computed":0
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={"schema":"structural.bala_confirmatory_phase_routing_result.v1_138","status":"STOP","reason":str(e),
          "MF_tokens_decoded":0,"organismQuantity_values_decoded":0,"taxonomy_values_decoded":0,
          "t2_semantically_opened":False,"source_loss_effects_computed":0};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__": raise SystemExit(main())
