#!/usr/bin/env python3
"""Validate SW Finland historical source identities from two independent t0 signals.

Candidate source islands are the complement of archived historical-absence row
keys. Exactness is accepted only when:
  1) candidate source count agrees with archived Historical_total_log under a
     frozen affine log10 calibration; and
  2) candidate-source nearest distances agree with archived
     Dist_to_historical_log under a separate affine log10 calibration.

Future colonization outcome is never parsed.
"""
from __future__ import annotations

import argparse,csv,hashlib,json,math,re,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_dual_t0_source_identity_contract_v1_176.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return re.sub(r"\s+"," ",unicodedata.normalize("NFC",str(x)).strip())

def maybe_float(x:str):
    try:v=float(str(x).strip())
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None

def parse_float(x:str,label:str)->float:
    v=maybe_float(x)
    if v is None:raise Stop(f"invalid {label}")
    return v

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def ols_xy(xs,ys):
    if len(xs)!=len(ys) or len(xs)<2:raise Stop("invalid OLS calibration vectors")
    mx=math.fsum(xs)/len(xs);my=math.fsum(ys)/len(ys)
    den=math.fsum((x-mx)**2 for x in xs)
    if den<=0:raise Stop("zero calibration x variance")
    slope=math.fsum((x-mx)*(y-my) for x,y in zip(xs,ys))/den
    intercept=my-slope*mx
    if not math.isfinite(intercept) or not math.isfinite(slope):raise Stop("nonfinite calibration")
    return intercept,slope

def euclidean(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])

def nearest_distance(target,sources,coords):
    if not sources:raise Stop("empty candidate source set")
    return min(euclidean(coords[target],coords[s]) for s in sources)

def load_t0(path:Path,router:dict,contract:dict):
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":raise Stop("router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:raise Stop("future outcome boundary violated")
    absent=defaultdict(set);count_tokens=defaultdict(set);dist_by_pair={};coords={};pairs=set();rows=0
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Euref_X_original","Euref_Y_original","Historical_total_log","Dist_to_historical_log"):
            if key not in rd.fieldnames:raise Stop(f"missing safe field {key}")
        for row in rd:
            rows+=1
            sp=norm(row["spp.name"]);isl=str(row["holmkod"]).strip()
            if not sp or not isl:raise Stop("blank species/island key")
            pair=(sp,isl)
            if pair in pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(pair);absent[sp].add(isl)
            count_tokens[sp].add(str(row["Historical_total_log"]).strip())
            dist_by_pair[pair]=maybe_float(row["Dist_to_historical_log"])
            xy=(parse_float(row["Euref_X_original"],"Euref_X_original"),parse_float(row["Euref_Y_original"],"Euref_Y_original"))
            if isl in coords and coords[isl]!=xy:raise Stop(f"coordinate drift within island {isl}")
            coords[isl]=xy
    if rows!=225345:raise Stop(f"archive row count drift: {rows}")
    if len(absent)!=int(contract["population"]["archive_species"]):raise Stop("archive species count drift")
    if len(coords)!=int(contract["population"]["island_universe"]):raise Stop("island count drift")
    if any(len(v)!=1 for v in count_tokens.values()):raise Stop("Historical_total_log varies within species")
    return absent,count_tokens,dist_by_pair,coords,rows

def anchor_table(contract):
    pot={norm(k):int(v) for k,v in contract["alphabetic_t0_anchor_table"]["potential_islands"].items()}
    return {sp:(p,471-p) for sp,p in pot.items()}

