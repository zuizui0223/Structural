#!/usr/bin/env python3
"""Source-only two-author-release Finnish beetle site-year identity crosswalk.

2022 original species matrix: header read ONLY.
2023 original covariate table: inspect ONLY original rowID/Site/Year fields.
Never inspect beetle capture rows, traits or numerical environmental values.
No individual source IDs are returned, logged, uploaded, or committed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

SOURCE_2022 = ("Finland_sites.species.csv", "c373ec9f597311a636b4f83d39fcfc9d")
SOURCE_2023 = ("Site_covariates.csv", "557451999b19335cbe8058a985d85363")
OLD_SAMPLE_COLUMNS = 153
NEW_AUTHOR_ROWS = 142
YEAR_PREFIX = re.compile(r"^((?:19[89][0-9]|20[0-2][0-9]))_(.+)$")


class ScientificStop(Exception):
    pass


def pinned(path: Path, digest: str):
    if not path.is_file():
        raise ScientificStop("SOURCE_STOP_MISSING_REQUIRED_AUTHOR_ARCHIVE")
    h = hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    if h.hexdigest() != digest:
        raise ScientificStop("SOURCE_STOP_PUBLISHED_FILE_VERSION_MD5_MISMATCH")


def source22_header_only(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        labels = next(csv.reader(f), [])[1:]
    if len(labels) != OLD_SAMPLE_COLUMNS or len(set(labels)) != len(labels) or not all(labels):
        raise ScientificStop("SOURCE_STOP_2022_ORIGINAL_153_UNIQUE_HEADER_DRIFT")
    parsed = []
    for x in labels:
        m = YEAR_PREFIX.fullmatch(x)
        if m is None:
            raise ScientificStop("SOURCE_STOP_2022_YEAR_PREFIX_NOT_EXPLICIT")
        parsed.append((x, m.group(2), int(m.group(1))))
    return parsed


def source23_author_identity_fields_only(path: Path):
    """CSV rows parsed; only author Site, Year, rowID fields are accessed."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if not all(x in header for x in ("rowID", "Site", "Year")):
            raise ScientificStop("SOURCE_STOP_2023_ROWID_SITE_YEAR_MISSING")
        idx = {k: header.index(k) for k in ("rowID", "Site", "Year")}
        records = []
        for row in reader:
            if len(row) != len(header):
                raise ScientificStop("SOURCE_STOP_2023_AUTHOR_COVARIATE_CSV_SCHEMA")
            rowid, site, year = (row[idx[k]].strip() for k in ("rowID", "Site", "Year"))
            if not rowid or not site or not re.fullmatch(r"(?:19[89][0-9]|20[0-2][0-9])", year):
                raise ScientificStop("SOURCE_STOP_2023_SOURCE_AUTHOR_ID_INVALID")
            # This is observed from the publicly published original CSV before
            # any biological outcome. Do not reverse/change it to improve a match.
            if rowid != year + "_" + site:
                raise ScientificStop("SOURCE_STOP_2023_AUTHOR_ROWID_YEAR_SITE_MISMATCH")
            records.append((rowid, site, int(year)))
    if len(records) != NEW_AUTHOR_ROWS:
        raise ScientificStop("SOURCE_STOP_2023_AUTHOR_142_SITEYEAR_ROW_DRIFT")
    rowids = [x[0] for x in records]
    if len(set(rowids)) != len(rowids):
        raise ScientificStop("SOURCE_STOP_2023_AUTHOR_DUPLICATE_SITEYEAR")
    return records


