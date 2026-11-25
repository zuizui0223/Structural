#!/usr/bin/env python3
"""One frozen BioTIME 458 descriptive contrast. No raw values exported."""
import argparse,csv,io,math,hashlib,json,collections,urllib.error
from pathlib import Path
from biotime_v4_forest_beetle_study_routing import fetch

URL="https://biotime.st-andrews.ac.uk/dl_request.php?dl=rawdata&study=458"
SHA="a39c4a3af2ede728c15ada47fa81f235dff619b6108526d06acb819265dbb005"
YEARS=tuple(range(2008,2012))
GROUPS=("logged","unlogged")
class Stop(ValueError):pass
def req(x,m):
    if not x:raise Stop(m)

def read_source(raw):
    req(len(raw)==307442 and hashlib.sha256(raw).hexdigest()==SHA,"PINNED_LIVE_BYTES_DRIFT")
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig",errors="strict"),newline=""))
    h=reader.fieldnames or []
    fields={"ABUNDANCE","valid_name","SAMPLE_DESC","LATITUDE","LONGITUDE","YEAR"}
    req(len(h)==9 and len(set(h))==9 and fields.issubset(h),"FROZEN_HEADER_DRIFT")
    communities=collections.defaultdict(set); coords={}; tax=set();n=0
    n_zero=0
    for r in reader:
        n+=1
        req(None not in r and all(v is not None for v in r.values()),"ROW_WIDTH_DRIFT")
        s=r["SAMPLE_DESC"].strip().split("_")
        req(len(s)==4 and all(s),"DESCRIPTOR_GRAMMAR_DRIFT")
        t=s[0].casefold();req(t in GROUPS,"TREATMENT_DRIFT")
        req(s[3].isdigit() and r["YEAR"].strip()==s[3],"YEAR_CONFLICT")
        y=int(s[3]);req(y in YEARS,"YEAR_DRIFT")
        key=(s[1],s[2]);p=(t,key)
        try: xy=(float(r["LATITUDE"]),float(r["LONGITUDE"]))
        except ValueError:raise Stop("COORDINATE_INVALID")
        req(all(map(math.isfinite,xy)) and -90<=xy[0]<=90 and -180<=xy[1]<=180,"COORDINATE_INVALID")
        req(p not in coords or coords[p]==xy,"SITE_COORDINATE_CONFLICT")
        coords[p]=xy
        name=r["valid_name"].strip()
        req(bool(name) and name.casefold() not in {"na","nan","null","none","n/a"},"TAXON_MISSING")
        try:c=float(r["ABUNDANCE"])
        except ValueError:raise Stop("INVALID_ABUNDANCE")
        req(math.isfinite(c) and c>=0 and c.is_integer(),"INVALID_ABUNDANCE")
        tax.add(name);a=communities[(t,key,y)]
        if c>0:a.add(name)
        else:n_zero+=1
    req(n==4304 and len(tax)==179,"FROZEN_RECORD_OR_TAXON_COUNT_DRIFT")
    sets={g:{key for t,key in coords if t==g} for g in GROUPS}
    req(all(len(v)==22 for v in sets.values()) and not (sets["logged"]&sets["unlogged"]),"PHYSICAL_CANDIDATE_KEY_DRIFT")
    req(set(communities)=={(g,k,y) for g in GROUPS for k in sets[g] for y in YEARS},"COMPLETE_176_FRAME_DRIFT")
    req(all(communities.values()),"RECORDED_EMPTY_COMMUNITY_STOP")
    return communities,sets,sorted(tax),{"records":n,"taxon_labels":len(tax),"site_keys":len(coords),"site_years":len(communities),"zero_count_rows":n_zero}

def metric(a,b):
    n=len(a);p=len(a[0])
    req(n==len(b) and n>=2 and p>0 and all(len(x)==p for x in a+b),"MATRIX_SHAPE")
    m=[sum(x[j] for x in a)/n for j in range(p)]
    q=[sum(x[j] for x in b)/n for j in range(p)]
    s0=s1=c=d=0.0
    for x,y in zip(a,b):
        for j in range(p):
            u=x[j]-m[j];v=y[j]-q[j]
            s0+=u*u;s1+=v*v;c+=u*v;d+=(x[j]-y[j])**2
    v0=s0/n;v1=s1/n
    return {"alignment":c/math.sqrt(s0*s1) if min(v0,v1)>1e-12 else None,
            "spatial_variance_prior":v0,"spatial_variance_next":v1,"centered_covariance":c/n,
            "mean_same_site_squared_distance":d/n}

def vec(s,taxa):
    z=1/math.sqrt(len(s))
    return [z if x in s else 0.0 for x in taxa]

def score(communities,sets,taxa):
    rows=[]
    for y in YEARS[:-1]:
        pair={"start_year":y,"end_year":y+1}
        for g in GROUPS:
            keys=sorted(sets[g])
            pair[g]=metric([vec(communities[(g,k,y)],taxa) for k in keys],
                           [vec(communities[(g,k,y+1)],taxa) for k in keys])
        a=pair["logged"]["alignment"];b=pair["unlogged"]["alignment"]
        pair["logged_minus_unlogged"]=a-b if a is not None and b is not None else None
        rows.append(pair)
    return rows

def test():
    z=1/math.sqrt(2)
    a=[[z,z,0,0,0],[z,0,z,0,0],[z,0,0,z,0]]
    shift=[[0,r[1],r[2],r[3],z] for r in a]
    perm=[a[1],a[2],a[0]]
    req(abs(metric(a,shift)["alignment"]-1)<1e-12,"SYNTH_SHIFT")
    req(abs(metric(a,perm)["alignment"]+0.5)<1e-12,"SYNTH_PERMUTE")
    req(metric(a,[a[0]]*3)["alignment"] is None,"SYNTH_COLLAPSE")
    req(abs(metric(a,shift)["mean_same_site_squared_distance"]-metric(a,perm)["mean_same_site_squared_distance"])<1e-12,"SYNTH_DISTANCE")
    print("BIOTIME458_FROZEN_ALIGNMENT_SYNTHETIC_PASS")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--test",action="store_true");ap.add_argument("--out",default="biotime458_onepass/receipt.json");a=ap.parse_args();test()
    if a.test:return
    r={"schema":"structural.biotime458.salvage_temporal_alignment.v1","source_sha256":SHA,"raw_data_exported":False,
       "inference":"descriptive_single_source_no_independent_treatment_replication","population_p_value":None,"population_ci":None,
       "primary_estimate":None,"source_response_scoring_attempted":False}
    try:
        raw=fetch(URL,"biotime.st-andrews.ac.uk",307442)
        r["source_response_scoring_attempted"]=True
        community,sets,taxa,counts=read_source(raw)
        r["source_frame"]=counts
        r["year_pairs"]=score(community,sets,taxa)
        vals=[x["logged_minus_unlogged"] for x in r["year_pairs"]]
        if any(x is None for x in vals):r["status"]="FROZEN_ALIGNMENT_UNDEFINED_STOP"
        else:
            r["primary_estimate"]=sum(vals)/3
            r["status"]="FROZEN_DESCRIPTIVE_WITHIN_FOREST_SCORE_COMPLETE"
    except urllib.error.HTTPError as e:r.update(status="SOURCE_HTTP_STOP",http=e.code)
    except Stop as e:r.update(status="SOURCE_OR_RESPONSE_SCHEMA_STOP",reason=str(e))
    except Exception as e:r.update(status="SOURCE_EXECUTION_STOP",error_class=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
