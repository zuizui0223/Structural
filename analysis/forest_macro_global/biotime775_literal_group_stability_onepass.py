#!/usr/bin/env python3
"""One frozen Jari literal code-group descriptive contrast.
Habitat crosswalk is NOT author-verified. No raw source rows exported.
"""
import argparse,csv,io,math,hashlib,json,collections,datetime,re,itertools,urllib.error
from pathlib import Path
from biotime_v4_forest_beetle_study_routing import fetch
from biotime458_salvage_temporal_alignment_onepass import metric,vec

URL="https://biotime.st-andrews.ac.uk/dl_request.php?dl=rawdata&study=775"
SHA="0223c9897f86c7c9d93a000fb6a38f1b932063ec642c5585c126a3a27cdc2ca6"
YEARS=tuple(range(2009,2014))
GROUPS={"F":12,"C":8,"E":15}
class Stop(ValueError):pass
def req(ok,msg):
    if not ok:raise Stop(msg)

def source(raw):
    req(len(raw)==212570 and hashlib.sha256(raw).hexdigest()==SHA,"PINNED_LIVE_BYTES_DRIFT")
    r=csv.DictReader(io.StringIO(raw.decode("utf-8-sig",errors="strict"),newline=""))
    h=r.fieldnames or []
    req(len(h)==9 and len(set(h))==9 and {"ABUNDANCE","valid_name","SAMPLE_DESC","LATITUDE","LONGITUDE","DAY","MONTH","YEAR"}.issubset(h),"HEADER_DRIFT")
    routing=[]; coords={}; dates={}; keys=collections.defaultdict(set)
    for row in r:
        req(None not in row and all(v is not None for v in row.values()),"ROW_WIDTH_DRIFT")
        p=row["SAMPLE_DESC"].strip().rsplit("_",3)
        req(len(p)==4 and all(p),"DESCRIPTOR_DRIFT")
        k=p[0];m=re.fullmatch(r"([FCE])[ _-]?(\d+)",k)
        req(m is not None,"LITERAL_GROUP_GRAMMAR_DRIFT")
        g=m.group(1)
        req(all(re.fullmatch(r"\d+",v) for v in p[1:]),"DESCRIPTOR_DATE_GRAMMAR")
        day,month,y=map(int,p[1:])
        req(y in YEARS,"YEAR_DRIFT")
        datetime.date(y,month,day)
        req(all(int(row[f])==v for f,v in (("YEAR",y),("MONTH",month),("DAY",day))),"DATE_CONFLICT")
        xy=(float(row["LATITUDE"]),float(row["LONGITUDE"]))
        req(all(map(math.isfinite,xy)) and -90<=xy[0]<=90 and -180<=xy[1]<=180,"COORDINATE_INVALID")
        req(k not in coords or coords[k]==xy,"SITE_COORDINATE_CONFLICT")
        coords[k]=xy;keys[g].add(k)
        idx=(g,k,y)
        req(idx not in dates or dates[idx]==(month,day),"DUPLICATE_ANNUAL_EVENT")
        dates[idx]=(month,day)
        routing.append((idx,row))
    req(len(routing)==2745 and len(coords)==35 and len(dates)==175,"RECORD_FRAME_DRIFT")
    req({g:len(v) for g,v in keys.items()}==GROUPS,"GROUP_SIZE_DRIFT")
    req(set(dates)=={(g,k,y) for g,ks in keys.items() for k in ks for y in YEARS},"COMPLETE_ANNUAL_FRAME_DRIFT")
    # Only after original method frame passed, interpret the two response fields.
    comm=collections.defaultdict(set);taxa=set();zero=0
    for idx,row in routing:
        name=row["valid_name"].strip()
        req(bool(name) and name.casefold() not in {"na","nan","none","null","n/a"},"MISSING_TAXON")
        x=float(row["ABUNDANCE"])
        req(math.isfinite(x) and x>=0 and x.is_integer(),"INVALID_ABUNDANCE")
        taxa.add(name);a=comm[idx]
        if x>0:a.add(name)
        else:zero+=1
    req(len(taxa)==64 and set(comm)==set(dates) and all(comm.values()),"TAXON_OR_EMPTY_COMMUNITY_DRIFT")
    return comm,keys,sorted(taxa),{"source_records":len(routing),"site_years":len(comm),"site_keys":len(coords),"taxon_labels":len(taxa),"zero_rows":zero,"literal_group_sizes":GROUPS}

def enrich(q):
    q=dict(q)
    q["centroid_shift_squared"]=q["mean_same_site_squared_distance"]-q["spatial_variance_prior"]-q["spatial_variance_next"]+2*q["centered_covariance"]
    req(q["centroid_shift_squared"]>=-1e-10,"DECOMPOSITION_NEGATIVE")
    q["centroid_shift_squared"]=max(0,q["centroid_shift_squared"])
    return q

def full(a,b):
    return enrich(metric(a,b))