def compare(old, new):
    oldkeys = set(x[0] for x in old)
    oldsites = set(x[1] for x in old)
    newkeys = set(x[0] for x in new)
    newsites = set(x[1] for x in new)
    oldcnt = Counter(x[1] for x in old)
    newcnt = Counter(x[1] for x in new)
    if len(oldkeys) != len(old) or len(newkeys) != len(new):
        raise ScientificStop("SOURCE_STOP_NONUNIQUE_AUTHOR_ID_KEY")
    matches = oldkeys & newkeys
    unmatched = oldkeys - newkeys
    known_sites_unmatched = sum(next(site for label, site, yr in old if label == key) in newsites for key in unmatched)
    # All IDs are used only inside private runner; release aggregate counts.
    out = {
        "source_2022_original_sample_year_columns": len(old),
        "source_2022_candidate_unique_non_year_tokens": len(oldsites),
        "source_2022_candidate_repeated_site_tokens": sum(v>1 for v in oldcnt.values()),
        "source_2022_repeated_event_excess": len(old) - len(oldsites),
        "source_2023_author_site_year_rows": len(new),
        "source_2023_author_unique_Site_fields": len(newsites),
        "source_2023_author_repeated_Site_fields": sum(v>1 for v in newcnt.values()),
        "same_exact_original_year_site_rows_in_both_author_releases": len(matches),
        "2022_sample_year_labels_not_in_2023_author_table": len(unmatched),
        "2023_author_rowIDs_not_in_2022_sample_headers": len(newkeys-oldkeys),
        "2022_sample_years_unmatched_but_Site_known_in_2023": known_sites_unmatched,
        "2022_unmatched_sample_years_with_Site_not_in_2023": len(unmatched)-known_sites_unmatched,
        "2022_site_base_tokens_present_in_2023_author_Site": len(oldsites & newsites),
        "2022_site_base_tokens_absent_in_2023_author_Site": len(oldsites-newsites),
        "2023_author_Site_not_among_2022_candidate_bases": len(newsites-oldsites),
        "source_year_and_site_author_contract_passed": True,
        "source_original_beetle_species_rows_unopened": True,
        "source_2023_environmental_numbers_uninspected": True,
        "source_original_site_year_keys_not_reexported": True,
        "site_cluster_taxon_or_guild_rescoring_not_performed": True,
        "full_original_2022_physical_site_crosswalk_author_verified": False,
    }
    # Full coverage would be necessary but still not a standalone proof of
    # physical forest plot identity across source projects.
    out["source_2023_author_metadata_matches_all_153_2022_events"] = (
        len(matches) == OLD_SAMPLE_COLUMNS
    )
    out["status"] = (
        "SOURCE_ONLY_EXACT_AUTHOR_ROWID_MATCH_FULL_BUT_SOURCE_PROJECT_GATE_STILL_REQUIRED"
        if out["source_2023_author_metadata_matches_all_153_2022_events"]
        else "SOURCE_ONLY_PARTIAL_AUTHOR_SITE_YEAR_CROSSWALK_NO_FULL_PHYSICAL_SITE_MERGE"
    )
    return out


def synthetic():
    old = [("1993_SYNTH_Q987", "SYNTH_Q987", 1993),
           ("2002_SYNTH_Q987", "SYNTH_Q987", 2002),
           ("2002_SYNTH_B321", "SYNTH_B321", 2002)]
    new = [("1993_SYNTH_Q987", "SYNTH_Q987", 1993),
           ("2002_SYNTH_B321", "SYNTH_B321", 2002)]
    r = compare(old, new)
    assert r["same_exact_original_year_site_rows_in_both_author_releases"] == 2
    assert r["2022_sample_years_unmatched_but_Site_known_in_2023"] == 1
    assert not r["full_original_2022_physical_site_crosswalk_author_verified"]
    assert r["status"].startswith("SOURCE_ONLY_PARTIAL")
    print("SYNTHETIC_SOURCE_ONLY_CROSSWALK_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--folder", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    synthetic()
    if a.test:
        return
    if a.folder is None or a.out is None:
        ap.error("--folder and --out required")
    out = {
        "schema": "structural.Finland_2022Zenodo5950610_2023Zenodo8322080_author_yearsite_crosswalk.v1",
        "source_2022_DOI": "10.5281/zenodo.5950610",
        "source_2023_independent_author_data_release_DOI": "10.5281/zenodo.8322080",
        "same_original_Finnish_biology_not_new_independent_forest_cohort": True,
        "source_pin_files_md5_checked": False,
        "author_original_site_IDs_species_environmental_values_not_exported": True,
        "prior_hostguild_D_0p091059_p_0p000333_unchanged": True,
        "prior_PREDICTS_NEON_BALA_GEB_seals_unchanged": True,
        "eBird_used": False,
    }
    try:
        p22 = a.folder / SOURCE_2022[0]
        p23 = a.folder / SOURCE_2023[0]
        pinned(p22, SOURCE_2022[1])
        pinned(p23, SOURCE_2023[1])
        out["source_pin_files_md5_checked"] = True
        old = source22_header_only(p22)
        new = source23_author_identity_fields_only(p23)
        out["author_source_identity_comparison"] = compare(old,new)
        out["status"] = out["author_source_identity_comparison"]["status"]
    except ScientificStop as exc:
        out["status"] = str(exc)
        out["source_schema_or_access_STOP_not_biological_null"] = True
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "finland_2022_2023_author_sourceonly_crosswalk.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
