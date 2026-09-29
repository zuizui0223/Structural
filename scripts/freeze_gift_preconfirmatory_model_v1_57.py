#!/usr/bin/env python3
"""Freeze GIFT R0-R3-C models and all confirmatory R3/C probabilities.

The method is fully defined by v1.57. Pilot response is consumed input;
confirmatory species composition is never requested or read here.
"""
from __future__ import annotations
import argparse,csv,hashlib,heapq,json,math,os,struct
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_preconfirmatory_model_contract_v1_57.json"
EARTH_RADIUS_KM=6371.0088

class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def parse_num(x):
    s=str(x).strip()
    try:
        v=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    except Exception as e:
        raise Stop(f"invalid numeric value: {s!r}") from e
    if not math.isfinite(v): raise Stop("nonfinite numeric value")
    return v

def hav(a,b):
    lat1,lon1=a;lat2,lon2=b
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*EARTH_RADIUS_KM*math.asin(min(1.0,math.sqrt(x)))

def sigmoid(x):
    out=np.empty_like(x,dtype=np.float64)
    pos=x>=0
    out[pos]=1.0/(1.0+np.exp(-x[pos]))
    ex=np.exp(x[~pos]);out[~pos]=ex/(1.0+ex)
    return out

def fit_ridge(X,y,columns):
    X=np.asarray(X,dtype=np.float64,order="C")
    y=np.asarray(y,dtype=np.float64)
    p=X.shape[1]
    if X.ndim!=2 or y.shape!=(X.shape[0],) or p!=len(columns):raise Stop("fit dimension drift")
    beta=np.zeros(p,dtype=np.float64)
    penalty=np.ones(p,dtype=np.float64);penalty[0]=0.0
    final=math.inf
    for iteration in range(1,101):
        eta=X@beta
        mu=sigmoid(eta)
        w=mu*(1.0-mu)
        grad=X.T@(y-mu)-penalty*beta
        H=X.T@(X*w[:,None])
        H.flat[::p+1]+=penalty
        try:delta=np.linalg.solve(H,grad)
        except np.linalg.LinAlgError as e:raise Stop("ridge IRLS linear solve failed") from e
        if not np.all(np.isfinite(delta)):raise Stop("nonfinite IRLS delta")
        beta+=delta
        final=float(np.max(np.abs(delta)))
        if final<=1e-8:
            return {"columns":list(columns),"coefficients":beta,"iterations":iteration,"final_delta":final}
    raise Stop("ridge IRLS did not converge within 100 iterations")

def predict(X,fit):
    p=sigmoid(np.asarray(X,dtype=np.float64)@fit["coefficients"])
    return np.clip(p,1e-12,0.999999999999)

def dijkstra(target,adj):
    dist={target:0.0};q=[(0.0,target)]
    while q:
        d,u=heapq.heappop(q)
        if d!=dist[u]:continue
        for v,w in adj[u]:
            nd=d+w
            if nd<dist.get(v,math.inf):
                dist[v]=nd;heapq.heappush(q,(nd,v))
    return dist

def load_csv(path):
    with path.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def vector_logit(successes,trials):
    s=np.asarray(successes,dtype=np.float64)
    p=(s+0.5)/(float(trials)+1.0)
    return np.log(p/(1.0-p))

