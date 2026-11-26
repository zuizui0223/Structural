#!/usr/bin/env python3
"""BioTIME Jari and Mexico source ID and sampling-month coverage only.
No biological values, taxa, raw site IDs, or coordinates exported.
"""
import csv,io,json,hashlib,re,collections,datetime,urllib.error
from pathlib import Path
from biotime_v4_forest_beetle_study_routing import fetch,URL,MD5

PUBLISHER="https://biotime.st-andrews.ac.uk/dl_request.php?dl=rawdata&study="
JARI_SHA="0223c9897f86c7c9d93a000fb6a38f1b932063ec642c5585c126a3a27cdc2ca6"
COMMON_MONTHS={3,5,6,8,10}
class Stop(ValueError):pass
def req(ok,msg):
    if not ok:raise Stop(msg)

def metadata():
    b=fetch(URL,"zenodo.org",4000000)
    req(hashlib.md5(b).hexdigest()==MD5,"PINNED_METADATA_DRIFT")
    rows={r["STUDY_ID"]:r for r in csv.DictReader(io.StringIO(b.decode("utf-8-sig"),newline="")) if r["STUDY_ID"] in {"775","776"}}
    req(set(rows)=={"775","776"},"STUDY_ROSTER_DRIFT")
    expected={"775":("Plot_Day_Month_Year","CC BY 4.0 DEED Attribution 4.0 International",2745),
              "776":("Site_HabitatType_Day_Month_Year","CC BY 4.0 Attribution 4.0 International",1260)}
    for sid,r in rows.items():
        desc,permission,n=expected[sid]
        req(r["SAMPLE_DESC_NAME"]==desc and r["PERMISSIONS"]==permission and int(r["TOTAL"])==n,"PINNED_METHOD_OR_PERMISSION_DRIFT")
    return rows

def parse(raw,sid,strict=True):
    if strict and sid=="775":req(hashlib.sha256(raw).hexdigest()==JARI_SHA and len(raw)==212570,"JARI_EXACT_BYTES_DRIFT")
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    h=reader.fieldnames or []
    req(len(h)==9 and len(set(h))==9 and {"SAMPLE_DESC","YEAR","DAY","MONTH"}.issubset(h),"HEADER_DRIFT")
    allowed={2009,2010,2011,2012,2013} if sid=="775" else {1999,2000,2016,2017}
    events=set();n=0
    for r in reader:
        n+=1;req(None not in r and all(v is not None for v in r.values()),"CSV_WIDTH_DRIFT")
        p=r["SAMPLE_DESC"].strip().rsplit("_",3 if sid=="775" else 4)
        req(len(p)==(4 if sid=="775" else 5) and all(p),"AUTHOR_DESCRIPTOR_GRAMMAR")
        ds=p[-3:]
        req(all(re.fullmatch(r"\d+",v) for v in ds),"DESCRIPTOR_DATE_GRAMMAR")
        d,m,y=map(int,ds);req(y in allowed,"YEAR_DRIFT")
        datetime.date(y,m,d)
        for name,val in (("YEAR",y),("MONTH",m),("DAY",d)):
            req(int(r[name])==val,"DESCRIPTOR_DATE_CONFLICT")
        key=p[0];habitat=p[1] if sid=="776" else ""
        events.add((key,habitat,y,m,d))
    if strict:req(n==({"775":2745,"776":1260}[sid]),"LIVE_ROW_TOTAL_DRIFT")
    return events,n

def report_jari(events):
    # Pure lexical inventory. Prefix counts never certify habitat membership,
    # even if they happen to match the nominal 12/8/15 design.
    keys={k for k,h,y,m,d in events}
    prefixes=collections.Counter()
    shapes=collections.Counter()
    for k in keys:
        match=re.fullmatch(r"([A-Za-z]{1,10})[ _-]?(\d+)",k)
        if match:prefixes[match.group(1)]+=1
        else:shapes[re.sub(r"[A-Za-z]+","A",re.sub(r"\d+","9",k))]+=1
    req(len(keys)==35 and len(events)==175,"JARI_FRAME_DRIFT")
    return {"candidate_plot_codes":len(keys),"recorded_events":len(events),
            "nonsite_specific_prefix_counts":dict(sorted(prefixes.items())),
            "other_lexical_shape_counts":dict(sorted(shapes.items())),
            "habitat_mapping_authenticated":False,
            "warning":"prefix spelling or agreement with 12/8/15 is not author verification"}

