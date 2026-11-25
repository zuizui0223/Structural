#!/usr/bin/env python3
"""Pinned Estonia repeated-stand and EMEND file-admission checks.
Read author-defined routing fields only. XLSX shared strings may be
deserialized, but taxon/abundance fields are not interpreted or exported.
No biological scores. Never retry a denied original file route.
"""
import argparse,csv,io,json,re,hashlib,collections,urllib.parse,urllib.error
from pathlib import Path
import openpyxl
from boreal_temporal_independent_source_design import est_file, get, dryad_meta, href, Stop, require

def token(v):
    if v is None:return ""
    if isinstance(v,float) and v.is_integer():return str(int(v))
    return str(v).strip()

def valid(v):
    return token(v).casefold() not in {"","na","n/a","nan","none","null"}

def year(v):
    x=token(v)
    require(re.fullmatch(r"20[0-2][0-9]",x) is not None and 2005<=int(x)<=2025,"EST_YEAR_VALUE_STOP")
    return int(x)

def selected_rows(ws,names):
    rows=ws.iter_rows(values_only=True)
    h=[token(x) for x in next(rows,())]
    require(all(h.count(x)==1 for x in names),"AUTHOR_ROUTING_HEADER_MISSING_OR_DUPLICATED")
    indices=[h.index(x) for x in names]
    for i,row in enumerate(rows,2):
        require(i<=400000,"SOURCE_ROW_LIMIT")
        values=[row[j] if j<len(row) else None for j in indices]
        if not any(valid(v) for v in values):continue
        yield dict(zip(names,values))

def structure_summary(contexts):
    by=collections.defaultdict(set)
    for s,y in contexts:by[s].add(y)
    return {"stand_tokens":len(by),"stand_years":len(contexts),
            "stand_tokens_repeated":sum(len(v)>1 for v in by.values()),
            "strict_adjacent_year_pairs":sum(sum(y+1 in v for y in v) for v in by.values()),
            "recorded_years":sorted({y for s,y in contexts}),
            "year_gap_counts":dict(sorted(collections.Counter(b-a for ys in by.values() for a,b in zip(sorted(ys),sorted(ys)[1:])).items()))}

