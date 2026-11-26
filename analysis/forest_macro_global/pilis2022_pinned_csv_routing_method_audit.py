#!/usr/bin/env python3
"""Pinned Pilis original GPLv3 archive: method and routing diagnosis only.

Read author CSV headers and exact generic routing fields, not organism
counts. Static author-code role inspection, never execution or republication.
No row-level site identities, taxon names, or original code exported.
"""
import argparse,collections,csv,hashlib,io,json,re,urllib.error
from pathlib import Path
from pilis2022_fp2b8_full_community_source import ROOT,NODE,metadata,public_file,req,Stop
from pilis2022_fp2b8_folder_role_audit import FOLDER,TITLE,crawl,license_info,csv_header

PINS={
    "60a7550e8a5d3d003a0d045e":("pilis-carabids-2014-18.csv",22800,"c5ac3e1ba8011d544284c19ac90934dec1a08679fa1b155bbbf6b6678d475a88"),
    "60a758e30b6c6900449ba3d1":("carabids-nmds-2014-18.csv",17939,"23e5e733eff9f73d69c7db666f2a81e22b2671d922ddfbacfc33908d8977b2fd"),
    "60a7550e0b6c6900459ba890":("Renyi_and_PCA-17-04-2020.R",7580,"7913d5dac8dfa3cc67fdd6e91243bc04205449e6fed7c81748974d49587a20de"),
    "60a755d70b6c6900449b9b2f":("GLMM-20-05-2021.R",5817,"93411da8d416d8edb9101daa6332a48b1bc46e1e29f1128f4d2b9d31c74dc382"),
    "60a758e00b6c6900459bb953":("Pilis-IndVal-overview-14-18-13-01-2019.r",1647,"98a464173cd5f2d47fca4e6b89509b26f8200f69afeee44df78eb641692b0bc1"),
}
DUP_ID="60a755da8a5d3d00410cb59b"
ROLE={
    "block":{"block","blockid","blockcode","rep","replicate","replication","replicateid"},
    "treatment":{"treatment","treat","trt","treatmentcode","management"},
    "year":{"year","samplingyear","surveyyear"},
    "plot":{"plot","plotid","plotcode","site","siteid","stand","standid"},
    "sample":{"sample","sampleid","samplecode","sampledesc"},
    "date":{"date","samplingdate","surveydate","month","season","session","period","samplingperiod","yearperiod"},
    "effort":{"effort","trapdays","trapday","trapid","trap","numberoftraps","ntraps","trapnumber"}
}
def norm(v):return re.sub(r"[^a-z0-9]","",str(v or "").casefold())
def token(v):return str(v or "").strip()
def valid(v):return token(v).casefold() not in {"","na","nan","none","null","n/a"}
def csv_rows(raw):
    text=raw.decode("utf-8-sig",errors="strict")
    first=text.splitlines()[0] if text else ""
    req(first and len(first)<=100000,"HEADER_LIMIT")
    # Count CSV delimiters using parser, not guessed names or row values.
    cand=[]
    for sep in (",",";","\t"):
        h=next(csv.reader([first],delimiter=sep))
        cand.append((len(h),sep,h))
    cand.sort(reverse=True,key=lambda v:v[0])
    width,sep,h=cand[0];req(width>=2 and width>cand[1][0],"HEADER_DELIMITER_AMBIGUOUS")
    req(len(set(x for x in h if x))==sum(bool(x) for x in h),"DUPLICATE_NONBLANK_HEADER")
    return csv.reader(io.StringIO(text,newline=""),delimiter=sep),h,sep
def grammar_shape(s):
    # No actual sample IDs emitted; retain only token shape. A literal treatment
    # or year is reported separately only in its named field.
    return re.sub(r"[A-Za-z]+","A",re.sub(r"[0-9]+","9",s))[:80]
