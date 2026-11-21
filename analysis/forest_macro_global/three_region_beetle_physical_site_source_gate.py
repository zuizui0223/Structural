#!/usr/bin/env python3
"""Author-native physical-site identity audit for Zenodo 5950610.

Only original matrix FILE HEADERS are parsed. Body bytes are MD5-hashed but
never decoded, and source sampling labels never leave the runner.
This is source-method QC, not a biological test or an automatic site merger.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

MANIFEST = {
    "Finland": ("Finland_sites.species.csv", "c373ec9f597311a636b4f83d39fcfc9d", 153, 142),
    "Germany": ("Germany_sites.species.csv", "0ab85a1e30e8c9cc52d08255c6cd9c16", 386, 386),
    "Norway": ("Norway_sites.species.csv", "2320412a2d87e68bb79d1ccf86829bf0", 1111, 468),
}
YEAR = r"(?:19[89][0-9]|20[0-2][0-9])"
SEP = r"[_./:\\s-]"
PREFIX = re.compile(r"^(" + YEAR + r")(" + SEP + r")(.+)$")
SUFFIX = re.compile(r"^(.+)(" + SEP + r")(" + YEAR + r")$")
TOKEN_YEAR = re.compile(r"(^|" + SEP + r")(" + YEAR + r")(?=$|" + SEP + r")")
CHAR_SEGMENTS = re.compile(r"[A-Za-z]+|[0-9]+|[^A-Za-z0-9]+")


class ScientificStop(RuntimeError):
    pass


def signature(label: str) -> str:
    """Anonymize all literal alphabetic/numeric source content."""
    out = []
    for m in CHAR_SEGMENTS.finditer(label):
        t = m.group()
        if t[0].isalpha():
            out.append("L" + str(len(t)))
        elif t[0].isdigit():
            out.append("D" + str(len(t)))
        else:
            out.append("S" + str(len(t)))
    return ".".join(out)[:110]


def pair_year_base(label: str, mode: str):
    if mode == "prefix":
        m = PREFIX.fullmatch(label)
        return (m.group(3), int(m.group(1))) if m else None
    if mode == "suffix":
        m = SUFFIX.fullmatch(label)
        return (m.group(1), int(m.group(3))) if m else None
    if mode == "token":
        found = list(TOKEN_YEAR.finditer(label))
        if len(found) != 1:
            return None
        m = found[0]
        year = int(m.group(2))
        # Remove the exact year and one adjacent separator; never shorten
        # other digits or guess which tokens represent projects/sites.
        if m.start(2) > 0:
            base = label[:m.start(2)-1] + label[m.end(2):]
        else:
            base = label[m.end(2)+1:]
        return (base, year) if base else None
    raise ValueError(mode)


def group_candidate(labels, mode, author_expected):
    matched = [pair_year_base(v, mode) for v in labels]
    ok = [x for x in matched if x is not None]
    out = {
        "method": mode,
        "explicit_year_token_labels": len(ok),
        "all_source_labels_covered": len(ok) == len(labels),
        "source_sample_count": len(labels),
        "published_author_physical_site_count": author_expected,
        "site_key_author_verified": False,
        "physical_site_merge_or_response_scoring_allowed": False,
    }
    if len(ok) == len(labels):
        groups = collections.defaultdict(set)
        for base, year in ok:
            groups[base].add(year)
        counts = collections.Counter(base for base, year in ok)
        out.update({
            "candidate_unique_bases_not_author_verified": len(groups),
            "candidate_total_repeated_event_excess": len(labels)-len(groups),
            "candidate_bases_with_repeated_source_event_labels": sum(v>1 for v in counts.values()),
            "candidate_max_source_events_per_base": max(counts.values(), default=0),
            "candidate_bases_with_distinct_years": sum(len(ys)>1 for ys in groups.values()),
            "candidate_unique_base_count_matches_author_report": len(groups)==author_expected,
        })
    return out


def original_headers(folder: Path):
    receipt = {}
    for country, (filename, expected_md5, n_expected, n_physical) in MANIFEST.items():
        path = folder / filename
        if not path.is_file():
            raise ScientificStop("SCIENTIFIC_STOP_AUTHOR_SOURCE_MATRIX_UNAVAILABLE")
        dig = hashlib.md5()
        with path.open("rb") as f:
            while (block := f.read(131072)):
                dig.update(block)
        if dig.hexdigest() != expected_md5:
            raise ScientificStop("SCIENTIFIC_STOP_AUTHOR_ORIGINAL_MATRIX_MD5_DRIFT")
        # Next/first line only; NO source species row or taxon/count opened.
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            header = next(csv.reader(f), [])
        if not header or len(header) != n_expected+1:
            raise ScientificStop("SCIENTIFIC_STOP_AUTHOR_ORIGINAL_COUNTRY_SAMPLE_COLUMN_COUNT_DRIFT")
        labels = header[1:]
        if any(not x.strip() for x in labels) or len(set(labels)) != len(labels):
            raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_SAMPLING_LABEL_DUPLICATE_OR_MISSING")
        sigs = collections.Counter(signature(label) for label in labels)
        # Lexical pattern *counts*, no strings recovered or exported.
        lengths = sorted(map(len, labels))
        year_presence = sum(pair_year_base(v, "token") is not None for v in labels)
        candidate = {
            method: group_candidate(labels, method, n_physical)
            for method in ("prefix", "suffix", "token")
        }
        receipt[country] = {
            "published_author_physical_sites": n_physical,
            "observed_original_sampling_columns": len(labels),
            "md5_matches_frozen_zenodo_v1": True,
            "sampling_labels_all_unique": True,
            "calendar_year_token_lexical_coverage": year_presence,
            "source_label_length_min_median_max": [
                lengths[0], lengths[len(lengths)//2], lengths[-1]
            ],
            "anonymized_lexical_signature_counts": [
                {"signature": k, "sample_columns": v}
                for k, v in sigs.most_common(12)
            ],
            "year_token_candidate_groupings_NOT_AUTHOR_VALIDATED": candidate,
            "biological_values_or_species_rows_parsed": False,
            "all_site_identity_inference_blocked_until_author_crosswalk": True,
        }
    return {
        "schema": "structural.Zenodo5950610_author_physical_site_header_only_gate.v1",
        "source_doI": "10.5281/zenodo.5950610",
        "separate_original_field_covariates_DOI": "10.5061/dryad.tmpg4f50b",
        "status": "SOURCE_LABEL_SYNTAX_AUDITED_AUTHOR_SITE_IDENTITY_STILL_REQUIRED",
        "source_original_species_and_abundance_values_unopened": True,
        "source_site_labels_not_reexported": True,
        "only_lexical_structure_and_candidate_counts_not_original_sites": True,
        "candidate_exact_site_count_match_cannot_validate_physical_identity": True,
        "old_hostguild_D_0p091059_p_0p000333_UNCHANGED": True,
        "original_PREDICTS_NEON_BALA_GEB_frozen": True,
        "eBird_used": False,
        "country": receipt,
    }


def synthetic_test():
    a = ["2010_A12", "2011_A12", "2012_B7"]
    assert all(pair_year_base(v, "prefix") for v in a)
    p = group_candidate(a, "prefix", 2)
    assert p["candidate_unique_bases_not_author_verified"]==2
    assert p["candidate_bases_with_repeated_source_event_labels"]==1
    assert p["candidate_bases_with_distinct_years"]==1
    assert p["candidate_unique_base_count_matches_author_report"]
    assert not p["physical_site_merge_or_response_scoring_allowed"]
    b = ["siteA-2017","siteA-2018","siteB-2018"]
    assert group_candidate(b, "suffix", 2)["candidate_unique_bases_not_author_verified"]==2
    assert group_candidate(b, "token", 2)["candidate_unique_bases_not_author_verified"]==2
    assert group_candidate(["ABC01", "DEF02"], "prefix", 2)["explicit_year_token_labels"]==0
    assert signature("NO42_2018")=="L2.D2.S1.D4"
    assert "A12" not in signature("2010_A12")
    assert pair_year_base("some2002mid", "token") is None
    assert pair_year_base("A_2019_2020", "token") is None
    print("SOURCE_ONLY_SYNTHETIC_PASS_year_parsing_repeats_no_biology")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--folder", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    synthetic_test()
    if args.test:
        return
    if not args.folder or not args.out:
        ap.error("--folder and --out are required unless --test")
    try:
        result = original_headers(args.folder)
    except ScientificStop as err:
        result = {
            "schema": "structural.Zenodo5950610_author_physical_site_header_only_gate.v1",
            "status": str(err),
            "no_original_biological_response_values_scored": True,
            "no_source_site_identity_claim": True,
        }
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "three_country_physical_site_identity_sourceonly.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
