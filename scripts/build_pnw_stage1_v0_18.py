#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import statistics
from io import StringIO
from pathlib import Path

RADII = (250.0, 500.0, 1000.0, 1500.0, 5000.0)
VALID_SURVEY_TYPES = {"full", "partial"}
SAFE_NUM = ("UTMe", "UTMn", "error", "elev.m", "max.size", "maxdepth", "perc.wooded")
SAFE_CAT = ("park", "region", "datum", "UTMzone", "fish")
STAGE1_COLUMNS = (
    "year", "site", "species",
    "obs1", "obs2", "obs3", "obs4", "obs5", "obs6",
    "survtype1", "survtype2", "survtype3",
    "survtype4", "survtype5", "survtype6",
)
SAFE_COLUMNS = ("year", "site") + SAFE_NUM + SAFE_CAT


def is_missing(value: str) -> bool:
    return value in {"", "NA", "NaN", "nan"}


def as_number(value: str) -> float | None:
    if is_missing(value):
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def canonical_csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    out = StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        encoded = {}
        for field in fields:
            value = row.get(field)
            if value is None:
                encoded[field] = ""
            elif isinstance(value, bool):
                encoded[field] = "1" if value else "0"
            elif isinstance(value, float):
                encoded[field] = format(value, ".12g")
            else:
                encoded[field] = value
        writer.writerow(encoded)
    return out.getvalue().encode("utf-8")


def load_authorized_source(path: Path):
    rows_2012: list[dict[str, str]] = []
    sites_2013: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header_line = handle.readline()
        header = next(csv.reader([header_line]))
        index = {name: i for i, name in enumerate(header)}
        needed = set(STAGE1_COLUMNS) | set(SAFE_COLUMNS)
        missing = sorted(needed - set(header))
        if missing:
            raise RuntimeError("missing required columns: " + ", ".join(missing))

        for raw in handle:
            prefix = raw.split(",", 3)
            if len(prefix) < 3:
                continue
            year = prefix[0]
            if year == "2013":
                # Site is the third physical field. No 2013 response columns are parsed.
                sites_2013.add(prefix[2])
                continue
            if year != "2012":
                continue

            parsed = next(csv.reader([raw]))
            rows_2012.append({
                name: parsed[index[name]].strip()
                for name in sorted(needed)
            })

    return header, rows_2012, sites_2013


def aggregate_reference(rows_2012: list[dict[str, str]]):
    grouped: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in rows_2012:
        grouped[row["site"]].append(row)

    reference = {}
    for site, rows in grouped.items():
        rec = {"site": site}
        for column in SAFE_NUM:
            values = sorted({
                value
                for row in rows
                if (value := as_number(row[column])) is not None
            })
            rec[column] = statistics.median(values) if values else None
        for column in SAFE_CAT:
            values = sorted({
                row[column]
                for row in rows
                if not is_missing(row[column])
            })
            if len(values) > 1:
                raise RuntimeError(
                    f"categorical conflict for {site} {column}: {values}"
                )
            rec[column] = values[0] if values else None
        reference[site] = rec
    return grouped, reference


def build_lagged_state(grouped):
    states = {}
    valid_visit_counts = {}
    explicit_raca_sites = set()
    survey_type_counts = collections.Counter()

    for site, rows in grouped.items():
        survey_types = []
        for visit in range(1, 7):
            values = sorted({
                row[f"survtype{visit}"]
                for row in rows
                if not is_missing(row[f"survtype{visit}"])
            })
            if len(values) > 1:
                raise RuntimeError(
                    f"survey-type conflict for {site} visit {visit}: {values}"
                )
            survey_type = values[0] if values else None
            if survey_type is not None:
                survey_type_counts[survey_type] += 1
            survey_types.append(survey_type)

        raca_rows = [row for row in rows if row["species"] == "RACA"]
        if raca_rows:
            explicit_raca_sites.add(site)

        positive = False
        valid_count = 0
        for visit, survey_type in enumerate(survey_types, start=1):
            if survey_type not in VALID_SURVEY_TYPES:
                continue
            valid_count += 1

            observed = [
                value
                for row in raca_rows
                if (value := as_number(row[f"obs{visit}"])) is not None
            ]
            # The source processing expands missing site×species×life-stage rows
            # and zero-fills observations on valid survey occasions.
            max_count = max(observed) if observed else 0.0
            if max_count > 0:
                positive = True

        if positive:
            state = 1
        elif valid_count >= 2:
            state = 0
        else:
            state = None

        states[site] = state
        valid_visit_counts[site] = valid_count

    return states, valid_visit_counts, explicit_raca_sites, survey_type_counts


