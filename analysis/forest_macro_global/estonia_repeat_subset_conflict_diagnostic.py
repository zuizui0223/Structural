#!/usr/bin/env python3
"""Estonia v3 source-only routing diagnosis. No biological values interpreted.
Diagnose the failed subset key separately from the stand/year census.
No EMEND/Finland requests. No invented stand identities or inferred zeros.
"""
import argparse,collections,io,json,re,hashlib
from pathlib import Path
import openpyxl
from northern_repeat_stand_emend_admission import est_file, token, valid, year, structure_summary

class Stop(ValueError):pass
def req(x,m):
    if not x:raise Stop(m)

def rows(ws,fields):
    it=ws.iter_rows(values_only=True);h=[token(x) for x in next(it,())]
    req(all(h.count(x)==1 for x in fields),"REQUIRED_ROUTING_HEADER_MISSING_OR_DUPLICATE")
    inds=[h.index(x) for x in fields]
    for i,r in enumerate(it,2):
        req(i<=400000,"ROW_LIMIT")
        v=tuple(token(r[j]) if j<len(r) else "" for j in inds)
        if any(valid(x) for x in v):yield v

def subset_diagnose(ws):
    fields=("subset_ID","subset_ID2","management","beetle_stands","beetle_years")
    table=list(rows(ws,fields));by=collections.defaultdict(set);composite=collections.defaultdict(set)
    counts=collections.Counter()
    for sid,name,management,n,ys in table:
        if not valid(sid):
            counts["missing_id"]+=1
            continue
        counts["valid_id_rows"]+=1
        by[sid].add((name,management,n,ys))
        if valid(name):composite[(sid,name)].add((management,n,ys))
    dups=collections.Counter(r[0] for r in table if valid(r[0]))
    return {"source_rows":len(table),"missing_id_rows":counts["missing_id"],
       "distinct_nonmissing_subset_ids":len(by),
       "ids_repeated_in_rows":sum(n>1 for n in dups.values()),
       "ids_with_conflicting_selected_metadata":sum(len(v)>1 for v in by.values()),
       "exact_duplicate_selected_rows":len(table)-len(set(table)),
       "distinct_nonmissing_id_and_name":len(composite),
       "composite_keys_with_conflicting_selected_metadata":sum(len(v)>1 for v in composite.values()),
       "subset_metadata_join_authorized":False},by

def ledger(ws):
    fields=("group","stand_ID","subset_ID","survey_year")
    groups=collections.defaultdict(set);subs=collections.defaultdict(set);bad=collections.Counter();dup=collections.Counter()
    for g,s,z,y in rows(ws,fields):
        if not all(map(valid,(g,s,z,y))):
            bad["missing_key_rows"]+=1
            if valid(g):bad["missing_key_rows_with_group"]+=1
            continue
        try:y=year(y)
        except Exception:bad["invalid_year_rows"]+=1;continue
        groups[g].add((s,y));subs[(g,s,y)].add(z);dup[(g,s,y,z)]+=1
    return groups,subs,{"missing_or_invalid_routing_rows":dict(bad),"duplicate_identical_routing_rows":sum(n-1 for n in dup.values()),"group_stand_year_multiple_subset_ids":sum(len(v)>1 for v in subs.values())}

def details(ws):
    fields=("group","stand_ID","subset_ID","survey_year","method_type","trap_no")
    by=collections.defaultdict(set);subs=collections.defaultdict(set);traps=collections.defaultdict(set);groups=set();bad=collections.Counter();counts=collections.Counter()
    for g,s,z,y,m,t in rows(ws,fields):
        if valid(g):groups.add(g)
        if m not in {"trap","log"}:bad["unknown_or_missing_method_rows"]+=1;continue
        counts[m]+=1
        if not all(map(valid,(g,s,z,y))):bad["missing_key_rows"]+=1;continue
        try:y=year(y)
        except Exception:bad["invalid_year_rows"]+=1;continue
        by[m].add((g,s,y));subs[(m,g,s,y)].add(z)
        if m=="trap" and valid(t):traps[(g,s,y)].add(t)
    return groups,by,subs,traps,{"method_record_row_counts_not_individuals":dict(counts),"missing_or_invalid_routing_rows":dict(bad)}

