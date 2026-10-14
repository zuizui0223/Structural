#!/usr/bin/env python3
"""v1.234: test whether nominal producer and presence bird ID namespaces coincide.

Strictly an identity/observation-year/hatchyear audit. No N_nestlings or
N_Recruits cells accessed; no reproduction or rescue inference.
"""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
from helgeland_reproduction_identity_crosswalk_v1_233 import (
    SHA,blob,integer,normalize,producers,presence_rows,
)
import csv,io

def compute(occ,pop,prod):
    for name,raw in (("presence",occ),("population",pop),("producer",prod)):
        if blob(raw)!=SHA[name]:raise ValueError("Original author file identity changed")
    islands={integer(r["Island"]) for r in csv.DictReader(
        io.StringIO(pop.decode("utf-8-sig"),newline=""),delimiter=";")}-{0,None}
    if len(islands)!=11:raise ValueError("Study island universe changed")
    nested=defaultdict(set);adults=defaultdict(set)
    for r in presence_rows(occ):
        ID=normalize(r["ID"]);yr=integer(r["Year"]);isl=integer(r["Island"])
        if not ID or yr is None or isl not in islands:continue
        s=normalize(r["stage"]).casefold()
        if s=="nest":nested[ID].add((yr,isl))
        if s in ("capt","obs"):adults[(ID,yr)].add(isl)
    natal={ID:next(iter(a)) for ID,a in nested.items() if len(a)==1}
    immigrant_origin={}
    for ID,(birth,origin) in natal.items():
        if birth+1 not in range(2007,2015):continue
        other=adults.get((ID,birth+1),set())
        if len(other)==1 and origin not in other:
            immigrant_origin[ID]=(birth,origin,next(iter(other)))
    known=Counter()
    hatch_offsets=Counter()
    by_pair=Counter()
    eligible_adult_source=Counter()
    adult_breeder_records=0
    IDs_matched_migration_destination=set()
    for r in producers(prod):
        ID=normalize(r["ID"]);yr=integer(r["Year"]);isl=integer(r["Island"])
        hatch=integer(r["Least_hatchyear"])
        if not ID or yr is None or isl not in islands:
            known["producer_invalid_identity_year_or_island"]+=1;continue
        known["valid_producer_records"]+=1
        dests=adults.get((ID,yr),set())
        if dests:
            known["same_ID_year_seen_in_presence_adult"]+=1
            if isl in dests:
                known["same_ID_year_same_island_in_presence_adult"]+=1
            else:
                known["same_ID_year_different_island_in_presence_adult"]+=1
        else:
            known["ID_year_not_seen_in_presence_adult"]+=1
        if ID not in natal:
            known["ID_not_known_nest_origin"]+=1
            continue
        known["ID_overlap_known_natal_rows"]+=1
        birth,origin=natal[ID]
        if hatch is None:
            known["producer_missing_hatchyear"]+=1
        elif hatch==birth:
            known["producer_hatchyear_agrees_with_natal_year"]+=1
        else:
            known["producer_hatchyear_CONFLICT_with_natal_year"]+=1
        offset=yr-birth
        if offset<0:cat="before_marked_birth_year"
        elif offset==0:cat="same_year_as_marked_birth"
        elif offset==1:cat="one_year_after"
        elif offset==2:cat="two_years_after"
        else:cat="three_or_more_years_after"
        hatch_offsets[cat]+=1
        if ID in immigrant_origin:
            known["rows_with_ID_of_observed_t1_natal_migrant"]+=1
            immigrant_birth,_,dest=immigrant_origin[ID]
            if yr>=immigrant_birth+1 and isl==dest:
                known["later_record_at_documented_t1_migrant_destination"]+=1
                IDs_matched_migration_destination.add(ID)
            if yr==immigrant_birth+1 and isl==dest:
                known["immediate_nextyear_record_at_migrant_destination"]+=1
    result={
      "schema":"structural.helgeland_breeder_ID_birthyear_namespace_diagnostic.v1_234",
      "status":"RETROSPECTIVE_SOURCE_ID_SEMANTICS_DIAGNOSTIC_NO_BREEDER_EFFECT",
      "pinned_source_git_blobs":dict(SHA),
      "source_islands":len(islands),
      "known_natal_individuals":len(natal),
      "producer_ID_and_hatchyear_consistency_counts":dict(known),
      "producer_record_year_relative_to_observed_nest_birth":dict(hatch_offsets),
      "previous_v1_233_natal_ID_overlap_without_year_matching":492,
      "previous_v1_233_nextyear_immigrant_exact_producer_matches":0,
      "previous_v1_233_nextyear_resident_exact_producer_matches":0,
      "known_2007_2014_immigrant_origin_IDs":len(immigrant_origin),
      "observed_migrant_IDs_with_ANY_later_producer_row_at_same_destination":len(IDs_matched_migration_destination),
      "breeder_output_measurements_read":False,
      "ID_collision_if_hatchyear_inconsistent_must_block_linked_effect":True,
      "observed_captured_adult_is_not_successful_offspring_producer":True,
      "frozen_v231_and_v232_resight_results_unchanged":True,
      "no_model_fitted_or_true_rescue_inferred":True,
      "original_529_mammal_heldout_unopened":True,
      "eBird_used":False,"GEB_scientific_HOLD":True
    }
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("author",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();root=a.author/"Data"
    result=compute((root/"presence_data_1994_2022.txt").read_bytes(),
       (root/"estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt").read_bytes(),
       (root/"nestling_producers_2007_2014.txt").read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
