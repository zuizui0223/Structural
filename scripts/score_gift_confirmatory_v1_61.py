#!/usr/bin/env python3
"""Score the one-shot GIFT confirmatory response against frozen R3/C predictions."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_confirmatory_scoring_contract_v1_61.json"
MAGIC=b"STRUCTURAL_GIFT_PRED_V1\n"

class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_csv(p):
    with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def type7(values,p):
    xs=sorted(float(x) for x in values)
    if not xs or not 0<=p<=1:raise Stop("invalid quantile input")
    if len(xs)==1:return xs[0]
    h=(len(xs)-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
    if lo==hi:return xs[lo]
    f=h-lo
    return xs[lo]*(1-f)+xs[hi]*f

def logloss(p,y):
    p=float(p)
    if not 0.0<p<1.0 or y not in (0,1):raise Stop("invalid prediction/target")
    return -math.log(p) if y==1 else -math.log1p(-p)

def parse_predictions(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MAGIC):raise Stop("prediction binary magic drift")
    off=len(MAGIC)
    if len(raw)<off+8:raise Stop("prediction binary truncated")
    ne,ns=struct.unpack_from("<II",raw,off);off+=8
    expected=off+ne*ns*16
    if len(raw)!=expected:raise Stop("prediction binary byte-size drift")
    vals=list(struct.iter_unpack("<dd",memoryview(raw)[off:]))
    if len(vals)!=ne*ns:raise Stop("prediction cell count drift")
    return ne,ns,vals

def score(predictions,entity_order,universe,matrix,response_receipt,block_output,contract):
    if sha(predictions)!=contract["prediction_input"]["prediction_sha256"]:raise Stop("prediction SHA drift")
    if sha(entity_order)!=contract["prediction_input"]["entity_order_sha256"]:raise Stop("entity order SHA drift")
    if sha(universe)!=contract["focal_response"]["species_universe_sha256"]:raise Stop("species universe SHA drift")
    rr=json.loads(response_receipt.read_text())
    if rr.get("status")!="CONFIRMATORY_RESPONSE_CONSUMED_FOCAL_MATRIX_FROZEN":raise Stop("confirmatory response did not qualify")
    if sha(matrix)!=rr.get("matrix_sha256"):raise Stop("confirmatory matrix SHA drift")
    if rr.get("confirmatory_response_consumed") is not True:raise Stop("confirmatory response consumption not recorded")

    erows=load_csv(entity_order);urows=load_csv(universe);mrows=load_csv(matrix)
    if len(erows)!=404 or len(urows)!=224 or len(mrows)!=90496:raise Stop("confirmatory scoring dimensions drift")
    entity_ids=[str(r["entity_ID"]) for r in erows]
    species_ids=[str(r["work_ID"]) for r in urows]
    if len(set(entity_ids))!=404 or len(set(species_ids))!=224:raise Stop("duplicate frozen order key")
    eidx={v:i for i,v in enumerate(entity_ids)};sidx={v:i for i,v in enumerate(species_ids)}
    y=[-1]*(404*224)
    positives=0
    for r in mrows:
        eid=str(r["entity_ID"]);wid=str(r["work_ID"])
        if eid not in eidx or wid not in sidx:raise Stop("confirmatory matrix key outside frozen prediction surface")
        val=int(str(r["y"]).strip())
        if val not in (0,1):raise Stop("confirmatory target outside binary domain")
        k=eidx[eid]*224+sidx[wid]
        if y[k]!=-1:raise Stop("duplicate confirmatory matrix cell")
        y[k]=val;positives+=val
    if any(v<0 for v in y):raise Stop("incomplete confirmatory matrix")

    ne,ns,pairs=parse_predictions(predictions)
    if (ne,ns)!=(404,224):raise Stop("prediction shape drift")
    deltas=[]
    for (p3,pc),target in zip(pairs,y):
        if not (0<p3<1 and 0<pc<1):raise Stop("frozen probability outside open unit interval")
        deltas.append(logloss(pc,target)-logloss(p3,target))

    by_block=defaultdict(list);block_islands=defaultdict(set)
    for i,row in enumerate(erows):
        block=str(row["archip"]).strip()
        if not block:raise Stop("blank confirmatory archipelago")
        block_islands[block].add(entity_ids[i])
        start=i*224
        by_block[block].extend(deltas[start:start+224])
    if len(by_block)!=59:raise Stop("confirmatory block count drift")
    block_means={b:math.fsum(v)/len(v) for b,v in by_block.items()}
    point=math.fsum(block_means.values())/59.0

    rng=random.Random(int(contract["primary"]["bootstrap_seed"]))
    names=sorted(block_means)
    boot=[]
    for _ in range(int(contract["primary"]["bootstrap_replicates"])):
        sampled=[block_means[names[rng.randrange(len(names))]] for _ in range(len(names))]
        boot.append(math.fsum(sampled)/len(sampled))
    low=type7(boot,0.025);high=type7(boot,0.975)
    supported=point<0.0 and high<0.0

    block_output.parent.mkdir(parents=True,exist_ok=True)
    with block_output.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["archip","islands","targets","mean_C_minus_R3_logloss","mean_C_minus_R3_hex"])
        for b in names:
            m=block_means[b]
            w.writerow([b,len(block_islands[b]),len(by_block[b]),repr(m),float(m).hex()])

    result={
      "schema":"structural.gift_confirmatory_scoring_result.v1_61",
      "status":"FRESH_PLANT_CONFIRMATORY_PRIMARY_SCORED_ONCE",
      "candidate_id":contract["candidate_id"],
      "confirmatory_entities":404,
      "focal_species":224,
      "target_rows":90496,
      "target_positive":positives,
      "target_negative":90496-positives,
      "confirmatory_blocks":59,
      "primary_estimand":"equal-weight mean across confirmatory archipelago means of C-minus-R3 binary log loss",
      "point_estimate":point,
      "point_estimate_hex":float(point).hex(),
      "bootstrap_ci95_low":low,
      "bootstrap_ci95_low_hex":float(low).hex(),
      "bootstrap_ci95_high":high,
      "bootstrap_ci95_high_hex":float(high).hex(),
      "bootstrap_replicates":10000,
      "bootstrap_seed":20260930,
      "primary_supported":supported,
      "favourable_direction":"negative",
      "block_scores_sha256":sha(block_output),
      "prediction_sha256":sha(predictions),
      "confirmatory_matrix_sha256":sha(matrix),
      "confirmatory_response_consumed":True,
      "rerun_authorized":False,
      "counts_as_fresh_confirmatory_evidence":True,
      "fresh_system_denominator_contribution":1,
      "secondary_analysis_may_rescue_primary":False,
      "mechanism_claim_authorized":False
    }
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("predictions",type=Path);ap.add_argument("entity_order",type=Path)
    ap.add_argument("universe",type=Path);ap.add_argument("matrix",type=Path);ap.add_argument("response_receipt",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--block-output",type=Path,required=True);ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.gift_confirmatory_scoring_contract.v1_61":raise Stop("contract schema drift")
        out=score(a.predictions,a.entity_order,a.universe,a.matrix,a.response_receipt,a.block_output,c);code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={"schema":"structural.gift_confirmatory_scoring_result.v1_61","status":"TERMINAL_SCORING_FAILURE_AFTER_CONFIRMATORY_RESPONSE","reason":str(e),"confirmatory_response_consumed":True,"rerun_authorized":False,"counts_as_fresh_confirmatory_evidence":False,"fresh_system_denominator_contribution":0};code=2
    a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