def audit_est(stands,details):
    sub={};sub_fields=["subset_ID","management","beetle_stands","beetle_years"]
    for r in selected_rows(stands["1.1_subsets"],sub_fields):
        k=token(r["subset_ID"])
        require(valid(k) and k not in sub,"SUBSET_KEY_MISSING_OR_DUPLICATE")
        sub[k]=r
    # Identify the literal group via the author-named beetle detail sheet,
    # not through species names, row counts or other response information.
    detail_fields=["group","subset_ID","stand_ID","survey_year","method_type","trap_no"]
    detail=collections.defaultdict(set);detail_sub=collections.defaultdict(set)
    groups=set();missing_year=0;missing_id=0;method_counts=collections.Counter();rows=0
    for r in selected_rows(details["2.4_beetle_detailed"],detail_fields):
        rows+=1
        g=token(r["group"]);require(valid(g),"DETAIL_GROUP_MISSING");groups.add(g)
        method=token(r["method_type"])
        require(method in {"trap","log"},"AUTHOR_METHOD_TYPE_UNKNOWN")
        method_counts[method]+=1
        if not valid(r["stand_ID"]) or not valid(r["subset_ID"]):
            missing_id+=1;continue
        if not valid(r["survey_year"]):
            missing_year+=1;continue
        k=(token(r["stand_ID"]),year(r["survey_year"]))
        detail[(method,k)].add(token(r["trap_no"]))
        detail_sub[(method,k)].add(token(r["subset_ID"]))
    require(len(groups)==1 and rows>0,"DETAIL_GROUP_NOT_UNIQUE")
    beetle_group=next(iter(groups))
    # Source ledger is stand x taxon-group x survey-year, not occurrences.
    by_group=collections.defaultdict(set);ledger_sub=collections.defaultdict(set)
    n_bad=collections.Counter();ledger_rows=0
    for r in selected_rows(stands["1.2_stands"],["group","stand_ID","subset_ID","survey_year"]):
        g=token(r["group"])
        if not valid(g):n_bad["missing_group"]+=1;continue
        if not valid(r["stand_ID"]) or not valid(r["subset_ID"]) or not valid(r["survey_year"]):
            n_bad["missing_required_group_ledger_key"]+=1
            if g==beetle_group:n_bad["missing_beetle_ledger_key"]+=1
            continue
        k=(token(r["stand_ID"]),year(r["survey_year"]))
        by_group[g].add(k)
        if g==beetle_group:
            ledger_rows+=1;ledger_sub[k].add(token(r["subset_ID"]))
    require(beetle_group in by_group,"BEETLE_GROUP_NOT_IN_LEDGER")
    ledger=by_group[beetle_group]
    trap={k for m,k in detail if m=="trap"}
    log={k for m,k in detail if m=="log"}
    matched=ledger&trap
    mismatch=sum(detail_sub[("trap",k)]!=ledger_sub[k] for k in matched)
    exact={k for k in matched if len(ledger_sub[k])==1 and detail_sub[("trap",k)]==ledger_sub[k]}
    require(all(s in sub for v in ledger_sub.values() for s in v),"LEDGER_SUBSET_NOT_DEFINED")
    repeated_sub=collections.defaultdict(set)
    for k in exact:
        repeated_sub[next(iter(ledger_sub[k]))].add(k)
    # Subset-level design labels only, no actual stand/subset IDs exported.
    subset_support=[]
    for s,ks in repeated_sub.items():
        ss=structure_summary(ks)
        if ss["stand_tokens_repeated"]:
            subset_support.append({"management_description":token(sub[s]["management"])[:180],
                "author_reported_beetle_years":token(sub[s]["beetle_years"])[:100],**ss})
    result={
        "author_beetle_group_label":beetle_group,
        "group_ledger_support":{g:structure_summary(v) for g,v in sorted(by_group.items())},
        "beetle_ledger_source_rows":ledger_rows,
        "beetle_ledger_duplicate_context_rows":ledger_rows-len(ledger),
        "missing_ledger_routing_counts":dict(n_bad),
        "detailed_method_row_counts_not_individuals":dict(method_counts),
        "detail_missing_year_rows":missing_year,"detail_missing_id_rows":missing_id,
        "trap_record_support":structure_summary(trap),"rearing_record_support":structure_summary(log),
        "beetle_ledger_without_trap_records":len(ledger-trap),
        "trap_records_without_beetle_ledger":len(trap-ledger),
        "shared_ledger_trap_contexts":len(matched),
        "shared_contexts_with_subset_disagreement":mismatch,
        "shared_contexts_exact_single_subset":structure_summary(exact),
        "matched_contexts_with_at_least_two_distinct_trap_numbers":sum(len({v for v in detail[("trap",k)] if valid(v)})>=2 for k in exact),
        "repeated_same_subset_support":subset_support,
        "empty_traps_not_inferred_from_missing_occurrence_rows":True,
        "effort_and_habitat_contrast_still_require_verification":True}
    return result

def estonia(o):
    a=est_file("1_subsets_stands_v3.xlsx",10094384)
    b=est_file("2_details_v2.xlsx",10499508)
    o["both_publisher_md5_verified"]=True
    w1=openpyxl.load_workbook(io.BytesIO(a),read_only=True,data_only=False,keep_links=False)
    w2=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=False,keep_links=False)
    try:o.update(audit_est(w1,w2))
    finally:w1.close();w2.close()
    o["status"]="EST_REPEATED_STAND_ROUTING_ONLY"