def build_features(grouped, reference, states, valid_visit_counts, sites_2013):
    sites = sorted(grouped)
    common = sorted(set(sites) & set(sites_2013))
    coords = {
        site: (reference[site]["UTMe"], reference[site]["UTMn"])
        for site in sites
    }
    if any(x is None or y is None for x, y in coords.values()):
        raise RuntimeError("missing 2012 coordinates")

    positive_sources = {
        site for site, state in states.items() if state == 1
    }

    features = []
    for site in common:
        x, y = coords[site]
        all_distances = []
        occupied_distances = []
        for other in sites:
            if other == site:
                continue
            ox, oy = coords[other]
            distance = math.hypot(x - ox, y - oy)
            all_distances.append(distance)
            if other in positive_sources:
                occupied_distances.append(distance)

        generic_reach = []
        generic_pressure = []
        occupied_reach = []
        occupied_pressure = []
        for radius in RADII:
            generic_reach.append(
                1.0 if any(distance <= radius for distance in all_distances) else 0.0
            )
            generic_pressure.append(
                sum(math.exp(-distance / radius) for distance in all_distances)
            )
            occupied_reach.append(
                1.0 if any(distance <= radius for distance in occupied_distances) else 0.0
            )
            occupied_pressure.append(
                sum(math.exp(-distance / radius) for distance in occupied_distances)
            )

        features.append({
            "site": site,
            "park": reference[site]["park"],
            "region": reference[site]["region"],
            "UTMe_2012": x,
            "UTMn_2012": y,
            "lagged_state_2012": states[site],
            "lagged_state_estimable": states[site] is not None,
            "valid_visit_count_2012": valid_visit_counts[site],
            "elev.m": reference[site]["elev.m"],
            "max.size": reference[site]["max.size"],
            "maxdepth": reference[site]["maxdepth"],
            "perc.wooded": reference[site]["perc.wooded"],
            "fish": reference[site]["fish"],
            "nearest_other_2012_pond_distance_m": min(all_distances),
            "generic_pond_reachability_fraction_across_scale_worldset":
                sum(generic_reach) / len(RADII),
            "generic_pond_pressure_mean_across_scale_worldset":
                sum(generic_pressure) / len(RADII),
            "occupied_source_reachability_fraction_across_scale_worldset":
                sum(occupied_reach) / len(RADII),
            "occupied_source_pressure_mean_across_scale_worldset":
                sum(occupied_pressure) / len(RADII),
        })
    return common, positive_sources, features


def build(path: Path, output_dir: Path | None = None) -> dict:
    _, rows_2012, sites_2013 = load_authorized_source(path)
    grouped, reference = aggregate_reference(rows_2012)
    states, valid_visit_counts, explicit_raca_sites, survey_type_counts =         build_lagged_state(grouped)
    common, positive_sources, features = build_features(
        grouped, reference, states, valid_visit_counts, sites_2013
    )

    state_rows = [
        {
            "site": site,
            "state_2012": states[site],
            "valid_visits_2012": valid_visit_counts[site],
        }
        for site in sorted(grouped)
    ]
    state_fields = ["site", "state_2012", "valid_visits_2012"]
    feature_fields = list(features[0])
    state_bytes = canonical_csv_bytes(state_rows, state_fields)
    feature_bytes = canonical_csv_bytes(features, feature_fields)

    counts_all = collections.Counter(states.values())
    counts_common = collections.Counter(states[site] for site in common)

    receipt = {
        "schema": "structural.pnw_stage1_result.v0_18",
        "status": "stage1_complete_with_normalization_adjudication",
        "source_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "year_opened": 2012,
        "future_target_year_opened": False,
        "species_token": "RACA",
        "normalization": {
            "valid_survey_types": ["full", "partial"],
            "excluded_survey_types": ["dry", "NA", "blank"],
            "missing_species_row_rule":
                "zero-fill RACA on valid survey occasions when no explicit RACA row exists",
            "adjudication_note":
                "v0.17 did not enumerate valid survtype values or missing-species row expansion; rules are fixed from source metadata/source-processing semantics, not response direction",
        },
        "site_state": {
            "sites_total": len(states),
            "positive": counts_all[1],
            "negative": counts_all[0],
            "non_estimable": counts_all[None],
            "explicit_raca_sites": len(explicit_raca_sites),
            "zero_filled_sites": len(states) - len(explicit_raca_sites),
            "survey_type_site_visit_counts": dict(sorted(survey_type_counts.items())),
            "state_table_sha256": hashlib.sha256(state_bytes).hexdigest(),
        },
        "evaluation_universe": {
            "common_sites": len(common),
            "positive_2012": counts_common[1],
            "negative_2012": counts_common[0],
            "non_estimable_2012": counts_common[None],
        },
        "connectivity": {
            "source_sites_all_2012": len(states),
            "occupied_source_sites": len(positive_sources),
            "scale_worldset_m": list(RADII),
            "self_anchor_exclusion": True,
        },
        "feature_table": {
            "rows": len(features),
            "columns": feature_fields,
            "sha256": hashlib.sha256(feature_bytes).hexdigest(),
        },
        "response_access": {
            "2012_lagged_state_opened": True,
            "2013_target_opened": False,
            "2013_target_values_summarized": False,
            "model_fit_count": 0,
            "candidate_ranking_count": 0,
        },
        "evidence_class": "response_unopened_design_exposed",
        "counts_as_pristine_fresh_evidence": False,
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "pnw_stage1_state_v0_18.csv").write_bytes(state_bytes)
        (output_dir / "pnw_stage1_features_v0_18.csv").write_bytes(feature_bytes)
        (output_dir / "pnw_stage1_receipt_v0_18.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("master_csv", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.master_csv, args.output_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