def report_mexico(events,strict=True):
    site_hab=collections.defaultdict(set)
    months=collections.defaultdict(set)
    for k,h,y,m,d in events:
        site_hab[k].add(h)
        months[(k,h,y)].add(m)
    # Treat literal habitat tokens as unlabelled groups unless exactly descriptive.
    # Never infer an unknown abbreviation by frequency.
    habs=sorted({h for k,h,y,m,d in events})
    out={}
    for h in habs:
        keys={k for k,a,y,m,d in events if a==h}
        per={}
        for y0,y1 in [(1999,2000),(2016,2017)]:
            pair=[k for k in keys if months.get((k,h,y0)) and months.get((k,h,y1))]
            common=[k for k in pair if (months[(k,h,y0)]&months[(k,h,y1)]&COMMON_MONTHS)]
            complete=[k for k in pair if COMMON_MONTHS<=months[(k,h,y0)] and COMMON_MONTHS<=months[(k,h,y1)]]
            per[f"{y0}-{y1}"]={"recorded_adjacent_site_candidates":len(pair),"at_least_one_same_common_month":len(common),"all_five_common_months_recorded_both_years":len(complete)}
        # Literal habitat token only, not individual IDs.
        req(re.fullmatch(r"[A-Za-z0-9 -]{1,40}",h) is not None,"UNKNOWN_HABITAT_TOKEN_SHAPE")
        out[h]={"candidate_site_tokens":len(keys),"periods":per}
    return {"literal_habitat_groups":out,"distinct_site_tokens":len(site_hab),
            "site_tokens_with_multiple_habitat_labels":sum(len(v)>1 for v in site_hab.values()),
            "recorded_events":len(events),"common_months":sorted(COMMON_MONTHS),
            "complete_effort_zero_and_author_physical_identity_verified":False,
            "warning":"recorded-month counts cannot distinguish no captures from absent sampling"}

def test():
    fake={("x","Forest",1999,3,1),("x","Forest",2000,3,1),("x","Forest",2016,3,1),("x","Forest",2017,3,1)}
    q=report_mexico(fake)
    req(q["literal_habitat_groups"]["Forest"]["periods"]["1999-2000"]["at_least_one_same_common_month"]==1,"SYNTH_MATCH")
    req(q["literal_habitat_groups"]["Forest"]["periods"]["2016-2017"]["all_five_common_months_recorded_both_years"]==0,"SYNTH_COMPLETE")
    print("BIOTIME_TROPICAL_ROUTING_SYNTHETIC_PASS")

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="biotime_tropical_routing/receipt.json")
    a=p.parse_args();test()
    if a.test:return
    out={"schema":"structural.biotime.tropical_routing.v1","original_biological_values_interpreted":0,"ecological_effects_scored":0,"raw_rows_exported":False,"studies":{}}
    try:
        metadata()
        out["pinned_metadata_verified"]=True
        for sid in ("775","776"):
            q={};out["studies"][sid]=q
            try:
                raw=fetch(PUBLISHER+sid,"biotime.st-andrews.ac.uk",2000000)
                q["live_csv_sha256"]=hashlib.sha256(raw).hexdigest()
                events,n=parse(raw,sid)
                q["record_rows"]=n
                q.update(report_jari(events) if sid=="775" else report_mexico(events))
                q["status"]="ROUTING_DIAGNOSTIC_ONLY"
            except urllib.error.HTTPError as e:q.update(status="SOURCE_HTTP_STOP",http=e.code)
            except Stop as e:q.update(status="SOURCE_SCHEMA_STOP",reason=str(e))
            except Exception as e:q.update(status="SOURCE_PARSE_OR_TRANSPORT_STOP",error_type=type(e).__name__)
        out["status"]="SOURCE_REVIEW_COMPLETE"
    except Stop as e:out.update(status="SOURCE_METADATA_STOP",reason=str(e))
    except Exception as e:out.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
