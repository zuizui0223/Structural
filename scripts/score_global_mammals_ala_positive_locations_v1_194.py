#!/usr/bin/env python3
"""One-shot, externally sourced ALA positive-location scoring of frozen mammal predictions.

No ALA absence labels, no original heldout mammal label and no model refit.
The first FID x species x eventDate access is conditional on the frozen v1.194 request.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,struct,unicodedata,zipfile
from collections import defaultdict
from decimal import Decimal,InvalidOperation
from pathlib import Path
import numpy as np

ACTUAL_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_PRED_V1\n"
NULL_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_NULL_PRED_V1\n"
class Stop(ValueError):pass

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def key(value):
    return " ".join(unicodedata.normalize("NFC",str(value)).replace("."," ").replace("_"," ").split()).casefold()

def rows(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def datayear(raw,yr0=2000,yr1=2026):
    s=str(raw).strip()
    if not re.match(r"^\d{4}(?:$|[-/ T]|[01]\d[0-3]\d$)",s):return None
    y=int(s[:4])
    return y if yr0<=y<=yr1 else None

def parse_fid(raw):
    s=str(raw).strip()
    if not s:return None
    try:v=Decimal(s)
    except InvalidOperation:return None
    if not v.is_finite() or v!=v.to_integral_value():return None
    z=int(v)
    return z if z>=0 else None

def dbf_layout(data,required):
    if len(data)<65 or data[0] not in (3,131,139,48):raise Stop("unsupported DBF header")
    n=int.from_bytes(data[4:8],"little")
    hdr=int.from_bytes(data[8:10],"little")
    width=int.from_bytes(data[10:12],"little")
    if not 1<=n<=2_000_000 or not 65<=hdr<len(data) or not 2<=width<=65535 or hdr+n*width>len(data):
        raise Stop("DBF length/record drift")
    offset=1;fields={}
    for p in range(32,hdr-1,32):
        f=data[p:p+32]
        if not f or f[0]==13:break
        nm=f[:11].split(b"\0",1)[0].decode("ascii")
        wid=int(f[16]);dtype=chr(f[11])
        if not nm or nm in fields or wid<=0:raise Stop("duplicate/invalid DBF field")
        fields[nm]=(offset,wid,dtype);offset+=wid
    if not set(required).issubset(fields):raise Stop("ALA required DBF fields unavailable")
    for x in required:
        off,w,_=fields[x]
        if off+w>width:raise Stop("DBF field exceeds record")
    return n,hdr,width,fields

def extract_positive_pairs(zip_bytes,contract,fid_to_id,allowed_names):
    src=contract["input_authority"]
    if len(zip_bytes)!=src["source_zip_size_bytes"] or blob_sha(zip_bytes)!=src["source_zip_git_blob_sha1"]:
        raise Stop("ALA source ZIP git identity drift")
    if hashlib.sha256(zip_bytes).hexdigest()!=src["source_zip_sha256"]:
        raise Stop("ALA source ZIP SHA256 drift")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        if z.testzip() is not None:raise Stop("source ZIP CRC drift")
        names=[x for x in z.namelist() if Path(x).name.lower()==src["source_dbf"].lower()
               and not x.lower().startswith("__macosx/") and not Path(x).name.startswith("._")]
        if len(names)!=1:raise Stop("source ZIP DBF membership drift")
        data=z.read(names[0])
    n,head,record,fields=dbf_layout(data,src["external_columns_semantically_opened_after_request_only"])
    pairs=set();selected_rows=dated_rows=0;undated=0
    def txt(recordbytes,field):
        off,w,_=fields[field]
        return recordbytes[off:off+w].strip(b" \0").decode("latin-1").strip()
    for i in range(n):
        r=data[head+i*record:head+(i+1)*record]
        if r[:1]==b"*":continue
        if r[:1]!=b" ":raise Stop("unexpected ALA DBF deletion flag")
        species=key(txt(r,"scientific"))
        if species not in allowed_names:continue
        selected_rows+=1
        y=datayear(txt(r,"eventDate"))
        if y is None:
            undated+=1;continue
        dated_rows+=1
        fid=parse_fid(txt(r,"FID"))
        if fid is None or fid not in fid_to_id:continue
        pairs.add((allowed_names[species],fid_to_id[fid]))
    return pairs,{"external_dbf_rows":n,"provisional_focal_rows":selected_rows,
                  "dated_provisional_focal_rows":dated_rows,
                  "excluded_missing_invalid_or_old_date_rows":undated,
                  "unique_valid_focal_island_pairs":len(pairs)}

def check_gate(contract,request,manifest,screen_receipt,eligible_csv,geometry_receipt,crosswalk,species,entity_order,actual,null):
    if contract["schema"]!="structural.ala_independent_positive_location_protocol.v1_194":
        raise Stop("contract schema drift")
    if request.get("schema")!="structural.ala_positive_location_request.v1_194":
        raise Stop("request schema drift")
    if request.get("status")!="AUTHORIZE_ONE_SHOT_EXTERNAL_POSITIVE_PAIR_SCORING":
        raise Stop("one-shot request not authorized")
    if not request.get("one_shot") or request.get("original_heldout_response_access") is not False:
        raise Stop("unsealed source or original heldout response")
    if request.get("model_refit") is not False or request.get("eBird_used") is not False:
        raise Stop("unexpected model refit/eBird")
    inputs=contract["input_authority"]
    for label,path in [("taxon_eligibility_receipt_sha256",screen_receipt),
                       ("taxon_eligibility_table_sha256",eligible_csv)]:
        if sha(path)!=request.get(label):raise Stop("one-shot SHA binding drift: "+label)
    if screen_receipt.name!=Path(inputs["taxon_eligibility_receipt"]).name or eligible_csv.name!=Path(inputs["taxon_eligibility"]).name:
        raise Stop("native eligibility path drift")
    a=json.loads(screen_receipt.read_text())
    if a.get("status")!=inputs["taxon_eligibility_expected_status"] or a.get("provisional_taxa")!=65 or a.get("external_species_x_island_positive_pairs_opened")!=0:
        raise Stop("pre-pair taxon screen receipt failed")
    if a["eligibility_table_sha256"]!=sha(eligible_csv):raise Stop("native eligibility receipt/table mismatch")
    if manifest.get("status")!="HOLD_ALA_FOCAL_TAXA_AND_GEOMETRY_IDENTITIES_READY_FUTURE_PAIR_GATE":
        raise Stop("taxon manifest drift")
    if manifest.get("ALA_island_x_species_pairs_semantically_decoded")!=0:raise Stop("external outcome already opened")
    if manifest.get("original_heldout_response_values_read")!=0:raise Stop("original outcome already opened")
    if geometry_receipt.get("exact_one_to_one_heldout_matches")!=167:raise Stop("frozen island crosswalk count drift")
    required={
      crosswalk:inputs["island_crosswalk_sha256"],
      species:inputs["original_species_universe_sha256"],
      entity_order:inputs["entity_order_sha256"],
      actual:inputs["actual_predictions_sha256"],
      null:inputs["rewired_predictions_sha256"]
    }
    for path,expected in required.items():
        if sha(path)!=expected:raise Stop("input file SHA drift: "+path.name)
    if geometry_receipt.get("crosswalk_sha256")!=sha(crosswalk):
        raise Stop("frozen geometry receipt mismatch")
    return a

def read_predictions(path,magic,shape):
    with path.open("rb") as f:
        got=f.read(len(magic))
        if got!=magic:raise Stop("prediction magic mismatch")
        dims=struct.unpack("<"+"I"*len(shape),f.read(len(shape)*4))
    if tuple(dims)!=tuple(shape):raise Stop("prediction shape drift")
    offset=len(magic)+len(shape)*4
    if path.stat().st_size!=offset+int(np.prod(shape))*8:raise Stop("prediction payload size drift")
    return np.memmap(path,dtype="<f8",mode="r",offset=offset,shape=shape)

def normalized_score(p3,pc,qn,pos):
    """Relative-location log score; input cases are 0-based positions in 167 island pool."""
    a=np.clip(np.asarray(p3,dtype=float),1e-12,1-1e-12)
    b=np.clip(np.asarray(pc,dtype=float),1e-12,1-1e-12)
    c=np.clip(np.asarray(qn,dtype=float),1e-12,1-1e-12)
    if a.ndim!=1 or b.shape!=a.shape or c.ndim!=2 or c.shape[1]!=len(a) or c.shape[0]!=20:
        raise Stop("normalized scoring shape drift")
    if len(a)!=167:raise Stop("scoring pool must be all 167 matched islands")
    if len(pos)==0:raise Stop("empty species ALA positive set")
    q3=a/a.sum();qc=b/b.sum();qnull=c/c.sum(axis=1,keepdims=True)
    idx=np.asarray(pos,dtype=int)
    if np.any(idx<0) or np.any(idx>=167):raise Stop("ALA positive index outside fixed island pool")
    loss3=float(-np.mean(np.log(q3[idx])))
    lossc=float(-np.mean(np.log(qc[idx])))
    lossnull=float(-np.mean(np.log(qnull[:,idx])))
    return lossc-loss3,lossc-lossnull,loss3,lossc,lossnull

def analyze(contract,request,zip_file,manifest_file,screen_receipt,eligible_csv,geometry_file,crosswalk_file,species_file,order_file,actual_file,null_file):
    manifest=json.loads(manifest_file.read_text())
    geom=json.loads(geometry_file.read_text())
    check_gate(contract,request,manifest,screen_receipt,eligible_csv,geom,crosswalk_file,species_file,order_file,actual_file,null_file)
    eligibility=rows(eligible_csv)
    if len(eligibility)!=70:raise Stop("70 eligible+ineligible source names drift")
    allowed={key(r["species_name"]):r["species_name"] for r in eligibility if r["eligible_provisional"]=="true"}
    if len(allowed)!=65 or len({key(r["species_name"]) for r in eligibility})!=70:
        raise Stop("eligible taxon count or uniqueness drift")
    cross=rows(crosswalk_file)
    if len(cross)!=167:raise Stop("167 matched island row count drift")
    fid_to_id={};matched_ids=[]
    for r in cross:
        fid=int(r["ALA_FID"]);iid=str(r["ID"])
        if fid in fid_to_id or iid in matched_ids:raise Stop("duplicate ALA FID or original island")
        fid_to_id[fid]=iid;matched_ids.append(iid)

    species=rows(species_file);order=rows(order_file)
    if len(species)!=529 or len(order)!=4126:raise Stop("frozen predictor population drift")
    jmap={key(r["species_name"]):j for j,r in enumerate(species)}
    if len(jmap)!=529 or not set(allowed).issubset(jmap):raise Stop("original species-name routing drift")
    imap={str(r["ID"]):i for i,r in enumerate(order)}
    if len(imap)!=4126 or not set(matched_ids).issubset(imap):raise Stop("original heldout island routing drift")

    # The fixed 167-island denominator is sorted by original heldout prediction order.
    matched_ids=sorted(matched_ids,key=lambda x:imap[x])
    rows_all=np.asarray([imap[i] for i in matched_ids],dtype=int)
    pool_position={i:k for k,i in enumerate(matched_ids)}

    pos,record_audit=extract_positive_pairs(zip_file.read_bytes(),contract,fid_to_id,allowed)
    byspecies=defaultdict(set)
    for name,iid in pos:byspecies[key(name)].add(iid)
    unique_islands={iid for _,iid in pos}
    unique_blocks={order[imap[iid]]["block_id"] for iid in unique_islands}
    minimum=contract["support_before_scoring"]
    support={"pairs":len(pos),"species":len(byspecies),"islands":len(unique_islands),"blocks":len(unique_blocks)}
    record_audit.update({"support_pairs":support})
    if not (support["pairs"]>=minimum["minimum_distinct_positive_pairs"] and
        support["species"]>=minimum["minimum_distinct_positive_taxa"] and
        support["islands"]>=minimum["minimum_distinct_matched_islands_with_positive_records"] and
        support["blocks"]>=minimum["minimum_frozen_spatial_blocks_with_positive_records"]):
        return [],{
           "schema":"structural.ala_independent_positive_location_result.v1_194",
           "status":"STOP_NO_EXTERNAL_POSITIVE_SCORING_INSUFFICIENT_SUPPORT_NO_RESCUE",
           "support":support,"record_audit":record_audit,"scores_computed":False,
           "external_species_island_pairs_semantically_read":True,"original_heldout_labels_read":0,
           "model_refit":False,"independently_surveyed_absences":False,"eBird_used":False
        }

    actual=read_predictions(actual_file,ACTUAL_MAGIC,(4126,529,2))
    nulls=read_predictions(null_file,NULL_MAGIC,(20,4126,529))
    scores=[];d1=[];d2=[]
    for nm in sorted(byspecies):
        j=jmap[nm]
        positive_pos=sorted(pool_position[iid] for iid in byspecies[nm])
        v=normalized_score(actual[rows_all,j,0],actual[rows_all,j,1],nulls[:,rows_all,j],positive_pos)
        scores.append({"species":species[j]["species_name"],"n_positive_islands":len(positive_pos),
                       "P1_C_minus_R3":v[0],"P2_C_minus_mean_rewired":v[1]})
        d1.append(v[0]);d2.append(v[1])
    arr=np.asarray([d1,d2],dtype=float)
    if not np.all(np.isfinite(arr)):raise Stop("nonfinite external normalized losses")
    n=len(scores);rng=np.random.default_rng(contract["uncertainty"]["bootstrap_seed"])
    if contract["uncertainty"]["bootstrap_replicates"]!=10000 or n!=support["species"]:
        raise Stop("bootstrap or species count drift")
    boot=np.empty((10000,2),dtype=float)
    for b in range(10000):
        idx=rng.integers(0,n,n)
        boot[b]=arr[:,idx].mean(axis=1)
    p1=float(arr[0].mean());p2=float(arr[1].mean())
    ci1=np.quantile(boot[:,0],[.025,.975],method="linear").tolist()
    ci2=np.quantile(boot[:,1],[.025,.975],method="linear").tolist()
    primary=bool(p1<0 and ci1[1]<0);topo=bool(p2<0 and ci2[1]<0)
    return scores,{
      "schema":"structural.ala_independent_positive_location_result.v1_194",
      "status":"EXTERNAL_POSITIVE_ONLY_CONDITIONAL_LOCATION_SCORED",
      "support":support,"record_audit":record_audit,
      "P1_mean_species_C_minus_R3":p1,"P1_species_bootstrap_ci95":ci1,"P1_supported":primary,
      "P2_mean_species_C_minus_rewired":p2,"P2_species_bootstrap_ci95":ci2,"P2_supported":topo,
      "joint_positive_location_support":bool(primary and topo),
      "scores_computed":True,"score_is_conditional_positive_location_only":True,
      "no_absence_discrimination_claim":True,"site_native_on_each_island_verified":False,
      "external_species_island_pairs_semantically_read":True,
      "original_heldout_labels_read":0,"model_refit":False,
      "independently_surveyed_absences":False,"movement_or_colonization_established":False,
      "eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    for label in ("ALA_zip","taxon_manifest","taxon_screen_receipt","eligibility_table",
                  "geometry_receipt","crosswalk","species_universe","entity_order",
                  "actual_predictions","rewired_predictions"):
        ap.add_argument(label,type=Path)
    ap.add_argument("--contract",type=Path,default=Path("development/global_mammals_ala_positive_location_protocol_v1_194.json"))
    ap.add_argument("--request",type=Path,required=True)
    ap.add_argument("--species-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        contract=json.loads(a.contract.read_text());request=json.loads(a.request.read_text())
        scored,receipt=analyze(contract,request,a.ALA_zip,a.taxon_manifest,a.taxon_screen_receipt,a.eligibility_table,
                               a.geometry_receipt,a.crosswalk,a.species_universe,a.entity_order,a.actual_predictions,a.rewired_predictions)
        if scored:
            a.species_output.parent.mkdir(parents=True,exist_ok=True)
            with a.species_output.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["species","n_positive_islands","P1_C_minus_R3","P2_C_minus_mean_rewired"],lineterminator="\n")
                w.writeheader();w.writerows(scored)
            receipt["species_table_sha256"]=sha(a.species_output)
        code=0 if receipt["status"]=="EXTERNAL_POSITIVE_ONLY_CONDITIONAL_LOCATION_SCORED" else 2
    except (Stop,KeyError,ValueError,OSError,RuntimeError,json.JSONDecodeError,zipfile.BadZipFile) as e:
        receipt={"schema":"structural.ala_independent_positive_location_result.v1_194",
                 "status":"STOP_ALA_EXTERNAL_PAIR_SCHEMA_OR_FROZEN_INPUT_DRIFT","reason":str(e),
                 "scores_computed":False,"original_heldout_labels_read":0,"model_refit":False,"eBird_used":False}
        code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
