#!/usr/bin/env python3
"""Published Helgeland bird data: observed next-year natal re-sightings only.
No demographic rescue, unseen migrant imputation, or fresh confirmation.
"""
import argparse,csv,hashlib,io,json
from collections import defaultdict,Counter
from pathlib import Path
def blob(x):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\x00"+x).hexdigest()
def records(raw):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=";")
    for r in reader:yield r
def integer(x):
    try:return int(str(x).strip().strip('"'))
    except (ValueError,TypeError):return None
def score(occ,pop,contract):
    s=contract["source"]
    if blob(occ)!=s["presence_sha"] or blob(pop)!=s["population_sha"]:
        raise ValueError("Author git file fingerprint changed")
    islands={integer(r["Island"]) for r in records(pop)}
    islands.discard(None);islands.discard(0)
    if len(islands)!=11:raise ValueError("Expected 11 fixed model islands")
    seen=defaultdict(set);qc=Counter()
    for r in records(occ):
        qc["source_rows"]+=1
        id=(r.get("ID") or "").strip().strip('"')
        year=integer(r.get("Year"));island=integer(r.get("Island"))
        stage=(r.get("stage") or "").strip().strip('"').lower()
        if id.lower() in ("","na","nan") or year is None or island is None:
            qc["invalid_id_year_island"]+=1;continue
        if island not in islands:
            qc["outside_model_islands"]+=1;continue
        if stage not in ("nest","capt","obs"):
            qc["other_stage"]+=1;continue
        seen[id].add((year,island,stage))
    periods={"historical":(1994,2013),"bridge":(2014,2014),"later":(2015,2021)}
    result={};origins=[];edges=[]
    for era,(lo,hi) in periods.items():
        totals=Counter();byorigin=defaultdict(Counter);byedge=Counter()
        for id,rows in seen.items():
            natal={(y,i) for y,i,stage in rows if stage=="nest"}
            if not natal:continue
            if len(natal)!=1:
                if era=="historical":qc["ambiguous_natal_id_global"]+=1
                continue
            y,origin=next(iter(natal))
            if not lo<=y<=hi:continue
            totals["marked_nest_individuals"]+=1;byorigin[origin]["marked"]+=1
            dest={i for yy,i,stage in rows if yy==y+1 and stage in ("capt","obs")}
            if len(dest)!=1:
                kind="unknown_followup" if not dest else "ambiguous_destination"
                totals[kind]+=1;byorigin[origin][kind]+=1;continue
            destination=next(iter(dest))
            kind="immigrant" if destination!=origin else "resident"
            totals[kind]+=1;byorigin[origin][kind]+=1
            if destination!=origin:byedge[(origin,destination)]+=1
        assert totals["marked_nest_individuals"]==sum(totals[k] for k in ("immigrant","resident","unknown_followup","ambiguous_destination"))
        result[era]=dict(totals)
        for origin in sorted(islands):
            r=byorigin[origin];den=r["immigrant"]+r["resident"]
            origins.append({"era":era,"origin":origin,"marked":r["marked"],
                            "observed_recruits":den,"exported":r["immigrant"],
                            "retained":r["resident"],"no_followup":r["unknown_followup"],
                            "ambiguous":r["ambiguous_destination"],
                            "export_share_observed":r["immigrant"]/den if den else None})
        for (i,j),n in sorted(byedge.items()):
            edges.append({"era":era,"origin":i,"destination":j,"observed_n":n})
    return {"schema":"structural.helgeland_known_natal_resight.v1_231",
            "status":"POSTPUBLICATION_DESCRIPTIVE_DIRECTLY_OBSERVED_NATAL_TRANSFERS_ONLY",
            "n_model_islands":11,"source_qc":dict(qc),
            "periods":result,"by_source":origins,"direct_observed_edges":edges,
            "unknown_followup_is_not_death":True,
            "documented_transfer_is_not_all_dispersal_or_demographic_rescue":True,
            "same_2021_and_2026_archipelago":True,
            "GEB_scientific_HOLD":True,"eBird_used":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("author",type=Path)
    p.add_argument("contract",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();c=json.loads(a.contract.read_text())
    s=c["source"]
    r=score((a.author/s["presence"]).read_bytes(),
            (a.author/s["population"]).read_bytes(),c)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
