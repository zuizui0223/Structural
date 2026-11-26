#!/usr/bin/env python3
"""BioTIME publisher study exports: header and author-described routing only.

No taxon, abundance or biomass values interpreted. Do not score communities
from the candidate keys. A live public CSV digest is not a v4 snapshot digest.
"""
import argparse,csv,io,re,json,hashlib,collections,datetime,urllib.error
from pathlib import Path
import biotime_v4_forest_beetle_study_routing as prior

IDS=("775","458","837","838")
KNOWN_PERMISSIONS={"cc-by","cc by 4.0","cc by 4.0 deed attribution 4.0 international","cc by 4.0 attribution 4.0 international","cc0","cc0 1.0"}
EXPECTED={"775":(2009,2013),"458":(2008,2011),"837":(2016,2020),"838":(2016,2021)}
MISSING={"","na","nan","null","none","n/a"}
class Stop(ValueError):pass
def req(x,msg):
    if not x:raise Stop(msg)
def norm(x):return str(x or "").strip()
def fld(x):return re.sub(r"[^a-z0-9]","",norm(x).casefold())
def present(x):return norm(x).casefold() not in MISSING
def integer(x,lo,hi):
    x=norm(x);req(bool(re.fullmatch(r"[0-9]+",x)),"NONINTEGER_ROUTING_DATE")
    v=int(x);req(lo<=v<=hi,"ROUTING_DATE_OUTSIDE_RANGE")
    return v

def get_meta():
    raw=prior.fetch(prior.URL,"zenodo.org",4_000_000)
    req(hashlib.md5(raw).hexdigest()==prior.MD5,"PINNED_METADATA_MD5_DRIFT")
    r=prior.readcsv(raw)
    cols=("STUDY_ID","TITLE","PERMISSIONS","SAMPLE_DESC_NAME","START_YEAR","END_YEAR","TOTAL","GENERAL_TREAT","TREATMENT","ABUNDANCE_TYPE","BIOMASS_TYPE")
    req(set(cols).issubset(r.fieldnames or []),"METADATA_HEADER_DRIFT")
    selected={}
    for row in r:
        sid=norm(row["STUDY_ID"])
        if sid in IDS:
            req(sid not in selected,"DUPLICATE_STUDY_METADATA")
            selected[sid]={k:norm(row[k]) for k in cols}
    req(set(selected)==set(IDS),"METADATA_STUDY_ROSTER_DRIFT")
    for sid,z in selected.items():
        req((integer(z["START_YEAR"],1900,2100),integer(z["END_YEAR"],1900,2100))==EXPECTED[sid],"METADATA_STUDY_YEAR_DRIFT")
    return selected

def header(raw):
    s=raw.decode("utf-8-sig",errors="strict")
    first=s.splitlines()[0] if s else ""
    req(bool(first) and len(first)<20000,"EMPTY_OR_OVERSIZE_FIRST_HEADER")
    counts={d:first.count(d) for d in (",",";","\t")}
    d=max(counts,key=counts.get)
    req(counts[d]>0 and list(counts.values()).count(counts[d])==1,"CSV_DELIMITER_UNRESOLVED")
    reader=csv.DictReader(io.StringIO(s,newline=""),delimiter=d)
    h=reader.fieldnames or []
    req(2<=len(h)<=40,"CSV_LONG_HEADER_WIDTH_UNRESOLVED")
    m={fld(x):x for x in h}
    req(len(m)==len(h),"NORMALIZED_HEADER_COLLISION")
    # For a long occurrence export, only generic field labels are disclosed.
    allowed={"studyid","sampledesc","sampledescription","year","month","day","plot","latitude","longitude","depth","idallrawdata","idspecies","newid","validname","resolution","taxon","genus","species","abundance","biomass","taxa","habitat","treatment","sampleid","recordid","scientificname"}
    info={"delimiter":{",":"comma",";":"semicolon","\t":"tab"}[d],"column_count":len(h),
          "recognized_source_headers":[{"column_1based":i+1,"literal_header":x} for i,x in enumerate(h) if fld(x) in allowed],
          "other_header_field_count":sum(fld(x) not in allowed for x in h)}
    return reader,m,info

def desc_column(m):
    # SAMPLE_DESC is the documented field; the expanded label "sample
    # description" is a spelling of that same explicitly documented role.
    candidates=[m[k] for k in ("sampledesc","sampledescription") if k in m]
    req(len(candidates)==1,"DOCUMENTED_SAMPLE_DESCRIPTOR_COLUMN_UNRESOLVED")
    return candidates[0]

