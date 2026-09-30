#!/usr/bin/env python3
"""Score one-shot nonconfirmatory mammal exploratory response vs frozen R3/C predictions."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_exploratory_scoring_contract_v1_74.json"
MAGIC=b"STRUCTURAL_MAMMAL_PRED_V1\n"

class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_csv(p:Path)->list[dict]:
    with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def type7(values,p):
    xs=sorted(float(x) for x in values)
    if not xs or not 0<=p<=1:raise Stop("invalid quantile input")
    if len(xs)==1:return xs[0]
    h=(len(xs)-1)*p
    lo=int(math.floor(h));hi=int(math.ceil(h))
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

def score(predictions:Path,entity_order:Path,universe:Path,matrix:Path,response_receipt:Path,
          block_output:Path,contract:dict):
    pinput=contract["prediction_input"]
    focal=contract["focal_response"]
    routing=contract["confirmatory_routing"]
    primary=contract["primary_exploratory_estimand"]

    if sha(predictions)!=pinput["prediction_sha256"]:raise Stop("prediction SHA drift")
    if sha(entity_order)!=pinput["entity_order_sha256"]:raise Stop("entity-order SHA drift")
    if sha(universe)!=focal["species_universe_sha256"]:raise Stop("species-universe SHA drift")

    rr=json.loads(response_receipt.read_text())
    if rr.get("status")!="NONCONFIRMATORY_EXPLORATORY_CONFIRMATORY_RESPONSE_CONSUMED_FOCAL_MATRIX_FROZEN":
        raise Stop("exploratory confirmatory response did not qualify")
    if rr.get("confirmatory_response_consumed") is not True:
        raise Stop("confirmatory response consumption not recorded")
    if rr.get("rerun_authorized") is not False:
        raise Stop("response receipt did not close rerun")
    if rr.get("confirmatory_nonfocal_values_decoded")!=0:
        raise Stop("nonfocal confirmatory occurrence was decoded")
    if rr.get("pilot_occurrence_values_decoded")!=0 or rr.get("excluded_occurrence_values_decoded")!=0:
        raise Stop("pilot/excluded occurrence was decoded during confirmatory execution")
    if sha(matrix)!=rr.get("matrix_sha256"):raise Stop("confirmatory matrix SHA drift")

    erows=load_csv(entity_order)
    urows=load_csv(universe)
    mrows=load_csv(matrix)
    if len(erows)!=4126 or len(urows)!=79 or len(mrows)!=4126:
        raise Stop("exploratory scoring dimensions drift")
    if tuple(erows[0].keys())!=("ID","block_id","bioregion"):
        raise Stop("entity-order schema drift")
    expected_labels=[f"S{j:05d}" for j in range(79)]
    if list(mrows[0].keys())!=["ID","block_id","bioregion"]+expected_labels:
        raise Stop("confirmatory matrix schema drift")
    if [str(r["ID"]) for r in mrows]!=[str(r["ID"]) for r in erows]:
        raise Stop("confirmatory matrix/entity order drift")
    for mr,er in zip(mrows,erows):
        if mr["block_id"]!=er["block_id"] or mr["bioregion"]!=er["bioregion"]:
            raise Stop("confirmatory routing metadata drift")
    if len({str(r["ID"]) for r in erows})!=4126:raise Stop("duplicate confirmatory ID")

    # Confirm exact focal order and source identity is still the frozen pilot universe.
    for j,r in enumerate(urows):
        if int(r["species_index"])!=j:raise Stop("focal species index drift")
        if str(r["species_name"]).strip()=="":raise Stop("blank focal species identity")

    ne,ns,pairs=parse_predictions(predictions)
    if (ne,ns)!=(4126,79):raise Stop("prediction shape drift")

    deltas=[]
    positives=0
    for i,row in enumerate(mrows):
        for j,label in enumerate(expected_labels):
            y=int(str(row[label]).strip())
            if y not in (0,1):raise Stop("confirmatory target outside binary domain")
            p3,pc=pairs[i*79+j]
            if not (0<p3<1 and 0<pc<1):raise Stop("frozen probability outside open unit interval")
            deltas.append(logloss(pc,y)-logloss(p3,y))
            positives+=y
    if len(deltas)!=focal["confirmatory_target_cells"]:raise Stop("target cell count drift")

    by_block=defaultdict(list)
    block_islands=defaultdict(set)
    block_region={}
    for i,row in enumerate(erows):
        block=str(row["block_id"]).strip()
        region=str(row["bioregion"]).strip()
        if not block or not region:raise Stop("blank confirmatory block/bioregion")
        if block in block_region and block_region[block]!=region:raise Stop("block spans multiple bioregions")
        block_region[block]=region
        block_islands[block].add(str(row["ID"]))
        start=i*79
        by_block[block].extend(deltas[start:start+79])

    if len(by_block)!=routing["blocks"]:raise Stop("confirmatory block count drift")
    block_means={b:math.fsum(v)/len(v) for b,v in by_block.items()}
    names=sorted(block_means)
    point=math.fsum(block_means[b] for b in names)/len(names)

    rng=random.Random(int(primary["bootstrap_seed"]))
    boot=[]
    reps=int(primary["bootstrap_replicates"])
    for _ in range(reps):
        sampled=[block_means[names[rng.randrange(len(names))]] for _ in range(len(names))]
        boot.append(math.fsum(sampled)/len(sampled))
    low=type7(boot,0.025);high=type7(boot,0.975)
    directional=point<0.0 and high<0.0

    block_output.parent.mkdir(parents=True,exist_ok=True)
    with block_output.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow([
          "block_id","bioregion","islands","targets",
          "mean_C_minus_R3_logloss","mean_C_minus_R3_hex"
        ])
        for b in names:
            m=block_means[b]
            w.writerow([b,block_region[b],len(block_islands[b]),len(by_block[b]),repr(m),float(m).hex()])

    return {
      "schema":"structural.global_mammals_exploratory_scoring_result.v1_74",
      "status":"NONCONFIRMATORY_EXPLORATORY_MAMMAL_PRIMARY_SCORED_ONCE",
      "candidate_id":contract["candidate_id"],
      "analysis_route":contract["analysis_route"],
      "confirmatory_entities":4126,
      "focal_species":79,
      "target_cells":325954,
      "target_positive":positives,
      "target_negative":325954-positives,
      "confirmatory_blocks":168,
      "primary_estimand":"equal-weight mean across frozen confirmatory spatial-block means of C-minus-R3 binary log loss",
      "point_estimate":point,
      "point_estimate_hex":float(point).hex(),
      "bootstrap_ci95_low":low,
      "bootstrap_ci95_low_hex":float(low).hex(),
      "bootstrap_ci95_high":high,
      "bootstrap_ci95_high_hex":float(high).hex(),
      "bootstrap_replicates":reps,
      "bootstrap_seed":int(primary["bootstrap_seed"]),
      "directional_support_exploratory":directional,
      "favourable_direction":"negative",
      "block_scores_sha256":sha(block_output),
      "prediction_sha256":sha(predictions),
      "confirmatory_matrix_sha256":sha(matrix),
      "confirmatory_response_consumed":True,
      "rerun_authorized":False,
      "counts_as_fresh_confirmatory_evidence":False,
      "counts_as_primary_confirmatory_evidence":False,
      "fresh_system_denominator_contribution":0,
      "terminal_v165_status_unchanged":True,
      "historical_318_overlap_exclusion_unchanged":True,
      "secondary_analysis_may_rescue_confirmatory_status":False,
      "mechanism_claim_authorized":False,
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("predictions",type=Path)
    ap.add_argument("entity_order",type=Path)
    ap.add_argument("universe",type=Path)
    ap.add_argument("matrix",type=Path)
    ap.add_argument("response_receipt",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--block-output",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_exploratory_scoring_contract.v1_74":
            raise Stop("contract schema drift")
        out=score(a.predictions,a.entity_order,a.universe,a.matrix,a.response_receipt,a.block_output,c)
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={
          "schema":"structural.global_mammals_exploratory_scoring_result.v1_74",
          "status":"TERMINAL_EXPLORATORY_SCORING_FAILURE_AFTER_CONFIRMATORY_RESPONSE",
          "reason":str(e),
          "confirmatory_response_consumed":True,
          "rerun_authorized":False,
          "counts_as_fresh_confirmatory_evidence":False,
          "counts_as_primary_confirmatory_evidence":False,
          "fresh_system_denominator_contribution":0,
          "terminal_v165_status_unchanged":True,
          "mechanism_claim_authorized":False
        }
        code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