def model_mapping(fit):
    return {
      "columns":fit["columns"],
      "coefficients_hex":[float(x).hex() for x in fit["coefficients"]],
      "iterations":fit["iterations"],
      "final_max_abs_delta_hex":float(fit["final_delta"]).hex(),
      "ridge_lambda_hex":float(1.0).hex(),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_universe",type=Path)
    ap.add_argument("pilot_matrix",type=Path)
    ap.add_argument("pilot_freeze",type=Path)
    ap.add_argument("state_reference",type=Path)
    ap.add_argument("partition",type=Path)
    ap.add_argument("graph_edges",type=Path)
    ap.add_argument("spatial_receipt",type=Path)
    ap.add_argument("gift_geography",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--predictions",type=Path,required=True)
    ap.add_argument("--entity-order",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.gift_preconfirmatory_model_contract.v1_57":raise Stop("contract schema drift")
        expected=c["required_response_independent_inputs"]
        for path,key in [
          (a.state_reference,"state_reference_sha256"),
          (a.graph_edges,"source_graph_edges_sha256"),
          (a.partition,"island_partition_sha256"),
          (a.spatial_receipt,"spatial_receipt_sha256"),
          (a.gift_geography,"gift_geography_sha256"),
        ]:
            if sha(path)!=expected[key]:raise Stop(f"response-independent input SHA drift: {key}")

        pf=json.loads(a.pilot_freeze.read_text())
        preq=c["pilot_parent_requirement"]
        if pf.get("schema")!=preq["schema"] or pf.get("status")!=preq["status"]:raise Stop("pilot freeze did not qualify")
        if sha(a.pilot_universe)!=pf["artifact_files"]["pilot_species_universe.csv"]["sha256"]:raise Stop("pilot universe SHA drift")
        if sha(a.pilot_matrix)!=pf["artifact_files"]["pilot_matrix.csv"]["sha256"]:raise Stop("pilot matrix SHA drift")

        universe=load_csv(a.pilot_universe)
        if not universe:raise Stop("empty focal species universe")
        species_ids=[str(r["work_ID"]).strip() for r in universe]
        if len(species_ids)!=len(set(species_ids)):raise Stop("duplicate focal work_ID")
        if species_ids!=sorted(species_ids,key=lambda x:int(float(x))):raise Stop("focal species order drift")
        S=len(species_ids);sindex={wid:i for i,wid in enumerate(species_ids)}

        part=load_csv(a.partition)
        if len(part)!=503:raise Stop("partition population drift")
        pmap={str(r["entity_ID"]):r for r in part}
        if len(pmap)!=503:raise Stop("duplicate partition entity")
        pilot_ids=sorted([eid for eid,r in pmap.items() if r["split"]=="pilot"],key=lambda x:int(float(x)))
        confirm_ids=sorted([eid for eid,r in pmap.items() if r["split"]=="confirmatory"],key=lambda x:int(float(x)))
        if len(pilot_ids)!=99 or len(confirm_ids)!=404:raise Stop("pilot/confirmatory count drift")
        pidx={eid:i for i,eid in enumerate(pilot_ids)}

        Y=np.full((99,S),-1,dtype=np.int8)
        matrix_rows=load_csv(a.pilot_matrix)
        if len(matrix_rows)!=99*S:raise Stop("pilot matrix row count drift")
        for r in matrix_rows:
            eid=str(r["entity_ID"]).strip();wid=str(r["work_ID"]).strip()
            if eid not in pidx or wid not in sindex:raise Stop("pilot matrix key outside frozen universe")
            y=int(str(r["y"]).strip())
            if y not in (0,1):raise Stop("pilot target domain drift")
            ii=pidx[eid];jj=sindex[wid]
            if Y[ii,jj]!=-1:raise Stop("duplicate pilot matrix cell")
            Y[ii,jj]=y
        if np.any(Y<0):raise Stop("incomplete pilot matrix")
        if np.any(Y.sum(axis=0)<5) or np.any((99-Y.sum(axis=0))<5):raise Stop("pilot species threshold drift")

        state_rows=load_csv(a.state_reference)
        smap={str(r["entity_ID"]):r for r in state_rows}
        if set(smap)!=set(pmap):raise Stop("state/partition population mismatch")
        pool_levels=sorted({r["regional_pool"] for r in part})
        if len(pool_levels)!=13:raise Stop("regional-pool level count drift")
        pool_index={p:i for i,p in enumerate(pool_levels)}

        geo_rows=load_csv(a.gift_geography)
        gmap={str(r["entity_ID"]):r for r in geo_rows}
        coords={}
        for eid in pmap:
            if eid not in gmap:raise Stop("primary entity missing GIFT geography")
            coords[eid]=(parse_num(gmap[eid]["latitude"]),parse_num(gmap[eid]["longitude"]))

        sr=json.loads(a.spatial_receipt.read_text())
        scales={k:float.fromhex(v) for k,v in sr["regional_edge_scale_hex"].items()}
        if set(scales)!=set(pool_levels):raise Stop("regional scale levels drift")

        adj={p:{eid:[] for eid,r in pmap.items() if r["regional_pool"]==p} for p in pool_levels}
        max_edge={p:0.0 for p in pool_levels}
        edge_rows=load_csv(a.graph_edges)
        for r in edge_rows:
            p=r["regional_pool"];u=str(r["from_entity_ID"]);v=str(r["to_entity_ID"]);d=float.fromhex(r["distance_km_hex"])
            if p not in adj or u not in adj[p] or v not in adj[p] or d<=0:raise Stop("graph edge outside frozen pool")
            adj[p][u].append((v,d));adj[p][v].append((u,d));max_edge[p]=max(max_edge[p],d)
        node_count={p:len(nodes) for p,nodes in adj.items()}
        if any(max_edge[p]<=0 or node_count[p]<3 for p in pool_levels):raise Stop("invalid graph sentinel context")

        # Distances from every target to each pilot island, frozen response-independent geometry only.
        all_ids=pilot_ids+confirm_ids
        euc=np.empty((503,99),dtype=np.float64)
        gdist=np.full((503,99),np.inf,dtype=np.float64)
        for ti,eid in enumerate(all_ids):
            for j,pid in enumerate(pilot_ids):euc[ti,j]=hav(coords[eid],coords[pid])
            pool=pmap[eid]["regional_pool"]
            paths=dijkstra(eid,adj[pool])
            for j,pid in enumerate(pilot_ids):
                if pmap[pid]["regional_pool"]==pool and pid in paths:gdist[ti,j]=paths[pid]

        pilot_arch=np.array([pmap[e]["archip"] for e in pilot_ids],dtype=object)
        pilot_pool=np.array([pmap[e]["regional_pool"] for e in pilot_ids],dtype=object)

        def source_raw(target_id,ti,training):
            pool=pmap[target_id]["regional_pool"];scale=scales[pool]
            allowed=np.ones(99,dtype=bool)
            if training:allowed=(pilot_arch!=pmap[target_id]["archip"])
            trials=int(allowed.sum())
            if trials<1:raise Stop("pilot cross-fit left zero global training islands")
            succ=Y[allowed].sum(axis=0)
            global_logit=vector_logit(succ,trials)
            rallowed=allowed & (pilot_pool==pool)
            rtrials=int(rallowed.sum());rsucc=Y[rallowed].sum(axis=0) if rtrials else np.zeros(S,dtype=np.int64)
            regional_logit=vector_logit(rsucc,rtrials)

            occ=(Y==1) & allowed[:,None]
            ed=euc[ti]
            nearest_e=np.min(np.where(occ,ed[:,None],np.inf),axis=0)
            empty_e=~np.isfinite(nearest_e)
            nearest_e[empty_e]=math.pi*EARTH_RADIUS_KM+scale
            pressure_e=np.sum(occ*np.exp(-ed/scale)[:,None],axis=0,dtype=np.float64)

            gd=gdist[ti]
            reachable=np.isfinite(gd)
            gocc=occ & reachable[:,None]
            nearest_g=np.min(np.where(gocc,gd[:,None],np.inf),axis=0)
            empty_g=~np.isfinite(nearest_g)
            nearest_g[empty_g]=(node_count[pool]-1)*max_edge[pool]+scale
            gw=np.zeros(99,dtype=np.float64);gw[reachable]=np.exp(-gd[reachable]/scale)
            pressure_g=np.sum(gocc*gw[:,None],axis=0,dtype=np.float64)
            raw=np.column_stack([
              global_logit,regional_logit,np.log1p(nearest_e),np.log1p(pressure_e),
              np.log1p(nearest_g),np.log1p(pressure_g)
            ])
            return raw,int(empty_e.sum()),int(empty_g.sum())

        source_raw_train=np.empty((99*S,6),dtype=np.float64)
        y=np.empty(99*S,dtype=np.float64)
        train_empty_e=train_empty_g=0
        for i,eid in enumerate(pilot_ids):
            raw,ee,eg=source_raw(eid,i,True)
            sl=slice(i*S,(i+1)*S)
            source_raw_train[sl]=raw;y[sl]=Y[i]
            train_empty_e+=ee;train_empty_g+=eg
        src_mean=np.mean(source_raw_train,axis=0,dtype=np.float64)
        src_var=np.mean((source_raw_train-src_mean)**2,axis=0,dtype=np.float64)
        src_sd=np.sqrt(src_var)
        if not np.all(np.isfinite(src_sd)) or np.any(src_sd<=0):raise Stop("zero/nonfinite source-feature SD")
        source_z=(source_raw_train-src_mean)/src_sd

        r0_cont=["z_ccvt","z_temp","z_vart","z_prec","z_varp","z_elev"]
        r1_cont=["z_log_area","z_dist","z_slmp","z_gmmc"]
        r2_cont=["z_log1p_nearest_island_km","z_generic_neighbor_pressure"]
        columns=["intercept"]+[f"regional_pool::{p}" for p in pool_levels]+r0_cont+r1_cont+r2_cont+[
          "z_global_occupancy_jeffreys_logit","z_regional_pool_prevalence_jeffreys_logit",
          "z_log1p_nearest_euclidean_source_km","z_log1p_euclidean_source_pressure",
          "z_log1p_nearest_graph_source_km","z_log1p_graph_source_pressure"]
        if len(columns)!=32:raise Stop("full model column count drift")
        X=np.empty((99*S,32),dtype=np.float64)
        for i,eid in enumerate(pilot_ids):
            sl=slice(i*S,(i+1)*S);row=smap[eid]
            X[sl,0]=1.0
            one=np.zeros(13,dtype=np.float64);one[pool_index[row["regional_pool"]]]=1.0
            X[sl,1:14]=one
            X[sl,14:20]=[parse_num(row[x]) for x in r0_cont]
            X[sl,20:24]=[parse_num(row[x]) for x in r1_cont]
            X[sl,24:26]=[parse_num(row[x]) for x in r2_cont]
        X[:,26:32]=source_z

        bounds={"R0":20,"R1":24,"R2":26,"R3":30,"C":32}
        fits={}
        for name in ("R0","R1","R2","R3","C"):
            k=bounds[name];fits[name]=fit_ridge(X[:,:k],y,columns[:k])

        a.entity_order.parent.mkdir(parents=True,exist_ok=True)
        with a.entity_order.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["entity_ID","archip","regional_pool"])
            for eid in confirm_ids:w.writerow([eid,pmap[eid]["archip"],pmap[eid]["regional_pool"]])

        confirm_empty_e=confirm_empty_g=0
        a.predictions.parent.mkdir(parents=True,exist_ok=True)
        with a.predictions.open("wb") as h:
            h.write(b"STRUCTURAL_GIFT_PRED_V1\n")
            h.write(struct.pack("<II",len(confirm_ids),S))
            for ci,eid in enumerate(confirm_ids):
                ti=99+ci
                raw,ee,eg=source_raw(eid,ti,False);confirm_empty_e+=ee;confirm_empty_g+=eg
                z=(raw-src_mean)/src_sd
                row=smap[eid]
                base=np.empty((S,32),dtype=np.float64);base[:,0]=1.0
                one=np.zeros(13,dtype=np.float64);one[pool_index[row["regional_pool"]]]=1.0
                base[:,1:14]=one
                base[:,14:20]=[parse_num(row[x]) for x in r0_cont]
                base[:,20:24]=[parse_num(row[x]) for x in r1_cont]
                base[:,24:26]=[parse_num(row[x]) for x in r2_cont]
                base[:,26:32]=z
                p3=predict(base[:,:30],fits["R3"]);pc=predict(base[:,:32],fits["C"])
                pair=np.empty((S,2),dtype="<f8");pair[:,0]=p3;pair[:,1]=pc
                h.write(pair.tobytes(order="C"))

        src_names=[
          "global_occupancy_jeffreys_logit","regional_pool_prevalence_jeffreys_logit",
          "log1p_nearest_euclidean_source_km","log1p_euclidean_source_pressure",
          "log1p_nearest_graph_source_km","log1p_graph_source_pressure"]
        result={
          "schema":"structural.gift_preconfirmatory_model_result.v1_57",
          "status":"CONFIRMATORY_R3_C_PREDICTIONS_FROZEN_BEFORE_RESPONSE",
          "focal_species":S,
          "training_rows":99*S,
          "confirmatory_entities":404,
          "prediction_cells":404*S,
          "regional_pool_levels":pool_levels,
          "source_standardization":{name:{"mean_hex":float(src_mean[i]).hex(),"sd_hex":float(src_sd[i]).hex()} for i,name in enumerate(src_names)},
          "training_empty_global_source_rows":train_empty_e,
          "training_empty_graph_source_rows":train_empty_g,
          "confirmatory_empty_global_source_rows":confirm_empty_e,
          "confirmatory_empty_graph_source_rows":confirm_empty_g,
          "models":{name:model_mapping(fits[name]) for name in ("R0","R1","R2","R3","C")},
          "species_universe_sha256":sha(a.pilot_universe),
          "pilot_matrix_sha256":sha(a.pilot_matrix),
          "entity_order_sha256":sha(a.entity_order),
          "prediction_binary_sha256":sha(a.predictions),
          "prediction_binary_magic":"STRUCTURAL_GIFT_PRED_V1\\n",
          "prediction_binary_shape":[404,S,2],
          "prediction_binary_fields":["p_R3","p_C"],
          "pilot_response_used":True,
          "confirmatory_target_values_used":False,
          "confirmatory_species_composition_opened":False,
          "confirmatory_response_authorized":False,
          "counts_as_fresh_confirmation":False,
          "fresh_system_denominator_contribution":0,
          "next_action":"commit and exact-replay verify this prediction artifact; only then authorize one-shot retrieval of the 596 frozen confirmatory list_IDs"
        }
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={"schema":"structural.gift_preconfirmatory_model_result.v1_57","status":"STOP","reason":str(e),
          "confirmatory_species_composition_opened":False,"confirmatory_response_authorized":False,
          "counts_as_fresh_confirmation":False,"fresh_system_denominator_contribution":0};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
