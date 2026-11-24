#!/usr/bin/env python3
"""BioTIME v4 candidate roster and two exact public study downloads.
Only publisher metadata and observation routing fields. Never interpret or
export taxon names, abundance, biomass, coordinates, plot/sample IDs or contacts.
Study-specific permissions control downloads; an empty/unclear licence is HOLD.
Live public CSV is not automatically the pinned v4 snapshot.
"""
import argparse,csv,io,re,json,hashlib,collections,urllib.request,urllib.parse,urllib.error
from pathlib import Path
URL="https://zenodo.org/records/15222193/files/biotime_v2_metadata_15April25.csv?download=1"
MD5="3daed71ed554888309f9f2443a847bea"
STUDIES={"775":{"years":set(range(2009,2014)),"nominal_sites":35},"458":{"years":set(range(2008,2012)),"nominal_sites":44}}
beetle=re.compile(r"\b(?:beetles?|coleoptera|carabid\w*|scarabae\w*|saproxylic)\b",re.I)
forest=re.compile(r"\b(?:forests?|woodlands?|taiga)\b",re.I)
MISSING={"","na","nan","null","none","n/a"}
SAFE_META=("STUDY_ID","TITLE","REALM","CLIMATE","HABITAT","BIOME_MAP","TAXA","ORGANISMS","START_YEAR","END_YEAR","DATA_POINTS","GENERAL_TREAT","TREATMENT","SAMPLE_DESC_NAME","PERMISSIONS","LINK_ID","ABUNDANCE_TYPE")
class Stop(ValueError):pass
def norm(v):return " ".join(str(v or "").strip().split())
def missing(v):return norm(v).casefold() in MISSING
def require(v,m):
    if not v:raise Stop(m)
def candidate(r):
    return norm(r["REALM"]).casefold()=="terrestrial" and bool(beetle.search(" ".join(norm(r[k]) for k in ("TITLE","TAXA","ORGANISMS")))) and bool(forest.search(" ".join(norm(r[k]) for k in ("HABITAT","BIOME_MAP"))))