def design_summary(records):
    by=collections.defaultdict(set);blocks=set();plots=collections.defaultdict(set);all_years=set();treats=collections.Counter()
    bad=collections.Counter();counts=collections.Counter()
    for r in records:
        b,t,y=(r[k] for k in ("block","treatment","year"))
        if not all(valid(x) for x in (b,t,y)):
            bad["missing_block_treatment_year"]+=1;continue
        if not re.fullmatch(r"20(?:14|15|16|17|18)",y):
            bad["year_outside_documented_range"]+=1;continue
        if t not in {"C","CC","G","P","R"}:
            bad["treatment_literal_not_author_codes"]+=1;continue
        y=int(y);by[(b,t)].add(y);counts[(b,t,y)]+=1
        all_years.add(y);blocks.add(b);treats[t]+=1
        if valid(r.get("plot","")):plots[(b,t)].add(r["plot"])
    return {"routing_rows":len(records),"invalid_rows":dict(bad),
      "distinct_block_tokens":len(blocks),"distinct_block_treatment_tokens":len(by),
      "distinct_block_treatment_year_contexts":len(counts),
      "duplicate_context_rows":sum(x-1 for x in counts.values()),
      "documented_treatment_row_counts":dict(sorted(treats.items())),
      "observed_years":sorted(all_years),
      "complete_2014_2018_block_treatment_tokens":sum(v==set(range(2014,2019)) for v in by.values()),
      "block_treatment_tokens_with_multiple_plot_labels":sum(len(v)>1 for v in plots.values()),
      "candidate_blocks_with_both_CC_C_2015_2016":sum(all({2015,2016}<=by.get((b,t),set()) for t in ("CC","C")) for b in blocks),
      "physical_plot_identity_and_effort_verified":False}
def table(raw):
    reader,h,sep=csv_rows(raw);req(next(reader)==h,"HEADER_READ_CONFLICT")
    role_index={role:[i for i,x in enumerate(h) if norm(x) in names] for role,names in ROLE.items()}
    matched={k:v for k,v in role_index.items() if v}
    report={"header_width":len(h),"delimiter":{",":"comma",";":"semicolon","\t":"tab"}[sep],
      "role_fields":{k:[{"index_1based":i+1,"literal":h[i]} for i in v] for k,v in matched.items()},
      "blank_header_positions":[i+1 for i,x in enumerate(h) if not x.strip()],
      "unclassified_header_count":len(h)-len({i for v in matched.values() for i in v})}
    # Candidate routing only. The leading column, if explicitly unnamed,
    # is a candidate row-label field, never assigned a biological role.
    idx={k:v[0] for k,v in matched.items() if len(v)==1}
    keyfields={k:i for k,i in idx.items() if k in {"block","treatment","year","plot","sample","date","effort"}}
    if not h[0].strip() and 0 not in keyfields.values():keyfields["unnamed_row_label"]=0
    profiles={k:collections.Counter() for k in keyfields}
    literal={k:collections.Counter() for k in ("year","treatment") if k in keyfields}
    data=[];n=0;blank=0
    for row in reader:
        n+=1;req(n<=50000 and len(row)==len(h),"TABLE_ROW_WIDTH_OR_LIMIT")
        if not row:blank+=1;continue
        r={k:token(row[i]) for k,i in keyfields.items()}
        for k,x in r.items():profiles[k][x]+=1
        for k in literal:
            v=r[k]
            if k=="year" and re.fullmatch(r"20(?:14|15|16|17|18)",v):literal[k][v]+=1
            elif k=="treatment" and v in {"C","CC","G","P","R"}:literal[k][v]+=1
            else:literal[k]["other_or_missing"]+=1
        if {"block","treatment","year"}<=set(r):data.append(r)
    report.update(rows=n,blank_rows=blank,
      routing_field_profiles={k:{"distinct_nonmissing":sum(valid(x) for x in c),"missing_rows":sum(v for x,v in c.items() if not valid(x)),"lexical_shapes":dict(sorted(collections.Counter({shape:sum(1 for x in c if valid(x) and grammar_shape(x)==shape) for shape in {grammar_shape(x) for x in c if valid(x)}}).items()))} for k,c in profiles.items()},
      documented_literal_counts={k:dict(v) for k,v in literal.items()},
      biological_values_interpreted=0)
    if data:report["direct_named_design_candidates"]=design_summary(data)
    return report,h
def code_roles(raw,headers):
    text=raw.decode("utf-8-sig",errors="strict")
    # Static inspection only. Preserve source file references and generic role
    # field mentions, and numeric column-range signatures, not source code.
    roles={name:sum(len(re.findall(r"(?<![A-Za-z0-9_])"+re.escape(field)+r"(?![A-Za-z0-9_])",text,re.I)) for field in fields) for name,fields in ROLE.items()}
    reads=[]
    for line_no,line in enumerate(text.splitlines(),1):
        if re.search(r"\b(read\.csv2?|read\.table|read_csv|read_delim)\s*\(",line,re.I):
            files=[name for name in headers if name in line]
            flags={k:m.group(1).strip("'\"") for k,pat in {
              "header":r"\bheader\s*=\s*(TRUE|FALSE|T|F)\b",
              "row_names":r"\brow\.names\s*=\s*(\d+|NULL|FALSE)\b",
              "sep":r"\bsep\s*=\s*(['\"][,;\\t]['\"])"}.items() if (m:=re.search(pat,line))}
            reads.append({"line":line_no,"catalog_file_references":files,"literal_read_options":flags})
    range_tokens=collections.Counter(re.findall(r"\b(\d+\s*:\s*\d+)\b",text))
    explicit_named={}
    for name,hh in headers.items():
        explicit_named[name]=sorted({x for x in hh if any(norm(x) in v for v in ROLE.values()) and re.search(r"(?<![A-Za-z0-9_])"+re.escape(x)+r"(?![A-Za-z0-9_])",text)})
    return {"line_count":len(text.splitlines()),"role_mention_counts":roles,
      "known_file_references":[x for x in headers if x in text],
      "literal_table_reads":reads,"generic_field_mentions":explicit_named,
      "numeric_range_token_counts":dict(sorted(range_tokens.items())),
      "original_code_executed":False}
