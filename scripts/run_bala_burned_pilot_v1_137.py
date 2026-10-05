#!/usr/bin/env python3
"""One-shot BALA burned-pilot estimability audit.

Only the already-routed pilot Occurrence surface is opened semantically.
The sealed confirmatory surface is not an input. The runner constructs the
frozen pitfall-only three-wave occupancy surface and audits estimability only.
It deliberately computes no leverage-outcome effect, score, coefficient,
correlation, odds ratio, or candidate-minus-reference contrast.
"""
from __future__ import annotations

import argparse,csv,hashlib,json,math
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_burned_pilot_contract_v1_137.json"
class Stop(RuntimeError): pass

PHASES=("BALA1","BALA2","BALA3")

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def clean(x)->str:
    return str(x or "").strip()

def lower(x)->str:
    return clean(x).casefold()

def read_csv(path:Path, delimiter=","):
    with path.open("r",encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h,delimiter=delimiter))

def parse_qty(raw:str)->float:
    s=clean(raw)
    if not s: raise Stop("blank organismQuantity in eligible pilot pitfall row")
    try:
        d=Decimal(s)
    except InvalidOperation as e:
        raise Stop(f"nonnumeric organismQuantity: {s!r}") from e
    if not d.is_finite() or d < 0:
        raise Stop(f"invalid organismQuantity: {s!r}")
    return float(d)

def load_manifest(path:Path,expected_sha:str):
    if sha(path)!=expected_sha: raise Stop("pilot token manifest SHA drift")
    rows=read_csv(path)
    required={"MF_token","bucket","occurrence_rows","salted_token_sha256"}
    if not rows or set(rows[0])!=required: raise Stop("pilot token manifest schema drift")
    tokens=[]
    for r in rows:
        token=clean(r["MF_token"])
        if not token or int(r["bucket"])!=0: raise Stop("pilot token manifest content drift")
        tokens.append(token)
    if len(tokens)!=142 or len(set(tokens))!=142: raise Stop("pilot token count drift")
    return tokens

def load_event_map(position_path:Path,island_quality_path:Path,c:dict,islands:set[str]):
    fi=c["frozen_inputs"]
    if sha(position_path)!=fi["pitfall_position_recovery_sha256"]: raise Stop("pitfall position SHA drift")
    if sha(island_quality_path)!=fi["pitfall_island_phase_quality_sha256"]: raise Stop("island quality SHA drift")
    q=read_csv(island_quality_path)
    if len(q)!=21: raise Stop("island-phase quality row-count drift")
    qpairs=set()
    for r in q:
        island=clean(r["island"]);phase=clean(r["phase"])
        if island not in islands or phase not in PHASES: raise Stop("island-phase quality identity drift")
        if lower(r["quality_pass"])!="true": raise Stop("frozen island-phase quality no longer passes")
        qpairs.add((island,phase))
    if len(qpairs)!=21: raise Stop("island-phase quality pair drift")

    rows=read_csv(position_path)
    event_map={}
    for r in rows:
        eid=clean(r["eventID"]);phase=clean(r["phase"]);lineage=clean(r["lineage"])
        if not eid or phase not in PHASES or not lineage: raise Stop("pitfall recovery identity drift")
        island=lineage.split("-",1)[0]
        if island not in islands: raise Stop("pitfall recovery island drift")
        v=(island,phase,lineage)
        if eid in event_map and event_map[eid]!=v: raise Stop("eventID maps to conflicting pitfall identities")
        event_map[eid]=v
    if not event_map: raise Stop("empty pitfall event map")
    return event_map