def audit(w1,w2):
    diag,submeta=subset_diagnose(w1["1.1_subsets"])
    g,ls,lq=ledger(w1["1.2_stands"])
    dg,ds,ss,tr,dq=details(w2["2.4_beetle_detailed"])
    r={"subset_key_diagnostics":diag,"ledger_diagnostics":lq,"detail_diagnostics":dq,
       "group_ledger_support":{a:structure_summary(v) for a,v in sorted(g.items())},
       "detail_group_labels":sorted(dg),"beetle_crosswalk_status":"HOLD"}
    # Named author detail sheet must identify exactly one group. No guessing.
    if len(dg)!=1 or not dg.issubset(g):return r
    group=next(iter(dg));led=g[group]
    trp={(s,y) for a,s,y in ds["trap"] if a==group}
    rear={(s,y) for a,s,y in ds["log"] if a==group}
    exact={(s,y) for s,y in led&trp if len(ls[(group,s,y)])==1 and ls[(group,s,y)]==ss[("trap",group,s,y)]}
    # Keep same-subset constraint distinct from any management label mapping.
    subgroups=collections.defaultdict(set)
    for s,y in exact:subgroups[next(iter(ls[(group,s,y)]))].add((s,y))
    repeated=[]
    for z,ctx in subgroups.items():
        q=structure_summary(ctx)
        if not q["stand_tokens_repeated"]:continue
        md=submeta.get(z,set())
        management={v[1] for v in md if valid(v[1])}
        repeated.append({"metadata_rows_distinct":len(md),"management_label_unique":len(management)==1,**q})
    r.update(beetle_crosswalk_status="ROUTING_DIAGNOSTIC_ONLY",
       author_beetle_group=group,beetle_ledger=structure_summary(led),
       trap_record_support=structure_summary(trp),rearing_record_support=structure_summary(rear),
       shared_stand_years=len(led&trp),ledger_without_trap_record=len(led-trp),trap_without_ledger=len(trp-led),
       same_unique_subset_support=structure_summary(exact),
       shared_contexts_not_exact_unique_subset=len(led&trp)-len(exact),
       exact_contexts_with_two_or_more_recorded_trap_numbers=sum(len(tr[(group,s,y)])>=2 for s,y in exact),
       repeated_same_subset_support=repeated,
       opportunity_and_effort_verified=False)
    return r

def test():
    a=openpyxl.Workbook();a.active.title="1.1_subsets";s=a.active
    s.append(["subset_ID","subset_ID2","management","beetle_stands","beetle_years"])
    s.append([1,"A","control",2,"2005-2006"]);s.append([1,"B","other",1,"2005"])
    s.append([None,"note",None,None,None])
    s=a.create_sheet("1.2_stands");s.append(["group","stand_ID","subset_ID","survey_year"])
    for y in (2005,2006):s.append(["beetles","s1",1,y])
    b=openpyxl.Workbook();b.active.title="2.4_beetle_detailed";s=b.active
    s.append(["group","stand_ID","subset_ID","survey_year","method_type","trap_no"])
    for y in (2005,2006):s.append(["beetles","s1",1,y,"trap",1])
    s.append(["beetles","s2",1,2005,"log",None])
    q=audit(a,b)
    assert q["subset_key_diagnostics"]["missing_id_rows"]==1
    assert q["subset_key_diagnostics"]["ids_with_conflicting_selected_metadata"]==1
    assert q["same_unique_subset_support"]["strict_adjacent_year_pairs"]==1
    assert q["rearing_record_support"]["stand_years"]==1
    assert not q["repeated_same_subset_support"][0]["management_label_unique"]
    print("ESTONIA_SUBSET_CONFLICT_INDEPENDENT_ROUTING_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="estonia_repeat_diagnostic/receipt.json");args=p.parse_args();test()
    if args.test:return
    o={"schema":"structural.estonia.repeat_diagnostic.v1","original_biological_values_interpreted":0,"new_ecological_effects_scored":0,"raw_rows_exported":False,"EMEND":"HTTP401_HOLD_NO_RETRY","Finland":"HTTP401_HOLD_NO_RETRY"}
    try:
        a=est_file("1_subsets_stands_v3.xlsx",10094384)
        b=est_file("2_details_v2.xlsx",10499508)
        o["both_publisher_md5_verified"]=True
        w1=openpyxl.load_workbook(io.BytesIO(a),read_only=True,data_only=False,keep_links=False)
        w2=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=False,keep_links=False)
        try:o["routing"]=audit(w1,w2)
        finally:w1.close();w2.close()
        o["status"]="ESTONIA_ROUTING_DIAGNOSTIC_COMPLETE"
    except Exception as e:o.update(status="SOURCE_OR_SCHEMA_STOP",error_class=type(e).__name__,reason=str(e) if isinstance(e,Stop) else None)
    q=Path(args.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n");print(json.dumps(o,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
