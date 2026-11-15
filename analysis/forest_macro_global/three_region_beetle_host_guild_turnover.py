#!/usr/bin/env python3
"""Frozen 2026-11-15 exploratory three-country host-guild conditional-null test.

Data: Zenodo 5950610; country-level beetle species x sampling-column counts
and source Host_tree affiliations. No geographical/field-forest independence
or structure effect inferred. No raw IDs, species or sample columns exported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

MANIFEST = {
    "Finland": {
        "matrix": ("Finland_sites.species.csv", "c373ec9f597311a636b4f83d39fcfc9d"),
        "traits": ("Finland_traits.csv", "6e0303545b79a9959b83d3c86437336a"),
    },
    "Germany": {
        "matrix": ("Germany_sites.species.csv", "0ab85a1e30e8c9cc52d08255c6cd9c16"),
        "traits": ("Germany_traits.csv", "51b711c03bc3926c8030537fc8d581f3"),
    },
    "Norway": {
        "matrix": ("Norway_sites.species.csv", "2320412a2d87e68bb79d1ccf86829bf0"),
        "traits": ("Norway_traits.csv", "342f68d55222b844c91cb4b415edd791"),
    },
}
GUILDS = {"broadl": 0, "conifer": 1, "both": 2}
N_PERM = 2999
SEED = 20261115
MIN_SITES = 20
MIN_SOURCE_SPECIES = 30
MIN_PER_SITE_HOST_KNOWN = 5
MIN_TRAIT_COVERAGE = .60


class ScientificStop(RuntimeError):
    pass


def validate_original_source(folder: Path):
    """Header and identity only; count rows, do not read abundance or trait outcomes."""
    receipts = {}
    for country, files in MANIFEST.items():
        r = {}
        for kind, (filename, expected_md5) in files.items():
            file_path = folder / filename
            if not file_path.is_file():
                raise ScientificStop("SCIENTIFIC_STOP_REQUIRED_SOURCE_FILE_UNAVAILABLE")
            digest = hashlib.md5(file_path.read_bytes()).hexdigest()
            if digest != expected_md5:
                raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_ZENODO_FILE_DIGEST_DRIFT")
            with file_path.open(newline="", encoding="utf-8-sig") as fh:
                rd = csv.reader(fh)
                head = next(rd, [])
                if len(head) < 2:
                    raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_SOURCE_EMPTY_HEADER")
                if kind == "traits" and "Host_tree" not in head:
                    raise ScientificStop("SCIENTIFIC_STOP_HOST_TREE_TRAIT_SOURCE_HEADER_MISSING")
                if kind == "matrix" and (len(head) < MIN_SITES + 1 or len(head[1:]) != len(set(head[1:]))):
                    raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_SOURCE_SAMPLING_COLUMN_IDENTITY")
                row_n = 0
                keys = set()
                for row in rd:
                    if len(row) != len(head) or not row[0] or row[0] in keys:
                        raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_SOURCE_SPECIES_ROWS_INCONSISTENT")
                    keys.add(row[0])
                    row_n += 1
            if row_n < MIN_SOURCE_SPECIES:
                raise ScientificStop("SCIENTIFIC_STOP_SOURCE_TOO_FEW_BEETLE_SPECIES")
            r[kind + "_original_rows"] = row_n
            r[kind + "_fields"] = len(head)
            if kind == "matrix":
                r["sampling_columns_not_independent_forests"] = len(head) - 1
                r["sampling_columns_with_four_digit_year_prefix"] = sum(
                    bool(re.match(r"^(19|20)\d{2}[_-]", v)) for v in head[1:]
                )
            r[kind + "_md5_verified"] = True
        receipts[country] = r
    return {
        "schema": "structural.zenodo5950610_threecountry_sourceonly.v1",
        "zenodo_original_record": "10.5281/zenodo.5950610",
        "source_original_manifest_all_md5_verified": True,
        "no_biological_abundance_or_Host_tree_values_read_in_source_gate": True,
        "source_labels_not_inferred_independent_physical_forests": True,
        "country_source_only": receipts,
    }


def read_country(folder: Path, country: str):
    matrix_name = MANIFEST[country]["matrix"][0]
    trait_name = MANIFEST[country]["traits"][0]
    with (folder / matrix_name).open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        head = next(reader)
        n_site = len(head) - 1
        species = []
        values = []
        for row in reader:
            if len(row) != n_site + 1:
                raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_MATRIX_FIELD_COUNT")
            species.append(row[0])
            clean = []
            for v in row[1:]:
                try:
                    z = float(v)
                except ValueError:
                    raise ScientificStop("SCIENTIFIC_STOP_RAW_ABUNDANCE_NOT_NUMERIC") from None
                if not math.isfinite(z) or z < 0 or z != int(z):
                    raise ScientificStop("SCIENTIFIC_STOP_RAW_ABUNDANCE_NEGATIVE_OR_INVALID")
                clean.append(z > 0)
            values.append(clean)
    detected = np.asarray(values, dtype=np.uint8).T  # sampling columns x species
    if detected.shape != (n_site, len(species)):
        raise ScientificStop("SCIENTIFIC_STOP_SOURCE_MATRIX_ORIENTATION")
    with (folder / trait_name).open(newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        guild = {}
        for row in rd:
            key = row[rd.fieldnames[0]]
            if key in guild:
                raise ScientificStop("SCIENTIFIC_STOP_DUPLICATE_COUNTRY_TRAIT_SPECIES")
            x = (row.get("Host_tree") or "").strip().lower()
            if x not in GUILDS and x not in {"na", "", "nan"}:
                raise ScientificStop("SCIENTIFIC_STOP_UNEXPECTED_ORIGINAL_HOST_TREE_GUILD")
            guild[key] = GUILDS.get(x, -1)
    codes = np.asarray([guild.get(s, -1) for s in species], dtype=int)
    coverage = detected[:, codes >= 0].sum(axis=1) / np.maximum(detected.sum(axis=1), 1)
    known_counts = detected[:, codes >= 0].sum(axis=1)
    elig = (known_counts >= MIN_PER_SITE_HOST_KNOWN) & (coverage >= MIN_TRAIT_COVERAGE)
    eligible_sites = detected[elig, :][:, codes >= 0]
    codes = codes[codes >= 0]
    active = np.asarray(eligible_sites.sum(axis=0) > 0)
    eligible_sites = eligible_sites[:, active]
    codes = codes[active]
    diag = {
        "original_sampling_columns": int(n_site),
        "original_species_rows": int(len(species)),
        "original_species_with_host_tree_category": int((np.asarray([
            guild.get(s, -1) for s in species]) >= 0).sum()),
        "eligible_source_sampling_columns": int(elig.sum()),
        "excluded_source_sampling_columns": int((~elig).sum()),
        "eligible_active_known_host_tree_beetle_species": int(len(codes)),
        "eligible_source_site_coverage_min": round(float(coverage[elig].min()), 4) if elig.any() else None,
        "raw_site_unit_is_not_independent_forest": True,
    }
    if int(elig.sum()) < MIN_SITES or int(len(codes)) < MIN_SOURCE_SPECIES:
        return None, None, diag
    return eligible_sites, codes, diag


def source_species_simpson(matrix: np.ndarray) -> float:
    rich = matrix.sum(axis=1).astype(float)
    co = (matrix.astype(np.int32) @ matrix.astype(np.int32).T).astype(float)
    i, j = np.triu_indices(matrix.shape[0], 1)
    b = rich[i] - co[i, j]
    c = rich[j] - co[i, j]
    minimum = np.minimum(b, c)
    denom = co[i, j] + minimum
    ok = denom > 0
    if not ok.any():
        return float("nan")
    return float(np.mean(minimum[ok] / denom[ok]))


def sqrt_js_distance(p: np.ndarray, q: np.ndarray):
    m = .5 * (p + q)
    with np.errstate(divide="ignore", invalid="ignore"):
        a = np.where(p > 0, p * np.log2(p / m), 0)
        b = np.where(q > 0, q * np.log2(q / m), 0)
    return np.sqrt(np.maximum(0, .5 * np.sum(a + b, axis=1)))


def mean_guild_sqrt_js(matrix: np.ndarray, codes: np.ndarray):
    """Exact all-site-pair mean: group identical 3-category guild proportions."""
    counts = matrix.astype(np.int32) @ np.eye(3, dtype=np.int32)[codes]
    if np.any(counts.sum(axis=1) == 0):
        raise ScientificStop("SCIENTIFIC_STOP_EMPTY_HOST_GUILD_AFTER_SITE_FILTER")
    props = counts / counts.sum(axis=1, keepdims=True)
    unique, multiplicities = np.unique(props, axis=0, return_counts=True)
    if len(unique) <= 1:
        return 0.
    a, b = np.triu_indices(len(unique), 1)
    weights = multiplicities[a].astype(float) * multiplicities[b]
    d = sqrt_js_distance(unique[a], unique[b])
    n = matrix.shape[0]
    return float(np.sum(weights * d) / (n * (n - 1) / 2))


def known_truth():
    p = np.array([[1., 0., 0.]])
    q = np.array([[0., 1., 0.]])
    assert abs(float(sqrt_js_distance(p, p)[0])) < 1e-12
    assert abs(float(sqrt_js_distance(p, q)[0]) - 1.) < 1e-12
    m = np.array([[1, 1, 0], [1, 0, 1]], dtype=np.uint8)
    assert abs(source_species_simpson(m) - 1/2) < 1e-12
    assert abs(mean_guild_sqrt_js(m, np.array([0, 0, 1])) -
               float(sqrt_js_distance(np.array([[1.,0.,0.]]),
                                     np.array([[.5, .5, 0.]]))[0])) < 1e-12
    m_before = m.copy()
    rng = np.random.default_rng(20261115)
    _ = mean_guild_sqrt_js(m, rng.permutation(np.array([0, 1, 2])))
    assert np.array_equal(m, m_before)
    print("SYNTHETIC_KNOWN_TRUTH_JSD_SIMPSON_SITE_PRESERVATION_PASS")


def score(folder: Path, out: Path):
    source = validate_original_source(folder)
    rng = np.random.default_rng(SEED)
    per_region = {}
    data = {}
    for country in MANIFEST:
        matrix, codes, diag = read_country(folder, country)
        per_region[country] = diag
        if matrix is not None:
            data[country] = (matrix, codes)
    result = {
        "schema": "structural.zenodo5950610_threecountry_beetle_hostguild_conditionalnull.v1",
        "source_record": "10.5281/zenodo.5950610",
        "source_only_receipt": source,
        "source_gate": per_region,
        "original_taxonomic_and_trait_rows_not_redistributed": True,
        "original_sampling_column_ids_and_raw_abundances_not_exported": True,
        "analysis_is_retrospective_not_prospectively_confirmatory": True,
        "no_forest_canopy_microclimate_or_individual_movement_effect_scored": True,
        "no_country_sample_columns_called_independent_forests": True,
        "prior_PREDICTS_NEON_BALA_GEB_original_endpoints_not_read_or_changed": True,
        "eBird_used": False,
    }
    if len(data) != len(MANIFEST):
        result["status"] = "SCIENTIFIC_STOP_THREE_COUNTRY_PREDECLARED_HOSTGUILD_SOURCE_COVERAGE"
    else:
        obs, nulls, betas = [], [], []
        for country, (matrix, codes) in data.items():
            beta = source_species_simpson(matrix)
            if not math.isfinite(beta):
                raise ScientificStop("SCIENTIFIC_STOP_ORIGINAL_TAXON_SIMSPON_UNDEFINED")
            fobs = mean_guild_sqrt_js(matrix, codes)
            reference = np.array(
                [mean_guild_sqrt_js(matrix, rng.permutation(codes))
                 for _ in range(N_PERM)]
            )
            obs.append(fobs)
            nulls.append(reference)
            betas.append(beta)
            per_region[country].update({
                "original_pairs_nonindependent": int(matrix.shape[0]*(matrix.shape[0]-1)//2),
                "same_host_trait_known_species_mean_simpson_taxon_beta": round(beta, 6),
                "observed_mean_hostguild_sqrt_JSD": round(fobs, 6),
                "null_mean_hostguild_sqrt_JSD": round(float(reference.mean()), 6),
                "observed_minus_null_mean_hostguild_sqrt_JSD": round(float(fobs-reference.mean()), 6),
            })
        Tobs = float(np.mean(obs))
        Tnull = np.mean(np.vstack(nulls), axis=0)
        delta = Tobs - float(Tnull.mean())
        p = (1 + int(np.count_nonzero(
            np.abs(Tnull-Tnull.mean()) >= abs(delta)-1e-12))) / (N_PERM+1)
        result["status"] = "EXPLORATORY_COMPLETED_THREE_COUNTRY_HOSTGUILD_CONDITIONAL_NULL"
        result["primary_inference"] = {
            "observed_equal_country_mean_hostguild_sqrt_JSD": round(Tobs, 6),
            "null_equal_country_mean_hostguild_sqrt_JSD": round(float(Tnull.mean()), 6),
            "observed_minus_null_mean_d": round(delta, 6),
            "country_wise_simultaneous_host_tree_species_label_permutations": N_PERM,
            "permutation_reference_95_interval_NOT_sampling_CI": [
                round(float(v), 6) for v in np.quantile(Tnull - Tnull.mean(), [.025, .975])
            ],
            "two_sided_conditional_permutation_p": round(float(p), 6),
            "country_count": len(data),
            "country_positives": int(sum(o > ref.mean() for o, ref in zip(obs, nulls))),
            "original_species_richness_not_functionally_equated_to_JSD": True,
            "effect_not_causal_local_tree_host_or_canopy_structure": True,
        }
    out.mkdir(parents=True, exist_ok=True)
    target = out / "three_country_beetle_hostguild_original_aggregate.json"
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["test", "source", "score"], required=True)
    ap.add_argument("--folder", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    known_truth()
    if a.mode == "test":
        return
    if a.folder is None or a.out is None:
        ap.error("source/score modes require --folder and --out")
    try:
        if a.mode == "source":
            x = validate_original_source(a.folder)
            a.out.mkdir(parents=True, exist_ok=True)
            (a.out / "three_country_source_only_receipt.json").write_text(
                json.dumps(x, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(x, indent=2))
        else:
            score(a.folder, a.out)
    except ScientificStop as e:
        a.out.mkdir(parents=True, exist_ok=True)
        rec = {
            "schema": "structural.zenodo5950610_scientific_source_stop.v1",
            "status": str(e),
            "no_source_data_or_respondent_rows_reexported": True,
            "no_biological_effect_claim": True,
        }
        (a.out / "source_STOP.json").write_text(json.dumps(rec, indent=2) + "\n")
        print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