def load_graph(geometry_path:Path,edges_path:Path,c:dict):
    fi=c["frozen_inputs"]
    if sha(geometry_path)!=fi["geometry_sha256"]: raise Stop("geometry SHA drift")
    if sha(edges_path)!=fi["graph_edges_sha256"]: raise Stop("edge SHA drift")
    g=read_csv(geometry_path); e=read_csv(edges_path)
    islands=[clean(r["island"]) for r in g]
    if len(islands)!=7 or len(set(islands))!=7: raise Stop("geometry island count drift")
    idx={x:i for i,x in enumerate(islands)}
    n=len(islands);inf=float("inf")
    d=[[inf]*n for _ in range(n)]
    for i in range(n): d[i][i]=0.0
    lengths=[]
    for r in e:
        a=clean(r["from_island"]);b=clean(r["to_island"]);w=float(r["haversine_km"])
        if a not in idx or b not in idx or a==b or not math.isfinite(w) or w<=0: raise Stop("edge content drift")
        i,j=idx[a],idx[b];d[i][j]=d[j][i]=min(d[i][j],w);lengths.append(w)
    if len(e)!=6: raise Stop("Gabriel edge-count drift")
    for k in range(n):
        for i in range(n):
            for j in range(n):
                alt=d[i][k]+d[k][j]
                if alt<d[i][j]: d[i][j]=alt
    if any(not math.isfinite(d[i][j]) for i in range(n) for j in range(n)): raise Stop("graph disconnected")
    lam=float(fi["graph_lambda_km"])
    if not lam>0: raise Stop("invalid frozen lambda")
    dist={(a,b):d[idx[a]][idx[b]] for a in islands for b in islands}
    return islands,dist,lam

def eligible_reason(info:dict)->tuple[bool,str]:
    if info["pitfall_rows"]<=0: return False,"no_pitfall_rows"
    orders={x for x in info["order"] if x}
    if not orders: return False,"missing_order"
    if len(orders)!=1: return False,"inconsistent_order"
    order=next(iter(orders)).casefold()
    explicit_groups={x.casefold() for field in ("scientificName","class","order") for x in info[field] if x}
    if "acari" in explicit_groups or "collembola" in explicit_groups:
        return False,"metadata_excluded_group"
    if order=="diptera": return False,"excluded_diptera"
    if order=="hymenoptera":
        fams={x.casefold() for x in info["family"] if x}
        if not fams or fams!={"formicidae"}: return False,"excluded_nonformicid_hymenoptera"
    status={x.casefold() for x in info["establishmentMeans"] if x}
    if not status: return False,"missing_establishment_status"
    if not status.issubset({"native","endemic"}): return False,"non_native_or_indeterminate"
    return True,"eligible"

