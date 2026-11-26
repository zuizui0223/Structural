#!/usr/bin/env python3
"""Pilis one frozen conditional recorded-community contrast. No author R execution."""
import argparse,csv,io,json,math,hashlib,re,collections,urllib.error
from pathlib import Path
from pilis2022_pinned_csv_routing_method_audit import PINS
from pilis2022_fp2b8_full_community_source import ROOT,NODE,metadata,public_file,Stop,req
from pilis2022_fp2b8_folder_role_audit import FOLDER,TITLE,crawl,license_info
TABLE="60a7550e8a5d3d003a0d045e"
CODE="60a7550e0b6c6900459ba890"
GROUPS=("C","CC","G","P","R")
YEARS=tuple(range(2014,2019))

def method_gate(raw):
    # Trace simple direct use of exact [,4:52] in a species-composition
    # calculation, or assignment of that slice to a variable later passed
    # to such a calculation. Conservative static recognition, not R evaluation.
    s=raw.decode("utf-8-sig",errors="strict")
    s="\n".join(line.split("#",1)[0] for line in s.splitlines())
    req("pilis-carabids-2014-18.csv" in s,"AUTHOR_TABLE_REFERENCE_MISSING")
    fun=r"(?:rda|prcomp|princomp|pca|adonis2?|renyi|vegdist|decostand|diversity|specnumber)"
    slice_pat=r"\[\s*[^\]\n]*?,\s*4\s*:\s*52\s*\]"
    lines=s.splitlines();direct=[];assigned=[]
    for i,line in enumerate(lines):
        # Single expression or one continued line, avoiding arbitrary
        # numerical-range mentions elsewhere in the script.
        text=line
        if re.search(fun+r"\s*\([^)]*$",line,re.I) and i+1<len(lines):text+=" "+lines[i+1]
        m=re.search(r"\b"+fun+r"\s*\(",text,re.I)
        if m and re.search(slice_pat,text[m.end():]):direct.append(i+1)
        m=re.match(r"\s*([A-Za-z][A-Za-z0-9._]*)\s*(?:<-|=)\s*(.*)",line)
        if m and re.search(slice_pat,m.group(2)):
            var=m.group(1);tail="\n".join(lines[i+1:])
            if re.search(r"\b"+fun+r"\s*\([^\n;]*?(?<![A-Za-z0-9._])"+re.escape(var)+r"(?![A-Za-z0-9._])",tail,re.I):
                assigned.append(i+1)
    return {"direct_composition_slice_line_numbers":direct,"assigned_slice_used_in_composition_line_numbers":assigned,"exact_role_supported":bool(direct or assigned)}

def read_source(raw,method):
    # The original hashes are authenticated by load_pinned before this call.
    req(method["exact_role_supported"],"AUTHOR_49_TAXON_SLICE_ROLE_NOT_ESTABLISHED")
    r=csv.reader(io.StringIO(raw.decode("utf-8-sig",errors="strict"),newline=""),delimiter=";")
    h=next(r,[])
    req(len(h)==62 and h[:3]==["year","block","treatment"] and all(x.strip() for x in h) and len(set(h))==62,"EXACT_AUTHOR_HEADER_DRIFT")
    taxa=h[3:52];req(len(taxa)==49 and len(set(taxa))==49,"TAXON_AXIS_DRIFT")
    data={}
    counts=[0]*49
    total=0
    n=0
    for row in r:
        n+=1
        req(len(row)==62,"ROW_WIDTH_DRIFT")
        y,b,t=(x.strip() for x in row[:3])
        req(y in tuple(map(str,YEARS)) and b and b.casefold() not in {"na","nan","none","null"} and t in GROUPS,"AUTHOR_ROUTING_DRIFT")
        k=(b,t,int(y))
        req(k not in data,"DUPLICATE_PLOT_YEAR")
        vals=[]
        for j,v in enumerate(row[3:52]):
            v=v.strip()
            req(re.fullmatch(r"[0-9]+(?:\.0+)?",v) is not None,"NONINTEGER_OR_MISSING_SPECIES_CELL")
            x=int(v.split(".")[0]);counts[j]+=x;total+=x;vals.append(x>0)
        rich=sum(vals);req(rich>0,"OBSERVED_EMPTY_COMMUNITY_STRICT_STOP")
        data[k]=[float(x)/math.sqrt(rich) for x in vals]
    blocks=sorted({k[0] for k in data})
    req(n==150 and len(blocks)==6 and set(data)=={(b,t,y) for b in blocks for t in GROUPS for y in YEARS},"FROZEN_150_CONTEXT_FRAME_DRIFT")
    req(all(x>0 for x in counts) and total==21352,"SOURCE_TAXON_COVERAGE_OR_PUBLISHED_TOTAL_MISMATCH")
    return data,blocks,{"rows":n,"observed_nonempty_contexts":len(data),"blocks":len(blocks),"documented_plot_keys":30,"species_columns":49,"all_species_detected":True,"total_individuals":total}