def fetch(url,host,cap):
    req=urllib.request.Request(url,headers={"User-Agent":"Structural-BioTIME-source-routing-audit/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:
        dest=urllib.parse.urlsplit(r.url)
        require(dest.scheme=="https" and dest.hostname==host and r.status==200,"SOURCE_HTTP_OR_ORIGIN_STOP")
        raw=r.read(cap+1)
        require(len(raw)<=cap,"SOURCE_BYTE_LIMIT_STOP")
        return raw
def readcsv(raw):
    return csv.DictReader(io.StringIO(raw.decode("utf-8-sig",errors="strict"),newline=""))
def metadata(raw):
    require(hashlib.md5(raw).hexdigest()==MD5,"V4_METADATA_MD5_DRIFT")
    rd=readcsv(raw);require(set(SAFE_META).issubset(rd.fieldnames or []),"METADATA_COLUMNS_DRIFT")
    rows=[]
    for r in rd:
        rows.append({k:norm(r[k]) for k in SAFE_META})
    require(len(rows)==708 and len({r["STUDY_ID"] for r in rows})==708,"METADATA_FRAME_DRIFT")
    found=[r for r in rows if candidate(r)]
    require(len(found)==10,"CANDIDATE_COUNT_DRIFT")
    return found
def licence_ok(v):
    # Explicitly permissive CC0/CC BY variants only, no interpretation of vague permission.
    t=norm(v).casefold()
    if "noncommercial" in t or "non-commercial" in t or "by-nc" in t or "no derivatives" in t or "by-nd" in t:return False
    return bool(re.fullmatch(r"(?:cc0(?: 1\.0)?|cc[- ]by(?:[- ]sa)?(?: [234]\.0)?|creative commons attribution(?: [234]\.0)?(?: international)?|https://creativecommons.org/(?:publicdomain/zero/1\.0|licenses/by(?:-sa)?/[234]\.0)/?)",t))
def inspect_routes(raw,sid):
    rd=readcsv(raw);h=rd.fieldnames or []
    allowed=("STUDY_ID","SAMPLE_DESC","PLOT","YEAR","MONTH","DAY","LATITUDE","LONGITUDE")
    require(len(set(h))==len(h),"DUPLICATE_HEADER")
    # Exact case-insensitive column normalization only; no alias guessing.
    m={x.upper():x for x in h}
    require(len(m)==len(h),"CASE_COLLIDING_HEADER")
    require(set(("STUDY_ID","SAMPLE_DESC","YEAR")).issubset(m),"RAW_REQUIRED_ROUTING_FIELDS_MISSING")
    samples={};n=0;missing_plot=0;plot_years=collections.defaultdict(set);years=collections.Counter()
    for r in rd:
        n+=1
        require(n<=100000 and None not in r,"RAW_ROW_WIDTH_OR_CAP")
        z={k:norm(r.get(m[k])) for k in allowed if k in m}
        require(z["STUDY_ID"]==sid,"RAW_WRONG_STUDY")
        require(z["YEAR"].isascii() and z["YEAR"].isdigit() and int(z["YEAR"]) in STUDIES[sid]["years"],"RAW_YEAR_DRIFT")
        require(not missing(z["SAMPLE_DESC"]),"RAW_SAMPLE_ID_MISSING")
        key=z["SAMPLE_DESC"];y=int(z["YEAR"])
        # Audit sample-descriptor identity with physical routing metadata.
        val=tuple(z.get(k,"") for k in ("PLOT","YEAR","MONTH","DAY","LATITUDE","LONGITUDE"))
        require(key not in samples or samples[key]==val,"SAMPLE_ROUTING_CONFLICT")
        samples[key]=val
        years[y]+=1
    require(n>0,"RAW_EMPTY")
    for val in samples.values():
        p,y=val[:2]
        if missing(p):missing_plot+=1;continue
        plot_years[p].add(int(y))
    # PLOT tokens are candidates, never certified physical sites or treatment.
    count=sum(sum(y+1 in ys for y in ys) for ys in plot_years.values())
    return {"source_csv_header_count":len(h),"available_routing_fields":[k for k in allowed if k in m],
      "source_csv_sha256":hashlib.sha256(raw).hexdigest(),"physical_bytes_received":len(raw),
      "source_record_count":n,"distinct_sample_descriptor_count":len(samples),
      "sample_descriptor_without_plot_token":missing_plot,"distinct_nonmissing_plot_tokens":len(plot_years),
      "distinct_plot_token_year_pairs":sum(len(ys) for ys in plot_years.values()),
      "adjacent_plot_token_year_candidates":count,
      "observed_calendar_years":sorted(years),"treatment_column_name_candidates":[x for x in ("TREATMENT","HABITAT","GENERAL_TREAT","LAND_USE","TREAT") if x in m],
      "same_physical_site_identity_verified":False,"treatment_crosswalk_verified":False,"effort_and_empty_sample_opportunities_verified":False}
def test():
    raw=b"STUDY_ID,SAMPLE_DESC,PLOT,YEAR,ABUNDANCE\n775,a,p,2009,999\n775,a,p,2009,888\n775,b,p,2010,777\n775,c,p,2012,666\n"
    q=inspect_routes(raw,"775");assert q["distinct_sample_descriptor_count"]==3 and q["adjacent_plot_token_year_candidates"]==1
    assert licence_ok("CC BY 4.0") and not licence_ok("CC BY-NC 4.0") and not licence_ok("")
    print("BIOTIME_ROUTING_SYNTHETIC_PASS")
def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="biotime_routing/receipt.json");a=p.parse_args();test()
    if a.test:return
    out={"schema":"structural.biotime_v4_10candidate_2study_routing.v1","biological_cells_interpreted":0,"ecological_effects_scored":0,"raw_source_exported":False,"studies":{}}
    try:
        candidates=metadata(fetch(URL,"zenodo.org",4_000_000))
        out["candidate_roster"]=candidates
        out["metadata_md5_verified"]=True
        d={r["STUDY_ID"]:r for r in candidates}
        require(set(STUDIES).issubset(d),"PRIORITY_STUDY_NOT_IN_CANDIDATES")
        for sid in STUDIES:
            q={"permissions":d[sid]["PERMISSIONS"],"sample_desc_definition":d[sid]["SAMPLE_DESC_NAME"]}
            out["studies"][sid]=q
            if not licence_ok(q["permissions"]):
                q["status"]="STUDY_PERMISSION_REVIEW_HOLD";continue
            try:
                # Exact URLs advertised by the publisher's Download raw data buttons.
                url="https://biotime.st-andrews.ac.uk/dl_request.php?dl=rawdata&study="+sid
                raw=fetch(url,"biotime.st-andrews.ac.uk",8_000_000)
                q.update(inspect_routes(raw,sid));q["status"]="PUBLIC_CSV_ROUTING_DIAGNOSTIC_ONLY"
            except urllib.error.HTTPError as e:q.update(status="SOURCE_HTTP_STOP",http=e.code)
            except Stop as e:q.update(status="SOURCE_SCHEMA_STOP",reason=str(e))
            except Exception as e:q.update(status="SOURCE_TRANSPORT_OR_PARSE_STOP",error_type=type(e).__name__)
        out["status"]="CANDIDATE_ROSTER_AND_STUDY_ROUTING_REVIEW_COMPLETE"
    except Stop as e:out.update(status="SOURCE_STOP",reason=str(e))
    except Exception as e:out.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(out,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