def test():
    raw=b"block,treatment,year,plot,SpeciesX\nB1,C,2015,X,NOT_READ\nB1,C,2016,X,NOT_READ\nB1,CC,2015,Y,NOT_READ\nB1,CC,2016,Y,NOT_READ\n"
    r,h=table(raw)
    assert r["direct_named_design_candidates"]["candidate_blocks_with_both_CC_C_2015_2016"]==1
    assert r["unclassified_header_count"]==1 and r["rows"]==4
    assert "SpeciesX" not in json.dumps(r) and "NOT_READ" not in json.dumps(r)
    q=code_roles(b'a <- read.csv("x.csv", header=TRUE, row.names=1)\n',{"x.csv":h})
    assert q["literal_table_reads"][0]["literal_read_options"]["row_names"]=="1"
    print("PILIS_PINNED_ROUTING_METHOD_SYNTHETIC_PASS")
def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="pilis_pinned_routing/receipt.json");a=p.parse_args();test()
    if a.test:return
    o={"schema":"structural.pilis_fp2b8.pinned_routing.v1","original_response_values_interpreted":0,"new_ecological_effects_scored":0,"raw_source_exported":False,"original_author_code_executed":False,"tables":{},"methods":{}}
    try:
        q,_=metadata(ROOT+"/");node=q["data"]
        req(node.get("id")==NODE and node.get("type")=="nodes" and node.get("attributes",{}).get("public") is True and node["attributes"].get("title")==TITLE,"NODE_DRIFT")
        # Exact GPLv3 public license confirmed in prior receipt and reviewed.
        lic=license_info(node)
        req(lic["name"]=="GNU General Public License (GPL) 3.0","EXACT_LICENSE_DRIFT")
        o["public_project_license"]=lic["name"]
        root,_=metadata(ROOT+"/files/osfstorage/")
        arr=root.get("data",[]);req(len(arr)==1 and arr[0].get("id")==FOLDER and not root.get("links",{}).get("next"),"ROOT_DRIFT")
        files,_=crawl(arr[0]);d={x["id"]:x for x in files}
        req(len(files)==14 and len(d)==14 and set(PINS)<=set(d),"PINNED_ROSTER_DRIFT")
        for i,(n,size,sha) in PINS.items():
            f=d[i]
            req(f["name"]==n and f["size"]==size and f["published_hashes"].get("sha256")==sha,"PINNED_FILE_METADATA_DRIFT")
        orig=d["60a7550e8a5d3d003a0d045e"];dup=d.get(DUP_ID,{})
        req(dup.get("published_hashes",{}).get("sha256")==orig["published_hashes"]["sha256"] and dup.get("size")==orig["size"],"DUPLICATE_COPY_MANIFEST_DRIFT")
        o["duplicate_csv_publisher_digest_identical"]=True
        raw={}
        for i,(n,size,sha) in PINS.items():
            b,verified=public_file(d[i])
            req(len(b)==size and hashlib.sha256(b).hexdigest()==sha,"SOURCE_PINNED_BYTES_DRIFT")
            raw[n]=b
        o["five_pinned_file_hashes_verified"]=True
        headers={}
        for name,b in raw.items():
            if name.casefold().endswith(".csv"):
                q,h=table(b);o["tables"][name]=q;headers[name]=h
        for name,b in raw.items():
            if name.casefold().endswith(".r"):o["methods"][name]=code_roles(b,headers)
        o["status"]="PINNED_SOURCE_ROUTING_AND_STATIC_METHOD_DIAGNOSTIC_COMPLETE"
    except urllib.error.HTTPError as e:o.update(status="SOURCE_HTTP_STOP",http=e.code)
    except Stop as e:o.update(status="SOURCE_SCHEMA_STOP",reason=str(e))
    except Exception as e:o.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n");print(json.dumps(o,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