def components(ds):
    n=len(ds)
    req(n==6 and all(len(x)==49 for x in ds),"FROZEN_SIX_PLOT_AXIS")
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    T=sum(dot(x,x) for x in ds)/n
    U=sum(dot(ds[i],ds[j]) for i in range(n) for j in range(n) if i!=j)/(n*(n-1))
    M=sum((sum(x[j] for x in ds)/n)**2 for j in range(49))
    req(abs(M-(T+(n-1)*U)/n)<1e-12,"CENTROID_IDENTITY_FAIL")
    return {"T":T,"U":U,"M":M}
def score(data,blocks):
    out={}
    for t in ("C","CC"):
        ds=[[v-u for u,v in zip(data[(b,t,2015)],data[(b,t,2016)])] for b in blocks]
        out[t]=components(ds)
    diff={k:out["CC"][k]-out["C"][k] for k in ("T","U","M")}
    return {"groups":out,"CC_minus_C":diff,"joint_directional_match":diff["T"]>0 and diff["U"]<0}
def load_pinned():
    q,_=metadata(ROOT+"/");node=q["data"]
    req(node.get("id")==NODE and node.get("type")=="nodes" and node.get("attributes",{}).get("public") is True and node["attributes"].get("title")==TITLE,"NODE_DRIFT")
    req(license_info(node)["name"]=="GNU General Public License (GPL) 3.0","LICENSE_DRIFT")
    root,_=metadata(ROOT+"/files/osfstorage/");arr=root.get("data",[])
    req(len(arr)==1 and arr[0].get("id")==FOLDER and not root.get("links",{}).get("next"),"ROOT_DRIFT")
    files,_=crawl(arr[0]);d={x["id"]:x for x in files}
    req(len(files)==14 and len(d)==14 and {TABLE,CODE}<=set(d),"ARCHIVE_ROSTER_DRIFT")
    out={}
    for i in (CODE,TABLE):
        name,size,sha=PINS[i];f=d[i]
        req(f["name"]==name and f["size"]==size and f["published_hashes"].get("sha256")==sha,"PINNED_METADATA_DRIFT")
        raw,_=public_file(f);req(len(raw)==size and hashlib.sha256(raw).hexdigest()==sha,"PINNED_BYTES_DRIFT")
        out[i]=raw
    return out
def test():
    assert method_gate(b'a <- read.csv("pilis-carabids-2014-18.csv")\np <- rda(sqrt(a[,4:52]))')["exact_role_supported"]
    assert method_gate(b'a <- read.csv("pilis-carabids-2014-18.csv")\nx <- a[,4:52]\np <- rda(x)')["exact_role_supported"]
    assert not method_gate(b'a <- read.csv("pilis-carabids-2014-18.csv")\nz <- 4:52')["exact_role_supported"]
    x=[1.,-1.]+[0.]*47
    a=components([x]*3+[[-v for v in x]]*3)
    assert abs(a["T"]-2)<1e-12 and abs(a["U"]+.4)<1e-12 and a["M"]==0
    print("PILIS_EXACT_ROLE_AND_CHANGE_COMPONENT_SYNTHETIC_PASS")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--test",action="store_true");ap.add_argument("--out",default="pilis_onepass/receipt.json");a=ap.parse_args();test()
    if a.test:return
    o={"schema":"structural.pilis2022.observed_community_onepass.v1","source_raw_exported":False,"original_author_code_executed":False,
       "actual_trap_effort_verified":False,"strict_effort_gate_passed":False,"population_p_value":None,"population_ci":None,"primary":None,"source_response_interpretation_attempted":False}
    try:
        raw=load_pinned();o["two_original_sha256_verified"]=True
        roles=method_gate(raw[CODE]);o["author_slice_method_evidence"]=roles
        req(roles["exact_role_supported"],"AUTHOR_49_TAXON_SLICE_ROLE_NOT_ESTABLISHED")
        o["source_response_interpretation_attempted"]=True
        data,blocks,frame=read_source(raw[TABLE],roles);o["source_frame"]=frame
        o["primary"]=score(data,blocks)
        o["status"]="FROZEN_CONDITIONAL_OBSERVED_COMMUNITY_SCORE_COMPLETE"
    except urllib.error.HTTPError as e:o.update(status="SOURCE_HTTP_STOP",http=e.code)
    except Stop as e:o.update(status="SOURCE_OR_SCHEMA_STOP",reason=str(e))
    except Exception as e:o.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,sort_keys=True,indent=2)+"\n");print(json.dumps(o,sort_keys=True))
if __name__=="__main__":main()
