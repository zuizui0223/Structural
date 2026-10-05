#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,decimal,hashlib,json,math,heapq
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL=ROOT/"development/bala_preoutcome_feature_protocol_v1_140.json"

class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def dec(raw:bytes)->str:
    try: return raw.decode("utf-8").strip()
    except UnicodeDecodeError as e: raise Stop("UTF-8 decode failed") from e

def qnum(s:str)->decimal.Decimal:
    try: x=decimal.Decimal(s)
    except decimal.InvalidOperation as e: raise Stop(f"nonnumeric organismQuantity: {s!r}") from e
    if not x.is_finite() or x<0: raise Stop(f"invalid organismQuantity: {s!r}")
    return x

def unique_nonblank(vals):
    return sorted({str(x).strip() for x in vals if str(x).strip()})

def eligible_taxon(tax):
    sci=unique_nonblank(tax["scientificName"]);order=unique_nonblank(tax["order"])
    family=unique_nonblank(tax["family"]);rank=unique_nonblank(tax["taxonRank"])
    if any(len(x)>1 for x in (sci,order,family,rank)):
        return False,"taxonomy_conflict",sci,order,family,rank
    if len(order)!=1:
        return False,"order_missing",sci,order,family,rank
    o=order[0].casefold();f=family[0].casefold() if len(family)==1 else ""
    mentions=" ".join(sci+order+family+rank).casefold()
    if "acari" in mentions or "collembola" in mentions:
        return False,"metadata_excluded_group",sci,order,family,rank
    if o=="diptera":
        return False,"diptera_not_morphospecies_resolved",sci,order,family,rank
    if o=="hymenoptera" and f!="formicidae":
        return False,"non_formicidae_hymenoptera_not_morphospecies_resolved",sci,order,family,rank
    return True,"eligible",sci,order,family,rank

def hav(lat1,lon1,lat2,lon2):
    r=6371.0088
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1.0,math.sqrt(a)))

def load_geometry(path):
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    out={}
    for r in rows:
        out[r["island"]]=(float(r["latitude"]),float(r["longitude"]))
    return out

def load_edges(path):
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    return [(r["from_island"],r["to_island"],float(r["haversine_km"])) for r in rows]

def all_pairs_shortest(islands,edges):
    adj={i:[] for i in islands}
    for a,b,d in edges:
        adj[a].append((b,d));adj[b].append((a,d))
    out={}
    for src in islands:
        dist={i:math.inf for i in islands};dist[src]=0.0
        q=[(0.0,src)]
        while q:
            d,u=heapq.heappop(q)
            if d!=dist[u]: continue
            for v,w in adj[u]:
                nd=d+w
                if nd<dist[v]:
                    dist[v]=nd;heapq.heappush(q,(nd,v))
        if not all(math.isfinite(dist[i]) for i in islands): raise Stop("graph disconnected")
        out[src]=dist
    return out

def load_event_map(path):
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    out={}
    for r in rows:
        ph=str(r["phase"]).strip()
        if ph not in {"BALA1","BALA2","BALA3"}: raise Stop("unexpected phase")
        eid=str(r["eventID"]).strip()
        island=str(r["lineage"])[:3]
        out[eid]=(ph,island)
    return out

def load_t2_effort(path):
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    out={}
    for r in rows:
        if str(r["phase"])=="BALA3":
            out[str(r["island"])]=int(r["unique_recovered_positions"])
    return out

def pop_mean_sd(xs):
    if not xs: raise Stop("empty vector")
    m=math.fsum(xs)/len(xs)
    sd=math.sqrt(math.fsum((x-m)**2 for x in xs)/len(xs))
    return m,sd