def decode_desc(sid,grammar,s):
    lo,hi=EXPECTED[sid]
    g=norm(grammar).casefold()
    if sid=="458":
        req(g=="treatment_sitecode1_sitecode2_year","AUTHOR_458_GRAMMAR_DRIFT")
        p=s.split("_")
        req(len(p)==4 and all(present(x) for x in p),"AUTHOR_458_FOUR_TOKEN_GRAMMAR")
        y=integer(p[3],lo,hi)
        t=p[0].casefold()
        return (p[0],p[1],p[2]),y,None,None,t,"beetle"
    if sid=="775":
        req(g=="plot_day_month_year","AUTHOR_775_GRAMMAR_DRIFT")
        p=s.rsplit("_",3)
        req(len(p)==4 and present(p[0]),"AUTHOR_775_FOUR_FIELD_GRAMMAR")
        y=integer(p[3],lo,hi);m=integer(p[2],1,12);d=integer(p[1],1,31)
        datetime.date(y,m,d)
        return (p[0],),y,m,d,None,"beetle"
    # The paired Light and Shadow studies explicitly describe three letters:
    # site A-F, treatment O/G, tree A/E/H/K/R/T; _b or _s for arthropods.
    # Author metadata gives the event grammar. Do not map O/G to names or
    # host letters to species without a source-confirmed codebook.
    parts=g.split("_")
    req(parts.count("plot")==1 and parts.count("year")==1 and len(parts)==len(set(parts)) and set(parts).issubset({"plot","year","month","day"}),"AUTHOR_LIGHT_SHADOW_GRAMMAR_UNRESOLVED")
    # Extract the documented whole plot code, allowing its internal _b/_s.
    plotpat=r"(?P<plot>[A-F][OG][AEHKRT]_[bs])" if sid=="837" else r"(?P<plot>[A-F][OG][AEHKRT])"
    pats={"plot":plotpat,"year":r"(?P<year>[0-9]{4})","month":r"(?P<month>[0-9]{1,2})","day":r"(?P<day>[0-9]{1,2})"}
    mm=re.fullmatch("_".join(pats[x] for x in parts),s)
    req(mm is not None,"AUTHOR_LIGHT_SHADOW_PLOT_OR_DATE_GRAMMAR")
    x=mm.groupdict();y=integer(x["year"],lo,hi)
    m=integer(x["month"],1,12) if "month" in x else None
    d=integer(x["day"],1,31) if "day" in x else None
    if d is not None:
        req(m is not None,"DAY_WITHOUT_MONTH");datetime.date(y,m,d)
    p=x["plot"]
    channel=("beetle" if p.endswith("_b") else "spider") if sid=="837" else "fungi"
    return tuple(p[:3]),y,m,d,p[1],channel

def audit(raw,sid,meta,report,expected_n=None):
    r,m,h=header(raw);report["header"]=h
    report["live_csv_sha256"]=hashlib.sha256(raw).hexdigest()
    report["physical_bytes_received"]=len(raw)
    desc=desc_column(m)
    n=0;events={};counts=collections.Counter();byyear=collections.defaultdict(set)
    observed_by_key=collections.defaultdict(set); date_unmatched=0
    for row in r:
        n+=1
        req(n<=100000 and None not in row and all(v is not None for v in row.values()),"SOURCE_ROW_WIDTH_OR_LIMIT")
        if "studyid" in m:req(norm(row[m["studyid"]])==sid,"SOURCE_WRONG_STUDY")
        s=norm(row[desc]);req(present(s),"MISSING_SAMPLE_DESCRIPTOR")
        key,y,month,day,t,channel=decode_desc(sid,meta["SAMPLE_DESC_NAME"],s)
        for f,value in (("year",y),("month",month),("day",day)):
            if f in m and value is not None and present(row[m[f]]):
                req(integer(row[m[f]],1,2100)==value,"EXPLICIT_DATE_DESCRIPTOR_CONFLICT")
        routing=(key,y,month,day,t,channel)
        req(s not in events or events[s]==routing,"SAMPLE_DESCRIPTOR_COLLISION")
        events[s]=routing
        counts[channel]+=1
    req(n>0,"EMPTY_SOURCE")
    report["source_record_count"]=n
    report["study_id_column_present"]="studyid" in m
    # Match pinned public metadata TOTAL, not a substitute for version hashing.
    if expected_n is None:
        expected_n=integer(meta["TOTAL"].replace(",",""),1,100000)
    report["pinned_metadata_total_matches_live_csv"]=n==expected_n
    req(n==expected_n,"LIVE_CSV_RECORD_COUNT_DIFFERS_FROM_PINNED_METADATA")
    for key,y,mo,da,t,ch in events.values():
        observed_by_key[(ch,key)].add(y)
        byyear[(ch,y)].add(key)
    def sub(ch):
        z={key:ys for (c,key),ys in observed_by_key.items() if c==ch}
        return {"distinct_candidate_units":len(z),"candidate_unit_years":sum(map(len,z.values())),
                "strict_adjacent_year_candidates":sum(sum(y+1 in ys for y in ys) for ys in z.values()),
                "units_per_year":{str(y):len(byyear[(ch,y)]) for y in range(EXPECTED[sid][0],EXPECTED[sid][1]+1)}}
    report["sample_descriptors"]=len(events)
    report["channel_record_counts_not_individuals"]=dict(counts)
    report["channels"]={ch:sub(ch) for ch in sorted(counts)}
    report["descriptor_decoding"]="AUTHOR_METADATA_GRAMMAR_PASS_CANDIDATE_ONLY"
    report["effort_or_empty_sample_frame_verified"]=False
    report["physical_identity_crosswalk_verified"]=False
    if sid=="458":
        groups=collections.defaultdict(set)
        for key,y,_,_,t,ch in events.values():groups[t].add(key)
        report["documented_treatment_literal_group_sizes"]={k:len(v) for k,v in groups.items() if k in {"logged","unlogged"}}
        report["other_treatment_group_count"]=sum(k not in {"logged","unlogged"} for k in groups)
        report["candidate_site_codes_reused_across_treatments"]=len({k[1:] for k in groups.get("logged",set())}&{k[1:] for k in groups.get("unlogged",set())})
    if sid in ("837","838"):
        report["literal_treatment_codes"]=sorted({t for _,_,_,_,t,_ in events.values()})
        report["observed_site_letter_count"]=len({k[0] for _,k in observed_by_key})
    return observed_by_key

