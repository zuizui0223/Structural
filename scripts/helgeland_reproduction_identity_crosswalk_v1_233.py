#!/usr/bin/env python3
"""v1.233: validate bird ID/year/island join to author reproduction table.

Exposes only join counts, NOT per-bird reproductive counts or effect scores.
The parentage file is author-attributed reproductive output, NOT individual
offspring pedigree or causal immigrant fitness. Published system already exposed.
"""
import argparse,csv,hashlib,io,json
from collections import Counter,defaultdict
from pathlib import Path

SHA={
 "presence":"c998367c55d0d88ec17e6d1dc2931a97c46aff55",
 "population":"c31823caff36dcd07ae30d657f8507a44ab4f7b0",
 "producer":"e6cc1558b740b03b9ca33c3af180e05079bcbba8"}
EXPECTED_COLS=("ID","Year","Island","N_nestlings","N_Recruits")

def blob(x):
    return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\x00"+x).hexdigest()

def normalize(v):
    return (v or "").strip().strip('"')

def integer(s):
    try:return int(normalize(s))
    except (ValueError,TypeError):return None

def presence_rows(raw):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=";")
    required={"ID","Year","Island","stage"}
    if not required.issubset(reader.fieldnames or []):raise ValueError("Presence source schema")
    for r in reader:
        if None in r:raise ValueError("Malformed presence source rows")
        yield r

def producers(raw):
    # Original author R write.table has 24 names and a LEADING row-index
    # in every biological row, making 25 values. Do not shift ID.
    source=io.StringIO(raw.decode("latin-1"),newline="")
    reader=csv.reader(source,delimiter=";")
    fields=[normalize(x) for x in next(reader)]
    if len(fields)!=24 or any(k not in fields for k in EXPECTED_COLS):
        raise ValueError("Frozen 24-column source header changed")
    if len(set(fields))!=24:raise ValueError("Duplicate producer field")
    for line_number,parts in enumerate(reader,2):
        if len(parts)!=25:
            raise ValueError(f"Source row {line_number} not 25 fields")
        rowname=normalize(parts[0])
        if not rowname:raise ValueError("Missing R exported row-number")
        yield dict(zip(fields,parts[1:]))

def audit(pres,pop,prod):
    for name,raw in (("presence",pres),("population",pop),("producer",prod)):
        if blob(raw)!=SHA[name]:raise ValueError("Author source blob drift "+name)
    islands={integer(r["Island"]) for r in csv.DictReader(
        io.StringIO(pop.decode("utf-8-sig"),newline=""),delimiter=";")}-{None,0}
    if len(islands)!=11:raise ValueError("Wrong island population universe")
    marked=defaultdict(set)
    observ=defaultdict(set)
    for r in presence_rows(pres):
        ID=normalize(r["ID"]);year=integer(r["Year"]);isl=integer(r["Island"])
        s=normalize(r["stage"]).lower()
        if not ID or year is None or isl not in islands:continue
        if s=="nest":marked[ID].add((year,isl))
        if s in ("capt","obs"):observ[ID].add((year,isl))
    natal={ID:next(iter(ns)) for ID,ns in marked.items() if len(ns)==1}
    natal_ambiguous={ID for ID,ns in marked.items() if len(ns)>1}
    # New v1.233 descriptive window: potential first t+1 adult year 2007-2014.
    # All individuals must have exactly 1 origin, and exactly 1 destination
    # with capt/obs at origin birth year +1. Same scope as v1.231.
    immigrant_keys=set();resident_keys=set()
    for ID,(birth,origin) in natal.items():
        if birth+1 not in range(2007,2015):continue
        dests={i for year,i in observ.get(ID,set()) if year==birth+1}
        if len(dests)!=1:continue
        dest=next(iter(dests))
        key=(ID,birth+1,dest)
        if dest!=origin:immigrant_keys.add(key)
        else:resident_keys.add(key)
    producer_keys=[];producer_ids=set();producer_years=Counter()
    invalid=Counter()
    for row in producers(prod):
        ID=normalize(row["ID"]);year=integer(row["Year"]);island=integer(row["Island"])
        if not ID or year is None or island is None:
            invalid["bad_producer_identity"]+=1;continue
        producer_ids.add(ID)
        producer_keys.append((ID,year,island))
        producer_years[year]+=1
    pc=Counter(producer_keys)
    duplicates=sum(v-1 for v in pc.values() if v>1)
    unique=set(producer_keys)
    # Distinguish exact bird-year-island join from mere ID reuse.
    join_i=sorted(unique & immigrant_keys)
    join_r=sorted(unique & resident_keys)
    return {
       "schema":"structural.helgeland_reproduction_identity_crosswalk.v1_233",
       "status":"PUBLISHED_SOURCE_ASSAY_IDENTITY_ONLY_NO_REPRODUCTIVE_EFFECT",
       "pinned_blobs":dict(SHA),
       "model_islands":len(islands),
       "producer_columns_from_header":list(EXPECTED_COLS),
       "extra_R_index_column_correctly_dropped":True,
       "producer_record_rows":sum(pc.values()),
       "producer_year_counts":dict(sorted(producer_years.items())),
       "producer_unique_individual_IDs":len(producer_ids),
       "producer_duplicate_individual_year_island_rows":duplicates,
       "producer_invalid_identity":dict(invalid),
       "marked_natal_unique_IDs":len(natal),
       "marked_natal_ambiguous_IDs":len(natal_ambiguous),
       "producer_ID_overlap_with_natal_known":len(producer_ids&set(natal)),
       "eligible_t1_migrant_observed_2007_2014":len(immigrant_keys),
       "eligible_t1_resident_observed_2007_2014":len(resident_keys),
       "exact_author_producer_join_migrant_keys":len(join_i),
       "exact_author_producer_join_resident_keys":len(join_r),
       "author_producer_nestling_and_recruits_numerical_values_accessed":False,
       "observed_natal_to_destination_still_not_offspring_parentage":True,
       "source_ID_overlap_not_equivalent_to_breeding_event":True,
       "detection_and_selection_not_adjusted":True,
       "no_model_scored":True,
       "new_confirmatory_systems":0,
       "original_mammal_heldout_opened":False,
       "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("author",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    root=a.author/"Data"
    result=audit(
        (root/"presence_data_1994_2022.txt").read_bytes(),
        (root/"estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt").read_bytes(),
        (root/"nestling_producers_2007_2014.txt").read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
