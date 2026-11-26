#!/usr/bin/env python3
"""BETA-FOR 99-patch A/D four resource treatment pairing: method metadata ONLY."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import io
import json
import math
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import get_official_metadata_only, SourceStop
from betafor11_v2_missingversion_firstheader_sourceonly import validate_publisher_v2
from betafor11_information_firstheader_gate import source_publisher_file_link, official_original_file_bytes

PRESPEC="docs/FOREST_MACRO_BETAFOR11_AUTHOR_TREATMENT_PAIR_SOURCE_PREFREEZE_20261120.md"
CODES=frozenset(("CC","AW","AL","AS","AB","DW","DL","DS","DB"))
SITE_CODES=frozenset(("B04","B05","B06","B07","U01","U02","U03","P08","H09","S10","L11"))
COLS=["patch","sample","firstday","lastday","meanday","treatment","X","Y"]


def read_method_only(raw):
    try:
        rd=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                          delimiter=";",strict=True)
        if rd.fieldnames!=COLS:
            raise SourceStop("TREATMENT_ORIGINAL_FIELD_ORDER_DRIFT")
        grouped=defaultdict(list)
        seen=set()
        total=0
        mismatched_code=0
        invalid_time=0
        inversions=0
        missing_study_labels=0
        for row in rd:
            total+=1
            if row.get(None) is not None:
                raise SourceStop("TREATMENT_ORIGINAL_ROW_COLUMNS_WRONG")
            patch=row["patch"].strip();sample=row["sample"].strip()
            treat=row["treatment"].strip()
            if not patch or not sample or (patch,sample) in seen:
                raise SourceStop("TREATMENT_ORIGINAL_SAMPLING_UNIQUE_KEY_STOP")
            seen.add((patch,sample))
            site=patch[:3]
            if site not in SITE_CODES:
                missing_study_labels+=1
            # This exact R substr(rownames(df),5,6) rule is frozen from
            # original author code, not a post-outcome string choice.
            if len(patch)<6 or patch[4:6] != treat or treat not in CODES:
                mismatched_code+=1
            def num(s):
                try:
                    v=float(s)
                    return v if math.isfinite(v) else None
                except (ValueError,OverflowError,TypeError): return None
            first=num(row["firstday"]);last=num(row["lastday"])
            if first is None or last is None:
                invalid_time+=1
            elif first>last:
                inversions+=1
            grouped[patch].append((sample,treat,site,first,last))
    except (UnicodeError,csv.Error):
        raise SourceStop("TREATMENT_ORIGINAL_CSV_METADATA_UNREADABLE") from None
    site_patches=defaultdict(set)
    site_treatments=defaultdict(set)
    bad_patch_treatment=0
    repeated_or_missing_periods=0
    duplicate_firstday_within_patch=0
    for p,rows in grouped.items():
        site=rows[0][2]
        site_patches[site].add(p)
        site_treatments[site].add(rows[0][1])
        if len(set(x[1] for x in rows))!=1:
            bad_patch_treatment+=1
        if len(rows)!=6 or len(set(x[0] for x in rows))!=6:
            repeated_or_missing_periods+=1
        days=[x[3] for x in rows]
        if any(t is None for t in days) or len(set(days))!=6:
            duplicate_firstday_within_patch+=1
    complete_source_design=(
        total==594 and len(grouped)==99 and len(seen)==594
        and len(site_patches)==11 and set(site_patches)==SITE_CODES
        and all(len(site_patches[s])==9 and site_treatments[s]==CODES
                for s in SITE_CODES)
        and mismatched_code==0 and missing_study_labels==0
        and bad_patch_treatment==0 and repeated_or_missing_periods==0
    )
    chronological=invalid_time==0 and inversions==0 and duplicate_firstday_within_patch==0
    status=(
        "SOURCE_TREATMENT_4PAIR_METHOD_READY_CHRONOLOGY_READY_NO_BIOLOGY"
        if complete_source_design and chronological else
        "SOURCE_TIME_CHRONOLOGY_HOLD_TREATMENT_FRAME_PASS"
        if complete_source_design else
        "SOURCE_TREATMENT_PAIRING_HOLD_NOT_A_BIOLOGICAL_NULL"
    )
    return {
        "status":status,
        "source_original_method_rows":total,
        "physical_unique_patches":len(grouped),
        "original_patch_sample_pairs":len(seen),
        "author_expected_11forest_9treatment_4_AD_resource_pairs_PASS":complete_source_design,
        "original_author_patch_substr_5_to_6_disagreements":mismatched_code,
        "source_unrecognized_site_prefix_rows":missing_study_labels,
        "source_patch_treatment_label_inconsistent_patches":bad_patch_treatment,
        "source_not_six_unique_sample_period_patches":repeated_or_missing_periods,
        "original_numeric_firstday_or_lastday_invalid":invalid_time,
        "original_firstday_greater_than_lastday_rows":inversions,
        "original_patch_firstday_nonunique_or_unparsed":duplicate_firstday_within_patch,
        "original_valid_six_period_strict_order_PER_PATCH":chronological,
        "source_original_dates_and_treatment_ID_values_NOT_EXPORTED":True,
        "original_OTU_and_species_response_rows_parsed":0,
        "new_ecological_estimands_estimated":0,
    }


def run():
    doc=get_official_metadata_only()
    v2=validate_publisher_v2(doc)
    if not v2["original_six_filenames_MD5s_and_sizes_verified"]:
        raise SourceStop("ORIGINAL_PUBLISHER_6_FILE_MD5_DRIFT")
    link,size=source_publisher_file_link(doc)
    raw=official_original_file_bytes(link,size)
    q=read_method_only(raw)
    q["original_source_MD5_size_verified"] = True
    q["original_only_information_file_requested"] = True
    return q


def synthetic():
    rows=[COLS]
    for t in ("AW","DW","CC"):
        for i in range(6):
            rows.append((f"B04_{t}",str(i+1),str(i+1),str(i+2),str(i+1.5),t,"",""))
    got=read_method_only(("\n".join(";".join(row) for row in rows)+"\n").encode())
    assert got["source_original_method_rows"]==18
    assert got["source_not_six_unique_sample_period_patches"]==0
    assert got["original_numeric_firstday_or_lastday_invalid"]==0
    assert got["source_patch_treatment_label_inconsistent_patches"]==0
    assert not got["author_expected_11forest_9treatment_4_AD_resource_pairs_PASS"]
    assert "B04_AW" not in json.dumps(got)
    print("SYNTHETIC_BETAFOR11_TREATMENT_4PAIR_SOURCE_METHOD_SAFEGUARD_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out needed")
    result={
        "schema":"structural.BETAFOR11_original_treatment_4paired_resource_method_v1",
        "prespec":PRESPEC,
        "original_organism_OTU_abundance_rows_read":0,
        "new_biodiversity_model_fits":0,
        "original_forest_99_and_island_source_seals_unmodified":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        result["source_method"]=run()
        result["status"]=result["source_method"]["status"]
    except SourceStop as e:
        result["status"]="SOURCE_TREATMENT_METADATA_STOP_"+str(e)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_AUTHOR_TREATMENT_PAIR_SOURCE",result["status"])
    print("ORIGINAL_OTU_RESPONSE_ROWS=0; NO_NEW_BIOLOGICAL_EFFECT")


if __name__=="__main__":
    main()
