#!/usr/bin/env python3
"""v1.232 post-publication observed destination resighting after natal export.

All unknown year+2 fates remain UNKNOWN, never mortality or rescue.
"""
import argparse,csv,io,json,hashlib
from collections import defaultdict,Counter
from pathlib import Path

def sha(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
def rows(raw):
    return csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=";")
def integer(v):
    try:return int(str(v).strip().strip('"'))
    except (TypeError,ValueError):return None
def classify(observations,year,dest):
    dests={i for y,i,s in observations if y==year+2 and s in ("capt","obs")}
    if not dests:return "unknown_second_followup"
    if len(dests)>1:return "ambiguous_second_followup"
    return "same_destination_seen_t2" if next(iter(dests))==dest else "different_destination_seen_t2"
def analyze(presence,pop,contract):
    src=contract["source"]
    if sha(presence)!=src["presence_sha"] or sha(pop)!=src["population_sha"]:
        raise ValueError("Frozen source fingerprint differs")
    islands={integer(r["Island"]) for r in rows(pop)}-{None,0}
    if len(islands)!=11:raise ValueError("Not eleven model islands")
    ids=defaultdict(set)
    for r in rows(presence):
        ID=(r.get("ID") or "").strip().strip('"')
        y=integer(r.get("Year"));i=integer(r.get("Island"))
        stage=(r.get("stage") or "").strip().strip('"').lower()
        if ID.lower() in ("","na","nan") or y is None or i not in islands or stage not in ("nest","capt","obs"):
            continue
        ids[ID].add((y,i,stage))
    cut=lambda y:("historical" if 1994<=y<=2012 else
        "boundary" if 2013<=y<=2014 else
        "later" if 2015<=y<=2020 else
        "right_censored_2021" if y==2021 else "outside")
    totals=defaultdict(Counter);per_origin=defaultdict(Counter)
    quality=Counter()
    for ID,obs in ids.items():
        natal={(y,i) for y,i,s in obs if s=="nest"}
        if len(natal)>1:quality["ambiguous_natal_ID"]+=1;continue
        if not natal:continue
        year,origin=next(iter(natal));era=cut(year)
        if era=="outside":continue
        if era=="right_censored_2021":
            quality["birth_2021_no_2023_followup"]+=1
        targets={i for y,i,s in obs if y==year+1 and s in ("capt","obs")}
        if len(targets)!=1:continue
        target=next(iter(targets))
        group="immigrant" if target!=origin else "resident"
        f=classify(obs,year,target) if year<=2020 else "not_observable_t2"
        totals[(era,group)][f]+=1
        per_origin[(era,group,origin)][f]+=1
    # Reproduce prior frozen v1.231 460 observed migrants and 1789 residents
    emigrants=sum(v for (e,g),counts in totals.items() if g=="immigrant" for v in counts.values())
    residents=sum(v for (e,g),counts in totals.items() if g=="resident" for v in counts.values())
    if (emigrants,residents)!=(460,1789):
        raise ValueError("v1.231 observed next-year identity counts do not reconcile")
    summary=[]
    for era in ("historical","boundary","later","right_censored_2021"):
        for group in ("immigrant","resident"):
            c=totals[(era,group)]
            summary.append({"era":era,"group":group,**dict(c),
                "total_nextyear_observed":sum(c.values())})
    origins=[]
    for (era,g,i),counts in sorted(per_origin.items()):
        origins.append({"era":era,"group":g,"origin_island":i,
            "total_nextyear_observed":sum(counts.values()),
            "same_destination_seen_t2":counts["same_destination_seen_t2"],
            "different_destination_seen_t2":counts["different_destination_seen_t2"],
            "unknown_or_ambiguous_t2":counts["unknown_second_followup"]+counts["ambiguous_second_followup"],
            "not_observable_t2":counts["not_observable_t2"]})
    return {"schema":"structural.helgeland_destination_retention_observation.v1_232",
       "status":"PUBLISHED_OBSERVATIONAL_TWO_YEAR_FOLLOWUP_NOT_TRUE_SURVIVAL",
       "n_islands":11,"original_t1_observed_immigrants":emigrants,
       "original_t1_observed_residents":residents,
       "source_identity_ambiguity":dict(quality),
       "two_year_followup_by_era_and_origin_status":summary,
       "per_natal_origin":origins,
       "no_t2_observation_not_mortality":True,
       "t2_same_island_resighting_not_established_breeding_fitness":True,
       "not_new_confirmatory_evidence":True,"GEB_scientific_HOLD":True,
       "eBird_used":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("author",type=Path)
    p.add_argument("contract",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();contract=json.loads(a.contract.read_text())
    src=contract["source"]
    result=analyze((a.author/src["presence"]).read_bytes(),
                   (a.author/src["population"]).read_bytes(),contract)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