def calibrate_count(absent,count_tokens,anchors,contract):
    for sp,(p,n) in anchors.items():
        if sp not in absent:raise Stop(f"anchor species absent from archive: {sp}")
        if len(absent[sp])!=p:raise Stop(f"anchor archived absence mismatch: {sp}: {len(absent[sp])} != {p}")
    xs=[];ys=[];used=[]
    for sp,(p,n) in sorted(anchors.items()):
        tok=next(iter(count_tokens[sp]));z=maybe_float(tok)
        if z is not None and n>=1:
            xs.append(z);ys.append(math.log10(n));used.append(sp)
    expected=int(contract["count_consistency"]["expected_numeric_anchor_count"])
    if len(used)!=expected:raise Stop(f"numeric count anchor drift: {len(used)} != {expected}")
    a,b=ols_xy(xs,ys)
    if contract["count_consistency"]["slope_must_be_positive"] and b<=0:raise Stop("count calibration slope nonpositive")
    maxres=max(abs(y-(a+b*x)) for x,y in zip(xs,ys))
    if maxres>float(contract["count_consistency"]["anchor_max_absolute_log10_residual"]):
        raise Stop(f"count-anchor log residual too large: {maxres}")
    return a,b,used,maxres

def calibrate_distance(absent,dist_by_pair,coords,anchors,contract):
    xs=[];ys=[];used_species=[];row_count=0
    for sp,(p,n) in sorted(anchors.items()):
        if n<1:continue
        sources=set(coords)-absent[sp]
        if len(sources)!=n:raise Stop(f"anchor source complement count drift: {sp}")
        local=[]
        for target in sorted(absent[sp]):
            z=dist_by_pair[(sp,target)]
            if z is None:
                local=[];break
            d=nearest_distance(target,sources,coords)
            if d<=0:raise Stop(f"nonpositive anchor nearest distance: {sp}|{target}")
            local.append((z,math.log10(d)))
        if local:
            used_species.append(sp);row_count+=len(local)
            for x,y in local:xs.append(x);ys.append(y)
    if len(used_species)<int(contract["distance_consistency"]["minimum_calibration_species"]):
        raise Stop(f"too few distance calibration species: {len(used_species)}")
    if row_count<int(contract["distance_consistency"]["minimum_calibration_rows"]):
        raise Stop(f"too few distance calibration rows: {row_count}")
    a,b=ols_xy(xs,ys)
    if contract["distance_consistency"]["slope_must_be_positive"] and b<=0:raise Stop("distance calibration slope nonpositive")
    maxres=max(abs(y-(a+b*x)) for x,y in zip(xs,ys))
    if maxres>float(contract["distance_consistency"]["anchor_max_absolute_log10_residual"]):
        raise Stop(f"distance-anchor log residual too large: {maxres}")
    return a,b,used_species,row_count,maxres

def validate_species(absent,count_tokens,dist_by_pair,coords,count_cal,dist_cal,contract):
    ca,cb=count_cal;da,db=dist_cal
    count_tol=float(contract["count_consistency"]["exact_species_max_absolute_log10_residual"])
    dist_tol=float(contract["distance_consistency"]["species_exact_if"].split("<=")[-1].strip()) if False else 0.0001
    rows=[];members=[];exact=0;count_fail=0;distance_fail=0;missing_distance=0;nonnumeric=0;zero=0
    for sp in sorted(absent):
        tok=next(iter(count_tokens[sp]));zcount=maybe_float(tok)
        n=471-len(absent[sp])
        if zcount is None:
            nonnumeric+=1
            rows.append((sp,"excluded_nonnumeric_Historical_total",len(absent[sp]),n,"","","",""));continue
        if n<1:
            zero+=1
            rows.append((sp,"excluded_zero_candidate_sources",len(absent[sp]),n,"","","",""));continue
        count_res=abs(math.log10(n)-(ca+cb*zcount))
        count_ok=count_res<=count_tol

        sources=set(coords)-absent[sp]
        dmax=0.0;drows=0;dist_ok=True;dist_missing=False
        for target in absent[sp]:
            z=dist_by_pair[(sp,target)]
            if z is None:
                dist_ok=False;dist_missing=True;break
            d=nearest_distance(target,sources,coords)
            if d<=0:raise Stop(f"nonpositive candidate distance: {sp}|{target}")
            res=abs(math.log10(d)-(da+db*z));dmax=max(dmax,res);drows+=1
            if dmax>dist_tol:dist_ok=False
        if dist_missing:missing_distance+=1
        elif not dist_ok:distance_fail+=1
        if not count_ok:count_fail+=1
        if count_ok and dist_ok and not dist_missing:
            status="exact_source_identity_dual_t0_validated";exact+=1
            members.extend((sp,s) for s in sorted(sources))
        else:
            status="excluded_t0_source_identity_not_exact"
        rows.append((sp,status,len(absent[sp]),n,float(count_res).hex(),float(dmax).hex(),drows,tok))
    if exact<int(contract["exact_source_identity"]["minimum_exact_species"]):
        raise Stop(f"only {exact} species passed dual t0 source identity gate")
    return rows,members,{
      "exact_source_species":exact,
      "count_failed_species":count_fail,
      "distance_failed_species":distance_fail,
      "missing_distance_species":missing_distance,
      "nonnumeric_species":nonnumeric,
      "zero_candidate_source_species":zero
    }

