#!/usr/bin/env python3
"""BETA-FOR original 594 source sampling frame: method-ID rows ONLY.

The sole permitted original member is BETAFOR_information.csv, MD5 verified.
No original OTU/species/biological endpoint files are downloaded or opened.
Original rows, source IDs, date values and coordinates are never exported.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import io
import json
import math
import re
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import get_official_metadata_only, SourceStop
from betafor11_v2_missingversion_firstheader_sourceonly import validate_publisher_v2
from betafor11_information_firstheader_gate import source_publisher_file_link, official_original_file_bytes

PRESPEC = "docs/FOREST_MACRO_BETAFOR11_594_SAMPLE_OPPORTUNITY_IDONLY_PREFREEZE_20261120.md"
HEADER = ("patch","sample","firstday","lastday","meanday","treatment","X","Y")
SITE_CODES = ("B04","B05","B06","B07","U01","U02","U03","P08","H09","S10","L11")
SITE_REGEX = re.compile(r"^(B04|B05|B06|B07|U01|U02|U03|P08|H09|S10|L11)[A-Za-z0-9_-]+$")
REGION_GROUP = {
    "B04":"Bavarian", "B05":"Bavarian", "B06":"Bavarian", "B07":"Bavarian",
    "U01":"Sailershausen", "U02":"Sailershausen", "U03":"Sailershausen",
    "P08":"Passau", "H09":"Hunsruck", "S10":"Saarland", "L11":"Lubeck",
}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,80}$")
TREATMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. +-]{0,75}$")


def date_class(s):
    t = s.strip()
    if not t:
        return "missing"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}",t):
        return "iso_date"
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}",t):
        return "dot_date"
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}",t):
        return "slash_date"
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",t):
        return "numeric"
    if re.fullmatch(r"[A-Za-z0-9: T+._/-]{1,45}",t):
        return "other_safe_datetime_token"
    return "unknown_time_format"


def float_or_none(s):
    try:
        v=float(s)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError, OverflowError):
        return None


def inspect_source_method_rows(raw, *, expected_rows=594, expected_patches=99,
                               expected_repeats=6, expected_sites=11,
                               expected_regions=6, expected_patches_per_site=9):
    # Source is known original verified semicolon, not an outcome/OTU file.
    try:
        f = io.StringIO(raw.decode("utf-8-sig",errors="strict"), newline="")
    except UnicodeError:
        raise SourceStop("ORIGINAL_INFORMATION_ROWS_NOT_UTF8") from None
    rd = csv.reader(f, delimiter=";", strict=True)
    try:
        header = tuple(next(rd))
    except (StopIteration, csv.Error):
        raise SourceStop("ORIGINAL_INFORMATION_ROW_HEADER_NOT_PARSEABLE") from None
    if header != HEADER:
        raise SourceStop("ORIGINAL_INFORMATION_EIGHT_HEADERS_NOT_FROZEN_ORDER")
    patch_samples=defaultdict(set)
    patch_treatments=defaultdict(set)
    site_patches=defaultdict(set)
    site_treatments=defaultdict(set)
    patch_coords=defaultdict(set)
    missing=Counter()
    dates={c:Counter() for c in ("firstday","lastday","meanday")}
    coordinate_two_finite=0
    site_prefix_failures=0
    duplicate_patch_sample=0
    rows=0
    try:
        for cells in rd:
            if len(cells)!=8:
                raise SourceStop("ORIGINAL_INFORMATION_NON_EIGHT_CELL_ROW")
            row=dict(zip(HEADER,cells))
            rows+=1
            patch=row["patch"].strip()
            sample=row["sample"].strip()
            treat=row["treatment"].strip()
            if not ID.fullmatch(patch) or not ID.fullmatch(sample):
                raise SourceStop("ORIGINAL_INFORMATION_UNSAFE_OR_EMPTY_ID")
            if not TREATMENT.fullmatch(treat):
                raise SourceStop("ORIGINAL_INFORMATION_UNSAFE_OR_EMPTY_TREATMENT")
            if sample in patch_samples[patch]:
                duplicate_patch_sample+=1
            patch_samples[patch].add(sample)
            patch_treatments[patch].add(treat)
            for c in dates:
                cls=date_class(row[c])
                dates[c][cls]+=1
                if cls=="missing":
                    missing[c]+=1
            x=float_or_none(row["X"]); y=float_or_none(row["Y"])
            if x is not None and y is not None:
                coordinate_two_finite+=1
                patch_coords[patch].add((x,y))
            else:
                if x is None: missing["X"]+=1
                if y is None: missing["Y"]+=1
            m=SITE_REGEX.match(patch)
            if m is None:
                site_prefix_failures+=1
            else:
                code=m.group(1)
                site_patches[code].add(patch)
                site_treatments[code].add(treat)
    except csv.Error:
        raise SourceStop("ORIGINAL_INFORMATION_CSV_BODY_PARSE_FAILED") from None

    n_patches=len(patch_samples)
    repeats=Counter(len(s) for s in patch_samples.values())
    stable_treat=all(len(z)==1 for z in patch_treatments.values())
    by_site_counts=Counter(len(z) for z in site_patches.values())
    by_site_treat_counts=Counter(len(z) for z in site_treatments.values())
    n_regions=len(set(REGION_GROUP[k] for k in site_patches))
    n_same_coords=sum(1 for vals in patch_coords.values() if len(vals)==1)
    n_coordinate_eligible=sum(1 for vals in patch_coords.values() if vals)
    no_missing = all(missing[c]==0 for c in dates)
    physical_frame_ok=(
        rows==expected_rows and n_patches==expected_patches
        and len(patch_samples)==len(patch_treatments)
        and repeats==Counter({expected_repeats: expected_patches})
        and duplicate_patch_sample==0 and stable_treat
    )
    site_frame_ok=(
        site_prefix_failures==0 and len(site_patches)==expected_sites
        and set(site_patches)==set(SITE_CODES)
        and n_regions==expected_regions
        and by_site_counts==Counter({expected_patches_per_site:expected_sites})
        and by_site_treat_counts==Counter({expected_patches_per_site:expected_sites})
    )
    # Source opportunity is only SOURCE-METHOD eligible if first two gates pass.
    status = (
        "ORIGINAL_BETAFOR11_SOURCE_SAMPLE_FRAME_AND_SITE_PREFIX_CANDIDATES_PASS_NOT_BIOLOGY"
        if physical_frame_ok and site_frame_ok else
        "ORIGINAL_BETAFOR11_SITE_PREFIX_ID_UNVERIFIED_SOURCE_HOLD"
        if physical_frame_ok else
        "ORIGINAL_BETAFOR11_SAMPLING_OPPORTUNITY_FRAME_MISMATCH_SOURCE_STOP"
    )
    return {
        "schema":"structural.BETAFOR11_2025_sample_ID_only_source_audit.v1",
        "status": status,
        "observed_original_source_sample_metadata_rows": rows,
        "distinct_original_physical_patch_identifiers": n_patches,
        "distinct_original_patch_sample_keys": sum(map(len,patch_samples.values())),
        "source_duplicate_patch_sample_keys": duplicate_patch_sample,
        "distinct_samples_per_patch_distribution_anonymous": dict(sorted(repeats.items())),
        "each_patch_has_one_source_treatment": stable_treat,
        "published_11_site_prefix_regex_rows_not_qualified": site_prefix_failures,
        "source_exact_published_site_prefixes_found": len(site_patches),
        "source_distinct_published_region_groups_if_ID_valid": (
            n_regions if site_prefix_failures==0 else None),
        "source_patch_count_per_mapped_site_frequency": (
            dict(sorted(by_site_counts.items())) if site_prefix_failures==0 else None),
        "source_treatment_count_per_mapped_site_frequency": (
            dict(sorted(by_site_treat_counts.items())) if site_prefix_failures==0 else None),
        "original_all_method_time_field_nonblank": no_missing,
        "original_published_date_field_syntax_counts": {
            k:dict(sorted(v.items())) for k,v in dates.items()},
        "source_XY_both_finite_rows": coordinate_two_finite,
        "source_patches_with_finite_XY": n_coordinate_eligible,
        "source_patches_with_single_identical_finite_XY": n_same_coords,
        "source_XY_projection_and_precision_NOT_IDENTIFIED": True,
        "original_source_missing_metadata_field_counts": dict(sorted(missing.items())),
        "original_99x6_physical_sampling_frame_pass": physical_frame_ok,
        "original_11forest_6region_prefix_9patch_treatment_source_candidate_pass": site_frame_ok,
        "original_dates_and_effort_separate_author_codebook_NOT_verified": True,
        "original_information_raw_id_treatment_timestamp_XY_values_NOT_EXPORTED": True,
        "original_OTU_response_or_species_values_READ": 0,
        "new_ecological_effects_fitted": 0,
    }


def run():
    record=get_official_metadata_only()
    provenance=validate_publisher_v2(record)
    if not provenance["original_six_filenames_MD5s_and_sizes_verified"]:
        raise SourceStop("ORIGINAL_PUBLISHER_FINGERPRINT_CHANGED")
    link,size=source_publisher_file_link(record)
    raw=official_original_file_bytes(link,size)
    result=inspect_source_method_rows(raw)
    result["original_versioned_publisher_member_MD5_and_size_verified"]=True
    result["original_one_information_member_GET_only"]=True
    result["original_other_five_members_NOT_DOWNLOADED"]=True
    return result


def synthetic():
    def make(npatch=2,nsamp=3,bad_duplicate=False):
        rows=[HEADER]
        for patchi in range(npatch):
            p=("B04" if patchi==0 else "U01")+f"_P{patchi+1}"
            for sample in range(nsamp):
                sm = str(sample if not bad_duplicate else 0)
                rows.append((p,sm,"2022-05-01","2022-05-14","2022-05-07",
                             "TR"+str(patchi+1), "23.4","45.6"))
        return ("\n".join(";".join(x) for x in rows)+"\n").encode()
    q=inspect_source_method_rows(make(),expected_rows=6,expected_patches=2,
                                 expected_repeats=3,expected_sites=2,
                                 expected_regions=2,expected_patches_per_site=1)
    assert q["original_99x6_physical_sampling_frame_pass"]
    assert not q["original_11forest_6region_prefix_9patch_treatment_source_candidate_pass"]
    assert q["original_OTU_response_or_species_values_READ"]==0
    q2=inspect_source_method_rows(make(bad_duplicate=True),expected_rows=6,
                                  expected_patches=2,expected_repeats=3)
    assert not q2["original_99x6_physical_sampling_frame_pass"]
    assert q2["source_duplicate_patch_sample_keys"]>0
    assert date_class("2022-05-01")=="iso_date"
    print("SYNTHETIC_BETAFOR11_SOURCE_METADATA_ONLY_ROW_FRAME_AND_STOP_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out needed")
    report={
        "schema":"structural.BETAFOR11_594_original_source_sampling_frame_onepass.v1",
        "prespec": PRESPEC,
        "source_original_file_requested":"BETAFOR_information.csv",
        "original_OTU_or_biodiversity_files_requested":0,
        "original_biodiversity_raw_values_read":0,
        "new_ecological_estimates":0,
        "prior_v1_version_STOP_and_v2_header_HOLD_unchanged":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        data=run()
        report["method_source_only"]=data
        report["status"]=data["status"]
    except SourceStop as ex:
        report["status"]="SOURCE_SAMPLE_FRAME_STOP_"+str(ex)
        report["source_STOP_not_biological_null"]=True
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_594_PUBLISHED_METHOD_SOURCE_OPPORTUNITIES",report["status"])
    print("SOURCE_ONLY_NO_ORIGINAL_OTU_DATA_OR_ECOLOGICAL_FITS")


if __name__=="__main__":
    main()
