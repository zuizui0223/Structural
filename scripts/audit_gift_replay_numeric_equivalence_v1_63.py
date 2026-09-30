#!/usr/bin/env python3
"""Audit numerical equivalence of original vs replay GIFT predictions without response."""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from pathlib import Path

MAGIC=b"STRUCTURAL_GIFT_PRED_V1\n"

class Stop(RuntimeError): pass

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def parse_pred(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MAGIC): raise Stop("prediction magic drift")
    off=len(MAGIC)
    if len(raw)<off+8: raise Stop("prediction header truncated")
    ne,ns=struct.unpack_from("<II",raw,off);off+=8
    expected=off+ne*ns*16
    if len(raw)!=expected: raise Stop("prediction byte length drift")
    vals=[]
    for i in range(ne*ns):
        a,b=struct.unpack_from("<dd",raw,off+i*16)
        if not (math.isfinite(a) and math.isfinite(b) and 0<a<1 and 0<b<1):
            raise Stop("prediction outside finite open probability interval")
        vals.append((a,b))
    return ne,ns,vals

def hexfloat(s):
    return float.fromhex(s)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("original_predictions",type=Path)
    ap.add_argument("replay_predictions",type=Path)
    ap.add_argument("original_entity_order",type=Path)
    ap.add_argument("replay_entity_order",type=Path)
    ap.add_argument("original_receipt",type=Path)
    ap.add_argument("replay_receipt",type=Path)
    ap.add_argument("--tolerance",type=float,default=1e-12)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    try:
        if a.tolerance!=1e-12: raise Stop("tolerance drift")
        if a.original_entity_order.read_bytes()!=a.replay_entity_order.read_bytes():
            raise Stop("entity-order bytes differ")
        o=json.loads(a.original_receipt.read_text()); r=json.loads(a.replay_receipt.read_text())
        if o["source_standardization"]!=r["source_standardization"]:
            raise Stop("source-standardization hex values differ")
        model_stats={}
        max_coef=0.0
        for name in ("R0","R1","R2","R3","C"):
            om=o["models"][name]; rm=r["models"][name]
            if om["columns"]!=rm["columns"]: raise Stop(f"{name} model columns differ")
            if om["iterations"]!=rm["iterations"]: raise Stop(f"{name} iteration count differs")
            if len(om["coefficients_hex"])!=len(rm["coefficients_hex"]): raise Stop(f"{name} coefficient count differs")
            diffs=[abs(hexfloat(x)-hexfloat(y)) for x,y in zip(om["coefficients_hex"],rm["coefficients_hex"])]
            m=max(diffs,default=0.0); max_coef=max(max_coef,m)
            model_stats[name]={"max_abs_coefficient_difference":m,"mean_abs_coefficient_difference":sum(diffs)/len(diffs)}
        if max_coef>a.tolerance: raise Stop("coefficient numerical-equivalence tolerance exceeded")
        one,ons,ov=parse_pred(a.original_predictions); rne,rns,rv=parse_pred(a.replay_predictions)
        if (one,ons)!=(rne,rns): raise Stop("prediction shape differs")
        max_p=0.0;sum_p=0.0;n=0
        max_r3=0.0;max_c=0.0
        for (or3,oc),(rr3,rc) in zip(ov,rv):
            dr3=abs(or3-rr3);dc=abs(oc-rc)
            max_r3=max(max_r3,dr3);max_c=max(max_c,dc);max_p=max(max_p,dr3,dc)
            sum_p+=dr3+dc;n+=2
        if max_p>a.tolerance: raise Stop("prediction numerical-equivalence tolerance exceeded")
        out={
          "schema":"structural.gift_replay_numeric_equivalence_result.v1_63",
          "status":"NUMERIC_REPLAY_EQUIVALENT_RESPONSE_INDEPENDENTLY",
          "absolute_tolerance":a.tolerance,
          "original_prediction_sha256":sha(a.original_predictions),
          "replay_prediction_sha256":sha(a.replay_predictions),
          "entity_order_sha256":sha(a.original_entity_order),
          "prediction_shape":[one,ons,2],
          "max_abs_probability_difference":max_p,
          "mean_abs_probability_difference":sum_p/n,
          "max_abs_R3_probability_difference":max_r3,
          "max_abs_C_probability_difference":max_c,
          "max_abs_coefficient_difference":max_coef,
          "models":model_stats,
          "source_standardization_exact":True,
          "entity_order_byte_identical":True,
          "confirmatory_target_values_used":False,
          "confirmatory_species_composition_opened":False,
          "counts_as_empirical_evidence":False,
          "confirmatory_response_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={"schema":"structural.gift_replay_numeric_equivalence_result.v1_63","status":"STOP_NUMERIC_REPLAY_NOT_EQUIVALENT","reason":str(e),"confirmatory_target_values_used":False,"confirmatory_species_composition_opened":False,"counts_as_empirical_evidence":False,"confirmatory_response_authorized":False};code=2
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