def write(path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header);w.writerows(rows)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--audit-output",type=Path,required=True)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--membership-output",type=Path,required=True)
    p.add_argument("--geometry-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=json.loads(a.contract.read_text());rr=json.loads(a.router_receipt.read_text())
        absent,count_tokens,dist_by_pair,coords,nrows=load_t0(a.safe_csv,rr,c)
        anchors=anchor_table(c)
        ca,cb,count_anchor_species,count_anchor_max=calibrate_count(absent,count_tokens,anchors,c)
        da,db,dist_anchor_species,dist_anchor_rows,dist_anchor_max=calibrate_distance(absent,dist_by_pair,coords,anchors,c)
        audit,members,stats=validate_species(absent,count_tokens,dist_by_pair,coords,(ca,cb),(da,db),c)
        exact_species={row[0] for row in audit if row[1]=="exact_source_identity_dual_t0_validated"}
        species_rows=[(row[0],"exact_source_identity",row[2],471-row[3],row[3]) for row in audit if row[0] in exact_species]
        geometry=[(i,*coords[i]) for i in sorted(coords)]
        write(a.audit_output,["species","status","archived_absent_count","candidate_source_count","count_log10_residual_hex","distance_log10_max_residual_hex","distance_rows_checked","Historical_total_log_token"],audit)
        write(a.species_output,["species","status","archived_absent_count","Potential_islands","historical_source_count"],species_rows)
        write(a.membership_output,["species","source_holmkod"],members)
        write(a.geometry_output,["holmkod","Euref_X_original","Euref_Y_original"],geometry)
        r={
          "schema":"structural.sw_finland_exact_source_reconstruction_result.v1_176",
          "status":c["success_ceiling"]["status"],
          "candidate_id":c["candidate_id"],
          "method":"dual t0 count and nearest-distance consistency",
          "archive_rows":nrows,"archive_species":len(absent),"unique_islands":len(coords),
          "alphabetic_anchor_count":len(anchors),
          "count_calibration_anchor_species":count_anchor_species,
          "count_calibration_anchor_count":len(count_anchor_species),
          "count_calibration_intercept_hex":float(ca).hex(),"count_calibration_slope_hex":float(cb).hex(),
          "count_calibration_anchor_max_log10_residual":count_anchor_max,
          "distance_calibration_anchor_species":dist_anchor_species,
          "distance_calibration_anchor_species_count":len(dist_anchor_species),
          "distance_calibration_rows":dist_anchor_rows,
          "distance_calibration_intercept_hex":float(da).hex(),"distance_calibration_slope_hex":float(db).hex(),
          "distance_calibration_anchor_max_log10_residual":dist_anchor_max,
          **stats,
          "source_membership_rows":len(members),
          "future_outcome_values_opened":0,"protected_outcome_values_decoded":0,
          "pilot_future_outcome_authorized":False,"confirmatory_future_outcome_authorized":False,
          "counts_as_empirical_evidence":False
        }
        r["audit_output_sha256"]=sha(a.audit_output);r["species_output_sha256"]=sha(a.species_output)
        r["membership_output_sha256"]=sha(a.membership_output);r["geometry_output_sha256"]=sha(a.geometry_output)
        code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_exact_source_reconstruction_result.v1_176",
           "status":"STOP_DUAL_T0_SOURCE_IDENTITY_GATE","reason":str(exc),
           "future_outcome_values_opened":0,"protected_outcome_values_decoded":0,
           "counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