def effective_source_number(source_set,islands,gdist,lam):
    if not source_set: return 0.0,{}
    masses={}
    for s in source_set:
        masses[s]=math.fsum(math.exp(-gdist[i][s]/lam) for i in islands if i!=s)
    total=math.fsum(masses.values())
    if not total>0: raise Stop("nonpositive source pressure mass")
    shares={s:masses[s]/total for s in source_set}
    neff=1.0/math.fsum(q*q for q in shares.values())
    return neff,shares

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("preoutcome_surface",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("pitfall_island_phase_quality",type=Path)
    ap.add_argument("island_geometry",type=Path)
    ap.add_argument("graph_edges",type=Path)
    ap.add_argument("--expected-preoutcome-sha",required=True)
    ap.add_argument("--protocol",type=Path,default=DEFAULT_PROTOCOL)
    ap.add_argument("--taxon-summary",type=Path,required=True)
    ap.add_argument("--features",type=Path,required=True)
    ap.add_argument("--fold-manifest",type=Path,required=True)
    ap.add_argument("--fold-standardization",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()

    try:
        c=json.loads(a.protocol.read_text())
        if c["schema"]!="structural.bala_preoutcome_feature_protocol.v1_140": raise Stop("protocol schema drift")
        if sha(a.preoutcome_surface)!=a.expected_preoutcome_sha: raise Stop("preoutcome SHA drift")
        for p,key in (
          (a.pitfall_position_recovery,"pitfall_position_recovery_sha256"),
          (a.pitfall_island_phase_quality,"pitfall_island_phase_quality_sha256"),
          (a.island_geometry,"island_geometry_sha256"),
          (a.graph_edges,"graph_edges_sha256"),
        ):
            if sha(p)!=c["inputs"][key]: raise Stop(f"{key} drift")

        geom=load_geometry(a.island_geometry);islands=sorted(geom)
        if islands!=c["geometry"]["islands"]: raise Stop("island set/order drift")
        edges=load_edges(a.graph_edges)
        gdist=all_pairs_shortest(islands,edges)
        event_map=load_event_map(a.pitfall_position_recovery)
        effort=load_t2_effort(a.pitfall_island_phase_quality)
        if set(effort)!=set(islands): raise Stop("BALA3 effort island coverage drift")
        lam=float(c["geometry"]["graph_lambda_km"])

        edist={i:{} for i in islands}
        maxe=0.0
        for i in islands:
            for j in islands:
                d=hav(*geom[i],*geom[j]);edist[i][j]=d;maxe=max(maxe,d)
        sentinel=maxe+lam

        raw=a.preoutcome_surface.read_bytes().splitlines()
        if len(raw)<2: raise Stop("preoutcome surface empty")
        data=raw[1:];idx=c["allowed_preoutcome_fields"];nfields=32
        tax=defaultdict(lambda:defaultdict(list));observed=defaultdict(set)
        decoded_rows=positive_rows=0
        for rn,line in enumerate(data,1):
            fields=line.split(b"\t")
            if len(fields)!=nfields: raise Stop(f"physical field-count drift row {rn}")
            coreid=dec(fields[idx["coreid"]])
            if coreid not in event_map: raise Stop("preoutcome row outside frozen pitfall Event map")
            phase,island=event_map[coreid]
            if phase not in {"BALA1","BALA2"}: raise Stop("BALA3 row entered preoutcome surface")
            tok=dec(fields[idx["identificationRemarks_MF"]])
            qty=qnum(dec(fields[idx["organismQuantity"]]))
            sci=dec(fields[idx["scientificName"]]);order=dec(fields[idx["order"]])
            family=dec(fields[idx["family"]]);rank=dec(fields[idx["taxonRank"]])
            tax[tok]["scientificName"].append(sci);tax[tok]["order"].append(order)
            tax[tok]["family"].append(family);tax[tok]["taxonRank"].append(rank)
            decoded_rows+=1
            if qty>0:
                observed[tok].add((island,phase));positive_rows+=1

        summaries=[];feature_rows=[];eligible_taxa=0;one_loss_taxa=0
        for tok in sorted(tax):
            ok,reason,sci,order,family,rank=eligible_taxon(tax[tok])
            if ok: eligible_taxa+=1
            p0={i for i in islands if (i,"BALA1") in observed[tok]} if ok else set()
            p1={i for i in islands if (i,"BALA2") in observed[tok]} if ok else set()
            lost=p0-p1
            one=ok and len(p0)>=2 and len(lost)==1 and len(p1)>=1
            if one: one_loss_taxa+=1
            summaries.append({
              "MF_token":tok,"eligible":str(ok).lower(),"reason":reason,
              "scientificName":";".join(sci),"order":";".join(order),"family":";".join(family),"taxonRank":";".join(rank),
              "t0_occupied_islands":len(p0),"t1_occupied_islands":len(p1),
              "t0_to_t1_lost_sources":len(lost),"exactly_one_source_loss":str(one).lower(),
              "lost_source_island":next(iter(lost)) if one else "",
              "t1_target_rows":len(p1) if one else 0
            })
            if not one: continue

            lost_source=next(iter(lost))
            neff_before,shares=effective_source_number(p0,islands,gdist,lam)
            neff_after,_=effective_source_number(p0-{lost_source},islands,gdist,lam)
            delta_neff=neff_before-neff_after
            lost_share=shares[lost_source]

            for target in sorted(p1):
                s0=set(p0)-{target}
                if not s0 or lost_source not in s0: raise Stop("self-anchor/source-loss arithmetic drift")
                denom=math.fsum(math.exp(-gdist[target][src]/lam) for src in s0)
                num=math.exp(-gdist[target][lost_source]/lam)
                if not denom>0 or not (0<num<=denom+1e-15): raise Stop("invalid E_i components")
                E=num/denom

                surviving=set(p1)-{target}
                no=int(len(surviving)==0)
                nearest=min((edist[target][src] for src in surviving),default=sentinel)
                diffuse=math.fsum(math.exp(-edist[target][src]/lam) for src in surviving)
                feature_rows.append({
                  "MF_token":tok,
                  "target_island":target,
                  "lost_source_island":lost_source,
                  "t0_other_source_count":len(s0),
                  "t1_surviving_other_source_count":len(surviving),
                  "nearest_surviving_euclidean_km":repr(nearest),
                  "diffuse_surviving_euclidean_pressure":repr(diffuse),
                  "no_surviving_other_source":no,
                  "target_was_occupied_at_t0":int(target in p0),
                  "log1p_t2_recovered_pitfall_positions":repr(math.log1p(effort[target])),
                  "E_i_lost_access_fraction":repr(E),
                  "event_delta_N_eff":repr(delta_neff),
                  "event_lost_source_share":repr(lost_share)
                })

        if not feature_rows: raise Stop("no exactly-one-loss target rows")
        cont=c["fold_freeze"]["continuous_columns"]
        bytax=defaultdict(list)
        for r in feature_rows: bytax[r["MF_token"]].append(r)
        tokens=sorted(bytax)
        fold_rows=[];fold_stats={};prefeature_estimable=0

        for held in tokens:
            train=[r for r in feature_rows if r["MF_token"]!=held]
            if not train: raise Stop("empty training complement")
            constants={};dropped=[];feature_ok=True
            for col in cont:
                xs=[float(r[col]) for r in train]
                m,sd=pop_mean_sd(xs)
                if sd<=0:
                    if col=="E_i_lost_access_fraction":
                        feature_ok=False
                    else:
                        dropped.append(col)
                else:
                    constants[col]={"mean":m,"sd":sd}
            if feature_ok: prefeature_estimable+=1
            fold_rows.append({
              "heldout_MF_token":held,
              "heldout_target_rows":len(bytax[held]),
              "training_target_rows":len(train),
              "prefeature_estimable":str(feature_ok).lower(),
              "dropped_zero_variance_R2":";".join(sorted(dropped))
            })
            fold_stats[held]={
              "heldout_target_rows":len(bytax[held]),
              "training_target_rows":len(train),
              "prefeature_estimable":feature_ok,
              "dropped_zero_variance_R2":sorted(dropped),
              "standardization":constants
            }

        Evals=[float(r["E_i_lost_access_fraction"]) for r in feature_rows]
        _,Esd=pop_mean_sd(Evals)
        distinct=len({float(x).hex() for x in Evals})
        gate=c["pre_t2_gate"]
        checks={
          "taxonomically_eligible_confirmatory_taxa":eligible_taxa>=gate["minimum_taxonomically_eligible_confirmatory_taxa"],
          "exactly_one_loss_taxa":one_loss_taxa>=gate["minimum_exactly_one_loss_taxa"],
          "exactly_one_loss_target_rows":len(feature_rows)>=gate["minimum_exactly_one_loss_target_rows"],
          "distinct_E_i_values":distinct>=gate["minimum_distinct_E_i_values"],
          "prefeature_estimable_taxon_folds":prefeature_estimable>=gate["minimum_prefeature_estimable_taxon_folds"],
          "E_i_population_sd_positive":Esd>0
        }
        passed=all(checks.values())

        write_csv(a.taxon_summary,summaries,[
          "MF_token","eligible","reason","scientificName","order","family","taxonRank",
          "t0_occupied_islands","t1_occupied_islands","t0_to_t1_lost_sources",
          "exactly_one_source_loss","lost_source_island","t1_target_rows"])
        write_csv(a.features,feature_rows,list(feature_rows[0].keys()))
        write_csv(a.fold_manifest,fold_rows,[
          "heldout_MF_token","heldout_target_rows","training_target_rows",
          "prefeature_estimable","dropped_zero_variance_R2"])
        a.fold_standardization.parent.mkdir(parents=True,exist_ok=True)
        a.fold_standardization.write_text(json.dumps(fold_stats,indent=2,sort_keys=True)+"\n",encoding="utf-8")

        result={
          "schema":"structural.bala_preoutcome_feature_result.v1_140",
          "status":"BALA_PREOUTCOME_FEATURE_GATE_PASSED" if passed else "BALA_PREOUTCOME_FEATURE_GATE_STOPPED",
          "preoutcome_rows_decoded":decoded_rows,
          "positive_preoutcome_rows":positive_rows,
          "taxa_seen_t0_t1":len(tax),
          "taxonomically_eligible_confirmatory_taxa":eligible_taxa,
          "exactly_one_loss_taxa":one_loss_taxa,
          "exactly_one_loss_target_rows":len(feature_rows),
          "distinct_E_i_values":distinct,
          "E_i_population_sd":Esd,
          "prefeature_estimable_taxon_folds":prefeature_estimable,
          "gate_checks":checks,
          "advance_authorized":passed,
          "taxon_summary_sha256":sha(a.taxon_summary),
          "features_sha256":sha(a.features),
          "fold_manifest_sha256":sha(a.fold_manifest),
          "fold_standardization_sha256":sha(a.fold_standardization),
          "t2_rows_opened":0,
          "t2_taxon_identities_opened":0,
          "t2_occurrence_values_opened":0,
          "candidate_minus_reference_effects_computed":0,
          "counts_as_empirical_support_or_non_support":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,decimal.InvalidOperation,Stop) as e:
        result={
          "schema":"structural.bala_preoutcome_feature_result.v1_140",
          "status":"IMPLEMENTATION_STOP",
          "reason":str(e),
          "t2_rows_opened":0,
          "t2_taxon_identities_opened":0,
          "t2_occurrence_values_opened":0,
          "candidate_minus_reference_effects_computed":0,
          "advance_authorized":False,
          "counts_as_empirical_support_or_non_support":False
        };code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