def balanced(a,b,n=8):
    # Exhaustive fixed matched subset diagnostic (not resampling inference).
    sums=collections.Counter();count=undefined=0
    for ix in itertools.combinations(range(len(a)),n):
        v=full([a[i] for i in ix],[b[i] for i in ix])
        count+=1
        for k,x in v.items():
            if x is None:
                req(k=="alignment","UNEXPECTED_NULL_METRIC")
                undefined+=1
            else:sums[k]+=x
    req(count==math.comb(len(a),n) and count>0,"BALANCED_SUBSET_COUNT")
    avg={k:s/count for k,s in sums.items()}
    if undefined:avg["alignment"]=None
    return {"subsets":count,"undefined_alignment_subsets":undefined,"metrics":avg}

MAIN=("alignment","mean_same_site_squared_distance","centroid_shift_squared")
def contrasts(x,y):
    return {k:x[k]-y[k] if x.get(k) is not None and y.get(k) is not None else None for k in MAIN}

def means(rows,name):
    out={}
    for k in MAIN:
        v=[row[name][k] for row in rows]
        out[k]=sum(v)/len(v) if all(x is not None for x in v) else None
    return out

def signature(x):
    if any(x[k] is None for k in MAIN):return "UNDEFINED_STOP"
    return "ALL_THREE_DIRECTIONAL_SIGNS_MATCH_GERMAN_DESCRIPTIVE_PATTERN" if x[MAIN[0]]>0 and x[MAIN[1]]>0 and x[MAIN[2]]<0 else "JOINT_DIRECTIONAL_PATTERN_NOT_MATCHED"

def score(comm,keys,taxa):
    rows=[]
    for y in YEARS[:-1]:
        row={"start_year":y,"end_year":y+1,"full":{},"balanced8":{}}
        for g in GROUPS:
            ks=sorted(keys[g]);a=[vec(comm[(g,k,y)],taxa) for k in ks];b=[vec(comm[(g,k,y+1)],taxa) for k in ks]
            row["full"][g]=full(a,b)
            row["balanced8"][g]=balanced(a,b)
        row["full_E_minus_F"]=contrasts(row["full"]["E"],row["full"]["F"])
        row["balanced8_E_minus_F"]=contrasts(row["balanced8"]["E"]["metrics"],row["balanced8"]["F"]["metrics"])
        rows.append(row)
    primary=means(rows,"full_E_minus_F");sensitivity=means(rows,"balanced8_E_minus_F")
    # Full cohort requires ALL six? Here 3 groups x 4 pairs = 12 alignments.
    defined=all(q["alignment"] is not None for row in rows for q in row["full"].values())
    if not defined:primary=None
    return rows,primary,sensitivity

def test():
    z=1/math.sqrt(2)
    a=[[z,z,0,0,0],[z,0,z,0,0],[z,0,0,z,0]]
    b=[[0,x[1],x[2],x[3],z] for x in a]
    q=full(a,b);req(abs(q["alignment"]-1)<1e-12 and abs(q["centroid_shift_squared"]-1)<1e-12,"SYNTH_COMMON_SHIFT")
    x=balanced(a,b,2)
    req(x["subsets"]==3 and x["undefined_alignment_subsets"]==0 and abs(x["metrics"]["alignment"]-1)<1e-12,"SYNTH_BALANCED")
    y=balanced(a,[a[0]]*3,2)
    req(y["undefined_alignment_subsets"]==3 and y["metrics"]["alignment"] is None,"SYNTH_UNDEFINED")
    print("BIOTIME775_LITERAL_GROUP_AND_BALANCED_SUBSET_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="biotime775_onepass/receipt.json");a=p.parse_args();test()
    if a.test:return
    o={"schema":"structural.biotime775.literal_codegroup_spatial_stability.v1","source_sha256":SHA,"habitat_crosswalk_author_verified":False,"raw_rows_exported":False,"population_p_value":None,"population_ci":None,"primary_E_minus_F":None,"source_response_scoring_attempted":False}
    try:
        raw=fetch(URL,"biotime.st-andrews.ac.uk",212570)
        o["source_response_scoring_attempted"]=True
        comm,keys,taxa,info=source(raw);o["source_frame"]=info
        rows,primary,sensitivity=score(comm,keys,taxa)
        o.update(year_pairs=rows,primary_E_minus_F=primary,balanced8_E_minus_F=sensitivity,
                 primary_joint_pattern=signature(primary) if primary is not None else "UNDEFINED_STOP",balanced8_joint_pattern=signature(sensitivity))
        o["status"]="FROZEN_LITERAL_GROUP_DESCRIPTIVE_SCORE_COMPLETE" if primary is not None else "FROZEN_ALIGNMENT_UNDEFINED_STOP"
    except urllib.error.HTTPError as e:o.update(status="SOURCE_HTTP_STOP",http=e.code)
    except Stop as e:o.update(status="SOURCE_OR_SCHEMA_STOP",reason=str(e))
    except Exception as e:o.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print(json.dumps(o,sort_keys=True))
if __name__=="__main__":main()
