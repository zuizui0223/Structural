#!/usr/bin/env python3
"""BELongDead 20406/tag2 original German METHOD VALUES ONLY, no biology.

A precommitted source-only method/occasion feasibility audit. Never requests
original 31123/31124, species, abundance or wood quantities and never exports
source plot/log/status/method names or field row values.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from belongdead_author_alias_naming_source_gate import NoRedirect

URL = "https://www.bexis.uni-jena.de/api/data/20406/tag/2"
SHA = "9bf68312668065a5d533fbbe65b22e9aef45b32f0d146921ab45e5133354b13f"
BYTES = 2717980
PRESPEC = "docs/FOREST_BELONGDEAD_20406_AUTHOR_GERMAN_METHOD_STATUS_PRESPEC_20261118.md"
HEADER = (
    "ID", "PLOT", "SUBPLOT", "Intensitaet_Subplot",
    "StammNR", "AG", "Jahr", "PositionaufStamm_cm",
    "AusdehnungaufStamm_cm", "Variable", "Methode",
    "Equipment", "wann", "Status",
)
# Exactly the four allowed original author method-text columns, no numeric wood.
TEXT_FIELDS = ("Variable", "Methode", "Equipment", "Status")
QUAL_FIELDS = TEXT_FIELDS + ("wann",)
KEY_FIELDS = ("PLOT", "SUBPLOT", "StammNR")
TIME_FIELD = "Jahr"
METHOD_REGEX = {
    "emergence_eclector": re.compile(
        r"eklekt|eclect|emergenz|emergence", re.IGNORECASE
    ),
    "other_trap": re.compile(
        r"falle|fallen|trap|pitfall|flight.?intercept", re.IGNORECASE
    ),
    "trap_deployment": re.compile(
        r"aufgestellt|montiert|installiert|angebracht|ausgebracht|deployed",
        re.IGNORECASE,
    ),
    "trap_collection_or_removal": re.compile(
        r"abgebaut|entnommen|entfernt|geleert|eingesammelt|removed",
        re.IGNORECASE,
    ),
    "trap_failure": re.compile(
        r"defekt|ausfall|kaputt|zerstört|zerstoert|missing.?trap|damaged.?trap",
        re.IGNORECASE,
    ),
    "explicit_zero_capture": re.compile(
        r"kein.{0,12}fang|ohne.{0,12}fang|zero.?catch|no.?catch",
        re.IGNORECASE,
    ),
    "sampling_time_or_effort": re.compile(
        r"beprobung|probenahme|sammeldauer|fangperiode|trap.?days|sampling.?effort",
        re.IGNORECASE,
    ),
    "forest_log_measurement": re.compile(
        r"durchmesser|stamm|rinde|zerfall|holz|log.?inventory",
        re.IGNORECASE,
    ),
}
UNKNOWN = {"", "na", "nan", "null", "missing"}


class SourceStop(RuntimeError):
    pass


def get_exact_tagged_source():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Structural-BELongDead-20406-original-German-methodonly/1.0",
        "Accept": "text/csv,application/octet-stream;q=0.8",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=55) as response:
            if response.status != 200:
                raise SourceStop("SOURCE_20406_ORIGINAL_TAG_NOT_HTTP_200")
            body = response.read(BYTES + 1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_20406_TAGGED_FILE_HTTP_" + str(ex.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError) as ex:
        raise SourceStop("SOURCE_20406_TAGGED_FILE_TRANSPORT_" + type(ex).__name__) from None
    if len(body) != BYTES or hashlib.sha256(body).hexdigest() != SHA:
        raise SourceStop("SOURCE_ORIGINAL_20406_TAG2_SHA_OR_LENGTH_DRIFT")
    return body


def is_present(value):
    return bool(value.strip()) and value.strip().casefold() not in UNKNOWN


def summarize_original_method_rows(raw):
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""),
                            delimiter=",", strict=True)
        header = next(reader)
    except (UnicodeError, csv.Error, StopIteration):
        raise SourceStop("SOURCE_20406_UTF8_CSV_HEADER_STOP") from None
    if tuple(header) != HEADER:
        raise SourceStop("SOURCE_20406_TAG2_ORIGINAL_HEADER_EXACT_DRIFT")
    idx = {name: i for i, name in enumerate(HEADER)}
    original_rows = 0
    non14 = 0
    empty_key_rows = 0
    log_keys, logyear_keys = set(), set()
    plot_subplots = set()
    year_labels = set()
    years_as_2009_2026 = 0
    nonempty = collections.Counter()
    distinct = {name: set() for name in QUAL_FIELDS}
    matches = {field: collections.Counter() for field in TEXT_FIELDS}
    source_methods_nonempty = 0
    for row in reader:
        if not row or not any(v.strip() for v in row):
            continue
        original_rows += 1
        if len(row) != len(HEADER):
            non14 += 1
            continue
        # These are source METHOD fields only, NOT source organism responses.
        keys = tuple(row[idx[name]].strip() for name in KEY_FIELDS)
        year = row[idx[TIME_FIELD]].strip()
        if all(is_present(x) for x in keys):
            log_keys.add(keys)
            plot_subplots.add(keys[:2])
            if is_present(year):
                logyear_keys.add((*keys, year))
        else:
            empty_key_rows += 1
        if is_present(year):
            year_labels.add(year)
            if re.fullmatch(r"20(?:0[9]|1[0-9]|2[0-6])", year):
                years_as_2009_2026 += 1
        has_method = False
        for field in QUAL_FIELDS:
            original_value = row[idx[field]].strip()
            if not is_present(original_value):
                continue
            nonempty[field] += 1
            distinct[field].add(original_value)
            if field not in TEXT_FIELDS:
                continue
            has_method = True
            for family, compiled in METHOD_REGEX.items():
                if compiled.search(original_value):
                    matches[field][family] += 1
        if has_method:
            source_methods_nonempty += 1
    if original_rows == 0 or non14:
        raise SourceStop("SOURCE_20406_METHOD_ROWS_EMPTY_OR_SHAPE_DRIFT")
    count_matrix = {
        field: {family: matches[field][family] for family in METHOD_REGEX}
        for field in TEXT_FIELDS
    }
    pattern_total = {
        family: sum(matches[field][family] for field in TEXT_FIELDS)
        for family in METHOD_REGEX
    }
    possible_trap = bool(
        pattern_total["emergence_eclector"] or pattern_total["other_trap"]
        or pattern_total["sampling_time_or_effort"] or pattern_total["explicit_zero_capture"]
    )
    return {
        "source_original_published_tag2_SHA": SHA,
        "source_original_bytes": len(raw),
        "source_original_method_records_NOT_insect_individuals_or_traps": original_rows,
        "original_14field_row_shape_errors": non14,
        "original_source_missing_exact_PLOT_SUBPLOT_StammNR_key_rows": empty_key_rows,
        "original_method_distinct_PLOT_SUBPLOT_StammNR_tuples": len(log_keys),
        "original_method_distinct_PLOT_SUBPLOT_tuples": len(plot_subplots),
        "original_method_distinct_log_Jahr_tuples_not_sampling_occupancies": len(logyear_keys),
        "original_year_distinct_labels_count_NOT_exposed": len(year_labels),
        "original_rows_with_a_2009_2026_four_digit_Jahr_token": years_as_2009_2026,
        "original_row_has_some_Variable_Methode_Equipment_Status_text": source_methods_nonempty,
        "method_fields_original_nonempty_record_counts": dict(nonempty),
        "method_fields_original_unique_nonmissing_text_level_counts": {
            field: len(distinct[field]) for field in QUAL_FIELDS
        },
        "source_method_lexical_family_counts_by_field": count_matrix,
        "source_method_lexical_family_counts_total_by_field": pattern_total,
        "original_status_or_method_raw_text_and_original_IDs_NOT_EXPORTED": True,
        "original_year_labels_dates_source_values_NOT_EXPORTED": True,
        "original_ten_source_method_columns_only_used": True,
        "old_31123_31124_or_any_species_source_rows_NOT_REQUESTED": True,
        "original_catch_zeros_or_trap_deployments_NOT_VERIFIED": True,
        "original_20406_StammNR_vs_31123_TreeID_mapping_NOT_VERIFIED": True,
        "original_20406_PLOT_vs_31123_PlotID_mapping_NOT_VERIFIED": True,
        "original_31124_fifteen_new_TrapID_keys_NOT_RECONCILED": True,
        "status": (
            "ORIGINAL_GERMAN_METHOD_FIELD_CANDIDATES_ONLY"
            if possible_trap else
            "ORIGINAL_LOG_METADATA_NOT_CERTIFIED_CAPTURE_FRAME"
        ),
    }


def known_truth():
    f = list(HEADER)
    sample = [
        f,
        ["1","P1","S1","1","L1","A","2010","23","10",
         "Eclector","emergence Eklektor installed","Traps","2010-03","defekt"],
        ["2","P1","S1","2","L1","A","2010","23","10",
         "Eclector","removed","Trap","2010-05","kein Fang"],
        ["3","P2","S3","2","L2","A","2011","24","15",
         "Bark","Holz Messung","none","2011-05","observed"],
    ]
    s = io.StringIO()
    wr = csv.writer(s)
    wr.writerows(sample)
    result = summarize_original_method_rows(s.getvalue().encode())
    assert result["source_original_method_records_NOT_insect_individuals_or_traps"] == 3
    assert result["original_method_distinct_PLOT_SUBPLOT_StammNR_tuples"] == 2
    assert result["source_method_lexical_family_counts_total_by_field"]["emergence_eclector"] >= 1
    assert result["source_method_lexical_family_counts_total_by_field"]["explicit_zero_capture"] == 1
    assert result["status"] == "ORIGINAL_GERMAN_METHOD_FIELD_CANDIDATES_ONLY"
    for secret in ("P1", "L1", "Eclector", "kein Fang", "Bark", "2010-03"):
        assert secret not in json.dumps(result)
    print("SYNTHETIC_20406_AUTHOR_GERMAN_METHODE_EQUIPMENT_STATUS_NONEXPORT_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    known_truth()
    if args.test:
        return
    if args.out is None:
        parser.error("--out required")
    result = {
        "schema": "structural.BELongDead20406_original_German_method_status_qualification.v1",
        "precommit": PRESPEC,
        "dataset": 20406,
        "tag": 2,
        "no_new_ecological_effect_estimated": True,
        "old_Finland_Chiu_Piccini_Burner_PREDICTS_NEON_BALA_GEB_unchanged": True,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        result["source_20406_method_only"] = summarize_original_method_rows(
            get_exact_tagged_source()
        )
        result["status"] = result["source_20406_method_only"]["status"]
    except SourceStop as ex:
        result["status"] = str(ex)
        result["source_stop_not_ecological_null"] = True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "BELongDead20406_original_German_methode_status_sourceonly.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("BEXIS20406_GERMAN_AUTHOR_METHODE_EQUIPMENT_STATUS_GATE", result["status"])


if __name__ == "__main__":
    main()