def kfun(target,source,dist,lam):
    if target==source: raise Stop("self anchor entered kernel")
    return math.exp(-dist[(target,source)]/lam)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_surface",type=Path)
    ap.add_argument("pilot_token_manifest",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("pitfall_island_quality",type=Path)
    ap.add_argument("geometry",type=Path)
    ap.add_argument("edges",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--eligibility",type=Path,required=True)
    ap.add_argument("--presence",type=Path,required=True)
    ap.add_argument("--exposure",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()

    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.bala_burned_pilot_contract.v1_137": raise Stop("contract schema drift")
        if sha(a.pilot_surface)!=c["frozen_inputs"]["pilot_surface_sha256"]: raise Stop("pilot surface SHA drift")
        tokens=load_manifest(a.pilot_token_manifest,c["frozen_inputs"]["pilot_token_manifest_sha256"])
        islands,dist,lam=load_graph(a.geometry,a.edges,c)
        event_map=load_event_map(a.pitfall_position_recovery,a.pitfall_island_quality,c,set(islands))

        with a.pilot_surface.open("r",encoding="utf-8",newline="") as h:
            reader=csv.DictReader(h,delimiter="\t")
            required={
              "organismQuantity","organismQuantityType","establishmentMeans","eventID",
              "identificationRemarks","scientificName","class","order","family","taxonRank"
            }
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)): raise Stop("pilot surface required fields missing")
            info={t:{
              "pitfall_rows":0,"all_rows":0,
              "establishmentMeans":set(),"scientificName":set(),"class":set(),"order":set(),"family":set(),"taxonRank":set(),
              "positive":set()
            } for t in tokens}
            seen_tokens=set()
            pilot_rows=pitfall_rows=0
            for r in reader:
                pilot_rows+=1
                token=clean(r["identificationRemarks"])
                if token not in info: raise Stop("pilot surface contains token outside frozen pilot manifest")
                seen_tokens.add(token);d=info[token];d["all_rows"]+=1
                for field in ("establishmentMeans","scientificName","class","order","family","taxonRank"):
                    v=clean(r[field])
                    if v:d[field].add(v)
                eid=clean(r["eventID"])
                if eid not in event_map:
                    continue
                pitfall_rows+=1;d["pitfall_rows"]+=1
                if lower(r["organismQuantityType"])!="individuals": raise Stop("pilot pitfall organismQuantityType drift")
                qty=parse_qty(r["organismQuantity"])
                if qty>0:
                    island,phase,_=event_map[eid]
                    d["positive"].add((island,phase))
        if pilot_rows!=20958: raise Stop("pilot row-count drift")
        if seen_tokens!=set(tokens): raise Stop("pilot token support drift")

        eligibility_rows=[];eligible=[]
        for token in tokens:
            d=info[token];ok,reason=eligible_reason(d)
            if ok: eligible.append(token)
            eligibility_rows.append({
              "MF_token":token,"eligible":str(ok).lower(),"reason":reason,
              "pilot_rows":d["all_rows"],"pitfall_rows":d["pitfall_rows"],
              "order":"|".join(sorted(d["order"])),"family":"|".join(sorted(d["family"])),
              "establishmentMeans":"|".join(sorted(d["establishmentMeans"])),
              "scientificName_count":len(d["scientificName"]),"taxonRank":"|".join(sorted(d["taxonRank"]))
            })

        presence={}
        presence_rows=[]
        for token in eligible:
            presence[token]={}
            pos=info[token]["positive"]
            for island in islands:
                vals={phase:int((island,phase) in pos) for phase in PHASES}
                presence[token][island]=vals
                presence_rows.append({"MF_token":token,"island":island,**vals})

        exposure_rows=[];outcome_counts={0:0,1:0};loss_taxa=set();persist_taxa=set()
        t0_ge2=0;one_loss_taxa=0;lost_islands=set();target_islands=set();E_values=[]
        by_source_count=defaultdict(list)
        one_loss_taxon_tokens=[]
        for token in eligible:
            t0={i for i in islands if presence[token][i]["BALA1"]==1}
            t1={i for i in islands if presence[token][i]["BALA2"]==1}
            t2={i for i in islands if presence[token][i]["BALA3"]==1}
            if len(t0)<2: continue
            t0_ge2+=1
            lost=t0-t1
            if len(lost)!=1: continue
            one_loss_taxa+=1;one_loss_taxon_tokens.append(token)
            lost_source=next(iter(lost));lost_islands.add(lost_source)
            # Event-level lost-source leverage share across all island target geometries.
            masses={}
            for src in t0:
                masses[src]=sum(kfun(target,src,dist,lam) for target in islands if target!=src)
            total_mass=sum(masses.values())
            if not total_mass>0: raise Stop("nonpositive total source pressure mass")
            q_loss=masses[lost_source]/total_mass
            for target in sorted(t1):
                if target==lost_source: raise Stop("lost source entered t1 survivor target set")
                denom_sources=t0-{target}
                if not denom_sources: continue
                den=sum(kfun(target,src,dist,lam) for src in denom_sources)
                num=sum(kfun(target,src,dist,lam) for src in lost if src!=target)
                if not den>0: raise Stop("nonpositive target baseline source pressure")
                E=num/den
                if E<0 or E>1+1e-12 or not math.isfinite(E): raise Stop("lost-access fraction outside [0,1]")
                E=min(1.0,max(0.0,E))
                target_islands.add(target);E_values.append(E);by_source_count[len(t0)].append(E)
                y=0 if target in t2 else 1
                outcome_counts[y]+=1
                if y==1: loss_taxa.add(token)
                else: persist_taxa.add(token)
                exposure_rows.append({
                  "MF_token":token,"t0_source_count":len(t0),"lost_source":lost_source,
                  "target_island":target,"E_i":format(E,".17g"),"Q_loss":format(q_loss,".17g")
                })

        thresholds=c["estimability_gate"]
        distinct_E=len({round(x,6) for x in E_values})
        identifiable_strata=[]
        for k,vals in sorted(by_source_count.items()):
            if len(vals)>=5 and len({round(x,6) for x in vals})>=3:
                identifiable_strata.append(k)

        metrics={
          "eligible_pilot_taxa":len(eligible),
          "pilot_taxa_with_at_least_two_t0_sources":t0_ge2,
          "exactly_one_loss_taxa":one_loss_taxa,
          "t1_surviving_target_rows":len(exposure_rows),
          "t2_contraction_rows":outcome_counts[1],
          "t2_persistence_rows":outcome_counts[0],
          "taxa_with_any_t2_contraction":len(loss_taxa),
          "taxa_with_any_t2_persistence":len(persist_taxa),
          "distinct_lost_source_islands":len(lost_islands),
          "distinct_target_islands":len(target_islands),
          "distinct_E_i_values_rounded_1e_6":distinct_E,
          "leverage_identifiable_source_count_strata":identifiable_strata
        }
        checks={
          "eligible_pilot_taxa":metrics["eligible_pilot_taxa"]>=thresholds["minimum_eligible_pilot_taxa"],
          "pilot_taxa_with_at_least_two_t0_sources":metrics["pilot_taxa_with_at_least_two_t0_sources"]>=thresholds["minimum_pilot_taxa_with_at_least_two_t0_sources"],
          "exactly_one_loss_taxa":metrics["exactly_one_loss_taxa"]>=thresholds["minimum_exactly_one_loss_taxa"],
          "t1_surviving_target_rows":metrics["t1_surviving_target_rows"]>=thresholds["minimum_t1_surviving_target_rows"],
          "t2_contraction_rows":metrics["t2_contraction_rows"]>=thresholds["minimum_t2_contraction_rows"],
          "t2_persistence_rows":metrics["t2_persistence_rows"]>=thresholds["minimum_t2_persistence_rows"],
          "taxa_with_any_t2_contraction":metrics["taxa_with_any_t2_contraction"]>=thresholds["minimum_taxa_with_any_t2_contraction"],
          "taxa_with_any_t2_persistence":metrics["taxa_with_any_t2_persistence"]>=thresholds["minimum_taxa_with_any_t2_persistence"],
          "distinct_lost_source_islands":metrics["distinct_lost_source_islands"]>=thresholds["minimum_distinct_lost_source_islands"],
          "distinct_target_islands":metrics["distinct_target_islands"]>=thresholds["minimum_distinct_target_islands"],
          "distinct_E_i_values":metrics["distinct_E_i_values_rounded_1e_6"]>=thresholds["minimum_distinct_E_i_values_rounded_1e_6"],
          "leverage_identifiability_beyond_source_count":len(identifiable_strata)>=1
        }
        gate_passed=all(checks.values())

        a.eligibility.parent.mkdir(parents=True,exist_ok=True)
        with a.eligibility.open("w",encoding="utf-8",newline="") as h:
            fields=list(eligibility_rows[0].keys()) if eligibility_rows else []
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(eligibility_rows)
        with a.presence.open("w",encoding="utf-8",newline="") as h:
            fields=["MF_token","island","BALA1","BALA2","BALA3"]
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(presence_rows)
        with a.exposure.open("w",encoding="utf-8",newline="") as h:
            fields=["MF_token","t0_source_count","lost_source","target_island","E_i","Q_loss"]
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(exposure_rows)

        result={
          "schema":"structural.bala_burned_pilot_result.v1_137",
          "status":"BALA_BURNED_PILOT_ESTIMABILITY_PASS" if gate_passed else "BALA_BURNED_PILOT_ESTIMABILITY_STOP",
          "pilot_rows_semantically_opened":pilot_rows,
          "pilot_distinct_routed_taxa":len(tokens),
          "pilot_pitfall_rows_used":pitfall_rows,
          "metrics":metrics,
          "checks":checks,
          "gate_passed":gate_passed,
          "effect_estimate_computed":False,
          "candidate_minus_reference_score_computed":False,
          "leverage_outcome_association_computed":False,
          "confirmatory_surface_semantically_opened":False,
          "confirmatory_taxon_identity_opened":False,
          "confirmatory_t2_opened":False,
          "source_loss_effects_computed":0,
          "eligibility_sha256":sha(a.eligibility),
          "presence_sha256":sha(a.presence),
          "exposure_sha256":sha(a.exposure),
          "next_action":"freeze confirmatory taxonomy/phase firewall and full R2/C scoring protocol" if gate_passed else "STOP BALA primary source-loss route without threshold relaxation"
        }
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.bala_burned_pilot_result.v1_137","status":"STOP","reason":str(e),
          "effect_estimate_computed":False,"candidate_minus_reference_score_computed":False,
          "leverage_outcome_association_computed":False,"confirmatory_surface_semantically_opened":False,
          "confirmatory_t2_opened":False,"source_loss_effects_computed":0
        };code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
