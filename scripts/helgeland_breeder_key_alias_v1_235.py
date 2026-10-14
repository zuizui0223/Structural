#!/usr/bin/env python3
"""v1.235. Exhaustive source-named key aliases for author breeder table.

Compare same-string ID, Year_ID, Year_ID_Location against marked-bird ID.
Only identity, nest birth-year, recorded adult year/island are parsed.
N_nestlings, N_Recruits and r2s are deliberately NEVER read.
"""
import argparse,csv,hashlib,io,json
from pathlib import Path
from collections import Counter,defaultdict

SHA={"presence":"c998367c55d0d88ec17e6d1dc2931a97c46aff55",
     "producer":"e6cc1558b740b03b9ca33c3af180e05079bcbba8"}
def git_blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
def val(v):return (v or "").strip().strip('"')
def number(v):
    try:return int(val(v))
    except (ValueError,TypeError):return None
def rows(raw):
    yield from csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=";")
def producer_identity_rows(raw):
    src=csv.reader(io.StringIO(raw.decode("latin-1"),newline=""),delimiter=";")
    header=[val(x) for x in next(src)]
    if len(header)!=24 or set(["ID","Year_ID","Year_ID_Location","Year","Least_hatchyear","Island"])-set(header):
        raise ValueError("Frozen author producer header or field positions differ")
    for line in src:
        if len(line)!=25:raise ValueError("Producer row must have one R index + 24 source fields")
        d=dict(zip(header,line[1:]))
        yield {key:d[key] for key in ("ID","Year_ID","Year_ID_Location","Year","Least_hatchyear","Island")}
def run(presence,producer):
    if git_blob(presence)!=SHA["presence"] or git_blob(producer)!=SHA["producer"]:
        raise ValueError("Frozen source blob SHA mismatch")
    natal=defaultdict(set)
    adults=defaultdict(set)
    for r in rows(presence):
        uid=val(r.get("ID"));year=number(r.get("Year"));island=number(r.get("Island"))
        if not uid or year is None or island is None:continue
        stage=val(r.get("stage")).casefold()
        if stage=="nest":natal[uid].add((year,island))
        if stage in ("obs","capt"):adults[(uid,year)].add(island)
    known={uid:next(iter(v)) for uid,v in natal.items() if len(v)==1}
    names=("ID","Year_ID","Year_ID_Location")
    result={}
    total=0
    for key in names:result[key]=Counter()
    for r in producer_identity_rows(producer):
        total+=1
        prod_year=number(r["Year"])
        hatch=number(r["Least_hatchyear"])
        producer_island=number(r["Island"])
        for key in names:
            id=val(r[key]);c=result[key]
            if id not in known:
                c["not_nest_provenance_ID"]+=1
                continue
            birth_year,birth_island=known[id]
            c["individual_ID_matches_known_nest"]+=1
            if hatch==birth_year:
                c["hatchyear_matches_nest_year"]+=1
            else:c["hatchyear_conflicts"]+=1
            if (id,prod_year) in adults:
                c["same_year_observed_adult"]+=1
                if producer_island in adults[(id,prod_year)]:
                    c["same_year_same_island_adult"]+=1
                    if hatch==birth_year:
                        c["all_ID_nestyear_adult_year_island_match"]+=1
                    else:
                        c["same_year_same_island_but_birthyear_conflict"]+=1
    if total!=1903:raise ValueError("Author rows changed")
    out={"schema":"structural.helgeland_breeder_named_key_alias_gate.v1_235",
        "status":"SOURCE_ID_ALIAS_DIAGNOSTIC_NOT_REPRODUCTIVE_ANALYSIS",
        "author_source_commit":"a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5",
        "pinned_blob_sha1":SHA,
        "producer_rows":total,
        "unique_source_nest_known_individual_IDs":len(known),
        "named_candidate_key_results":{key:dict(result[key]) for key in names},
        "N_nestlings_N_Recruits_values_decoded":False,
        "only_source_named_existing_key_columns_compared":True,
        "no_ambiguous_hatchyear_keys_assigned":True,
        "crosswalk_is_not_valid_without_birthyear_year_and_island":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False}
    return out
def main():
    a=argparse.ArgumentParser()
    a.add_argument("author",type=Path)
    a.add_argument("--out",type=Path,required=True)
    z=a.parse_args()
    d=z.author/"Data"
    r=run((d/"presence_data_1994_2022.txt").read_bytes(),
          (d/"nestling_producers_2007_2014.txt").read_bytes())
    z.out.parent.mkdir(parents=True,exist_ok=True)
    z.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