def emend(o):
    doi="10.5061/dryad.msbcc2fvq"
    sha="59dfbb4c8249bfbaa7e6775e422a1d14e0ebb6e31363292e1287f5d4a0199cd7"
    d=dryad_meta("https://datadryad.org/api/v2/datasets/"+urllib.parse.quote("doi:"+doi,safe=""))
    require(doi in str(d.get("identifier") or d.get("doi") or "").lower(),"EMEND_DOI_DRIFT")
    v=dryad_meta(href(d["_links"]["stash:version"]["href"]))
    require(str(v.get("publicationDate","")).startswith("2020-05-27"),"EMEND_VERSION_DRIFT")
    url=href(v["_links"]["stash:files"]["href"])
    arr=dryad_meta(url+("&" if "?" in url else "?")+"per_page=100").get("_embedded",{}).get("stash:files",[])
    require(len(arr)==1,"EMEND_FILE_COUNT_DRIFT")
    f=arr[0]
    require((f.get("path") or f.get("filename"))=="EMEND_Carabids_15.csv" and f.get("size")==118068 and str(f.get("digest")).lower()==sha,"EMEND_PINNED_MANIFEST_DRIFT")
    o.update(pinned_manifest_verified=True,source_sha256=sha,source_size=118068)
    link=href((f.get("_links",{}).get("stash:download") or {}).get("href"))
    o["original_file_request_attempted"]=True
    raw=get(link,"datadryad.org",118068,"application/octet-stream")
    require(len(raw)==118068 and hashlib.sha256(raw).hexdigest()==sha,"EMEND_FILE_DIGEST_DRIFT")
    o["original_file_sha256_verified"]=True
    # First row only: source field candidates, no taxon headers disclosed.
    first=io.BytesIO(raw).readline(50001)
    require(0<len(first)<=50000,"EMEND_HEADER_LIMIT")
    s=first.decode("utf-8-sig",errors="strict").rstrip("\r\n")
    sep=max((",",";","\t"),key=s.count)
    h=next(csv.reader([s],delimiter=sep))
    safe={"year","yr","time","cover","covertype","foresttype","standtype","treatment","trt","retention","retentionlevel","harvest","block","rep","replicate","compartment","compartmentid","comp","site","siteid","stand","standid","plot","plotid","effort","trapdays"}
    o["header"]={"columns":len(h),"recognized_method_field_candidates":[{"column":i+1,"field":x} for i,x in enumerate(h) if re.sub(r"[^a-z0-9]","",x.casefold()) in safe]}
    o["status"]="EMEND_PINNED_FIRST_HEADER_ONLY"

def test():
    w1=openpyxl.Workbook();w1.active.title="1.1_subsets"
    w1.active.append(["subset_ID","management","beetle_stands","beetle_years"])
    w1.active.append([1,"control",2,"2005-2006"])
    s=w1.create_sheet("1.2_stands");s.append(["group","stand_ID","subset_ID","survey_year","taxon_value"])
    for x in ("A","B"):
        for y in (2005,2006):s.append(["beetles",x,1,y,999])
    w2=openpyxl.Workbook();w2.active.title="2.4_beetle_detailed";d=w2.active
    d.append(["group","subset_ID","stand_ID","survey_year","method_type","trap_no","abundance"])
    d.append(["beetles",1,"A",2005,"trap",1,123])
    d.append(["beetles",1,"A",2006,"trap",2,123])
    d.append(["beetles",1,"B",2005,"log",None,123])
    a=audit_est(w1,w2)
    assert a["group_ledger_support"]["beetles"]["strict_adjacent_year_pairs"]==2
    assert a["shared_contexts_exact_single_subset"]["strict_adjacent_year_pairs"]==1
    assert a["beetle_ledger_without_trap_records"]==2
    assert a["rearing_record_support"]["stand_years"]==1
    print("EST_LEDGER_TRAP_REARING_SEPARATION_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="northern_repeat_admission/receipt.json");a=p.parse_args();test()
    if a.test:return
    r={"schema":"structural.northern_repeat_admission.v1","original_biological_cells_interpreted":0,"new_ecological_effects_scored":0,"raw_source_exported":False,"Finland":"HTTP401_HOLD_NO_RETRY","sources":{}}
    for name,fn in (("Estonia",estonia),("EMEND",emend)):
        o={};r["sources"][name]=o
        try:fn(o)
        except urllib.error.HTTPError as e:o.update(status="SOURCE_HTTP_STOP",http=e.code)
        except Exception as e:o.update(status="SOURCE_SCHEMA_OR_TRANSPORT_STOP",error_class=type(e).__name__,reason=str(e) if isinstance(e,Stop) else None)
    q=Path(a.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(r,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