def pair_channels(a,b):
    # Same literal three-letter author code and strict earlier year only.
    # A positive detection context is NOT an independently verified sampling opportunity.
    bt={(k,y) for (ch,k),ys in a.items() if ch=="beetle" for y in ys}
    fu={(k,y) for (ch,k),ys in b.items() if ch=="fungi" for y in ys}
    triples={(k,y) for k,y in bt if (k,y-1) in bt and (k,y-1) in fu}
    return {"shared_literal_unit_year_contexts":len(bt&fu),
            "prior_fungi_and_prior_beetle_to_next_beetle_candidate_triplets":len(triples),
            "candidate_units_in_triplets":len({k for k,y in triples}),
            "candidate_original_site_letters_in_triplets":len({k[0] for k,y in triples}),
            "triplets_per_target_year":dict(sorted(collections.Counter(str(y) for k,y in triples).items())),
            "same_experiment_not_independent_replication":True,
            "original_physical_log_identity_effort_and_empty_frame_verified":False}
def test():
    raw=b"Study ID;Sample Description;Year;Abundance\n458;logged_A_1_2008;2008;secret\n458;logged_A_1_2009;2009;secret\n"
    q={}
    x=audit(raw,"458",{"SAMPLE_DESC_NAME":"treatment_siteCode1_siteCode2_year"},q,expected_n=2)
    assert q["channels"]["beetle"]["strict_adjacent_year_candidates"]==1
    q={}
    x=audit(b"sample_desc,year,abundance\nA_12_3_2009,2009,x\nA_12_3_2010,2010,y\n","775",{"SAMPLE_DESC_NAME":"Plot_Day_Month_Year"},q,expected_n=2)
    assert q["channels"]["beetle"]["strict_adjacent_year_candidates"]==1
    assert decode_desc("837","month_year_plot","4_2017_AOA_b")==(tuple("AOA"),2017,4,None,"O","beetle")
    assert decode_desc("838","plot_month_year","AOA_10_2016")[0]==tuple("AOA")
    k=tuple("AOA")
    assert pair_channels({("beetle",k):{2016,2017,2019}},{("fungi",k):{2016,2018}})["prior_fungi_and_prior_beetle_to_next_beetle_candidate_triplets"]==1
    assert "cc by 4.0 deed attribution 4.0 international" in KNOWN_PERMISSIONS
    print("AUTHOR_DESCRIPTOR_AND_PERMISSION_SYNTHETIC_PASS")
def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="biotime_descriptor_v2/receipt.json");a=p.parse_args();test()
    if a.test:return
    o={"schema":"structural.biotime_author_descriptor_v2","source_numeric_biology_values_interpreted":0,"ecological_effects_scored":0,"source_raw_rows_exported":False,"studies":{}}
    try:
        meta=get_meta();o["metadata_md5_verified"]=True
        data={}
        for sid in IDS:
            m=meta[sid];q={"sample_desc_definition":m["SAMPLE_DESC_NAME"],"permissions":m["PERMISSIONS"],"title":m["TITLE"]}
            o["studies"][sid]=q
            if m["PERMISSIONS"].casefold() not in KNOWN_PERMISSIONS:
                q["status"]="EXPLICIT_PERMISSION_REVIEW_HOLD";continue
            try:
                url="https://biotime.st-andrews.ac.uk/dl_request.php?dl=rawdata&study="+sid
                raw=prior.fetch(url,"biotime.st-andrews.ac.uk",8_000_000)
                data[sid]=audit(raw,sid,m,q)
                q["status"]="AUTHOR_DESCRIPTOR_ROUTING_PASS_NOT_BIOLOGY"
            except urllib.error.HTTPError as e:q.update(status="SOURCE_HTTP_STOP",http=e.code)
            except Stop as e:q.update(status="SOURCE_ROUTING_STOP",reason=str(e))
            except Exception as e:q.update(status="SOURCE_TRANSPORT_OR_PARSE_STOP",error_type=type(e).__name__)
        if "837" in data and "838" in data:
            o["paired_light_shadow"]=pair_channels(data["837"],data["838"])
        o["status"]="SOURCE_DIAGNOSTICS_COMPLETE"
    except Stop as e:o.update(status="SOURCE_METADATA_STOP",reason=str(e))
    except Exception as e:o.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(o,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
