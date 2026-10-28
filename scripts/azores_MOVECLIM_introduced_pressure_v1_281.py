#!/usr/bin/env python3
"""Retrospective habitat-composition audit of already studied MOVECLIM 2013 plots.

Original 2013 Event/Occurrence and the same 20 strict Azorean historical loss
taxa are reused, *only after* the dedicated v1.281 protocol freeze. Results are
descriptive aggregate comparisons, NOT prospective evidence, causation, or
measurements of immigration, rescue, establishment or population survival.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import urllib.request

from azores_MOVECLIM_2013_refugia_v1_278 import (
    MURL, MSHA, SURL, SSHA, ISLANDS, NATIVE,
    audit_plot_frame, original_event_occurrence_records,
)
from azores2016_s1_loss_presence_crosswalk_v1_268 import (
    canonical_binomial, normalized_locality,
)
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original

EXPECTED_FOCAL_COUNTS = {"Flores": 1, "Pico": 5, "São Miguel": 1, "Terceira": 1}
EXPECTED_FOCAL_INCIDENCES = {"Flores": 7, "Pico": 26, "São Miguel": 3, "Terceira": 9}


def _norm(x):
    return " ".join(str(x or "").casefold().split())


def _avg(values):
    return sum(values) / len(values) if values else None


def _difference(a, b):
    return a - b if a is not None and b is not None else None


def _loss_taxa(losses):
    pairs = set()
    for record in losses:
        if (_norm(record.get("Archipelago")) not in {"azores", "açores"}
                or _norm(record.get("Category")) != "well-supported"
                or _norm(record.get("Extinction category")) != "extirpation (island level)"):
            continue
        taxon = canonical_binomial(record.get("Species"))
        island = normalized_locality(record.get("Island"))
        if taxon is None or island is None:
            raise ValueError("Frozen strict S1 loss taxon or island malformed")
        pairs.add((taxon, island))
    return {s for s, _ in pairs}, pairs


def audit_introduced_pressure(events, occurrences, losses, *, expected_plots=58,
                              expected_events=232):
    prior = audit_plot_frame(events, occurrences, losses,
                             expected_plots=expected_plots,
                             expected_events=expected_events)
    focal, loss_pairs = _loss_taxa(losses)
    if expected_plots == 58:
        if (len(events) != 232 or len(occurrences) != 2539
                or len(focal) != 20 or len(loss_pairs) != 24
                or prior["physical"]["distinct_permanent_plots"] != 58
                or prior["incidence"]["eligible_native_plot_taxon_positives"] != 746):
            raise ValueError("Original MOVECLIM/S1 frozen denominators mismatched")
        if any(prior["by_island"][s]["affected_native_taxa"] != n
               for s, n in EXPECTED_FOCAL_COUNTS.items()):
            raise ValueError("v1.278 focal species counts do not reconcile")
        if any(prior["by_island"][s]["S1_loss_affected_native_species_positive_plots"] != n
               for s, n in EXPECTED_FOCAL_INCIDENCES.items()):
            raise ValueError("v1.278 focal species-plot counts do not reconcile")

    id_to_site = {}
    elev_by_site = defaultdict(list)
    for e in events:
        island = normalized_locality(e.get("island"))
        site = (island, str(e.get("locationID", "")).strip())
        coreid = str(e.get("coreid", "")).strip()
        if not coreid or coreid in id_to_site:
            raise ValueError("Invalid Event core identifier")
        id_to_site[coreid] = site
        elev_by_site[site].append(float(e["minimumElevationInMeters"]))
    elevations = {s: statistics.median(x) for s, x in elev_by_site.items()}

    # A species is included only if all qualifying 2013 records agree on its
    # establishment class on that island. Same-species subplots collapse to a
    # single plot presence, with maximum 1..9 OTV retained as a sensitivity.
    status = defaultdict(set)
    plot_taxon_cover = defaultdict(list)
    for o in occurrences:
        coreid = str(o.get("coreid", "")).strip()
        if coreid not in id_to_site:
            raise ValueError("Occurrence references nonexistent Event")
        if _norm(o.get("taxonRank")) != "species":
            continue
        name = canonical_binomial(o.get("scientificName"))
        if name is None:
            continue
        try:
            cover = float(o.get("organismQuantity"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(cover) or not 1 <= cover <= 9:
            continue
        site = id_to_site[coreid]
        token = (site[0], name)
        raw = _norm(o.get("establishmentMeans"))
        cls = "native" if raw in NATIVE else "introduced" if raw == "introduced" else "unknown"
        status[token].add(cls)
        plot_taxon_cover[(site, name)].append(cover)

    native_by_taxon = defaultdict(set)
    introduced_by_taxon = defaultdict(set)
    introduced_cover_by_plot_species = {}
    for (site, taxon), covers in plot_taxon_cover.items():
        cls = status[(site[0], taxon)]
        if cls == {"native"}:
            native_by_taxon[(site[0], taxon)].add(site)
        elif cls == {"introduced"}:
            introduced_by_taxon[(site[0], taxon)].add(site)
            introduced_cover_by_plot_species[(site, taxon)] = max(covers)

    if expected_plots == 58:
        if sum(len(p) for p in native_by_taxon.values()) != 746:
            raise ValueError("Native plot-species incidence changed after status reconciliation")

    intro_richness = {s: 0 for s in elevations}
    intro_cover_proxy = {s: 0.0 for s in elevations}
    for (_, name), sites in introduced_by_taxon.items():
        for site in sites:
            intro_richness[site] += 1
            intro_cover_proxy[site] += introduced_cover_by_plot_species[(site, name)]

    native_by_site = defaultdict(set)
    focal_by_site = defaultdict(set)
    for (isl, name), sites in native_by_taxon.items():
        for site in sites:
            native_by_site[site].add(name)
            if name in focal:
                focal_by_site[site].add(name)

    by_island = {}
    for island in sorted({site[0] for site in elevations}):
        sites = sorted((site for site in elevations if site[0] == island),
                       key=lambda s: (elevations[s], s[1]))
        if len(sites) < 2:
            raise ValueError("At least two plots per island are required")
        # Equal-sized 12/12 low/high halves on Pico. Synthetic fixtures with
        # an even plot count also exercise this deterministic residualization.
        if len(sites) % 2:
            raise ValueError("Frozen median-elevation halves need an even plot count")
        midpoint = len(sites) // 2
        strata = [sites[:midpoint], sites[midpoint:]]
        exposure_mean = {site: _avg([intro_richness[p] for p in group])
                         for group in strata for site in group}
        exposure_resid = {site: intro_richness[site] - exposure_mean[site] for site in sites}
        taxon_focal = [s for (isl, s) in native_by_taxon if isl == island and s in focal]
        taxon_ref = [s for (isl, s) in native_by_taxon if isl == island and s not in focal]

        def mean_taxon_exposure(names, plot_value):
            return _avg([_avg([plot_value[p] for p in native_by_taxon[(island, name)]])
                         for name in names])
        f_intro = mean_taxon_exposure(taxon_focal, intro_richness)
        r_intro = mean_taxon_exposure(taxon_ref, intro_richness)
        f_resid = mean_taxon_exposure(taxon_focal, exposure_resid)
        r_resid = mean_taxon_exposure(taxon_ref, exposure_resid)
        f_cover = mean_taxon_exposure(taxon_focal, intro_cover_proxy)
        r_cover = mean_taxon_exposure(taxon_ref, intro_cover_proxy)
        positives = [s for s in sites if focal_by_site[s]]
        negatives = [s for s in sites if not focal_by_site[s]]
        ok = len(taxon_focal) >= 2 and len(taxon_ref) >= 5
        by_island[island] = {
            "independent_plots": len(sites),
            "focal_native_taxa": len(taxon_focal),
            "reference_native_taxa": len(taxon_ref),
            "focal_taxon_plot_positives": sum(len(native_by_taxon[(island, n)]) for n in taxon_focal),
            "reference_taxon_plot_positives": sum(len(native_by_taxon[(island, n)]) for n in taxon_ref),
            "introduced_taxon_plot_positives": sum(intro_richness[s] for s in sites),
            "introduced_taxa_total": sum(1 for (isl, _) in introduced_by_taxon if isl == island),
            "plots_with_any_introduced_taxon": sum(intro_richness[s] > 0 for s in sites),
            "introduced_richness_min": min(intro_richness[s] for s in sites),
            "introduced_richness_max": max(intro_richness[s] for s in sites),
            "focal_present_plots": len(positives),
            "focal_absent_plots": len(negatives),
            "mean_introduced_richness_at_focal_present_plots": _avg([intro_richness[s] for s in positives]),
            "mean_introduced_richness_at_focal_absent_plots": _avg([intro_richness[s] for s in negatives]),
            "plot_present_minus_absent_introduced_richness": _difference(
                _avg([intro_richness[s] for s in positives]),
                _avg([intro_richness[s] for s in negatives])),
            "mean_native_species_per_plot": _avg([len(native_by_site[s]) for s in sites]),
            "taxon_weighted_comparison_eligible": ok,
            "focal_mean_introduced_taxa_at_occupied_plots": f_intro if ok else None,
            "reference_mean_introduced_taxa_at_occupied_plots": r_intro if ok else None,
            "primary_focal_minus_reference_intro_richness": _difference(f_intro, r_intro) if ok else None,
            "focal_mean_elevation_half_centered_intro": f_resid if ok else None,
            "reference_mean_elevation_half_centered_intro": r_resid if ok else None,
            "elevation_half_adjusted_focal_minus_reference_intro": _difference(f_resid, r_resid) if ok else None,
            "focal_mean_introduced_ordinal_OTV_proxy": f_cover if ok else None,
            "reference_mean_introduced_ordinal_OTV_proxy": r_cover if ok else None,
            "source_OTV_not_percent_cover": True,
        }

    return {
        "schema": "structural.azores_moveclim_introduced_pressure_result.v1_281",
        "status": "RETROSPECTIVE_PUBLISHED_NATIVE_PLOT_ASSOCIATION",
        "original_2013_field_events": len(events),
        "original_2013_field_occurrences": len(occurrences),
        "author_defined_independent_plots": len(elevations),
        "strict_historical_S1_taxa": len(focal),
        "strict_historical_S1_loss_pairs": len(loss_pairs),
        "by_island": by_island,
        "primary_scope": "Pico only; all four islands retained as descriptive strata",
        "secondary_scope": "Within-Pico frozen median elevation 12/12 plot halves",
        "source_exposed_retrospective_not_confirmatory": True,
        "plot_10x10m_unit_not_four_independent_subplots": True,
        "no_species_names_site_ids_coordinates_or_raw_rows_exported": True,
        "not_invader_causality_or_regional_refugium": True,
        "not_demographic_rescue_or_natal_dispersal": True,
        "not_historical_at_risk_island_denominator": True,
        "other_protected_biological_endpoints_opened": 0,
        "GEB_scientific_HOLD": True,
        "confirmatory_systems_admitted": 0,
        "eBird_used": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    c = json.loads(args.protocol.read_text(encoding="utf-8"))
    if (c.get("schema") != "structural.azores_moveclim_introduced_pressure_protocol.v1_281"
            or c.get("status") != "RETROSPECTIVE_PRE_REACCESS_PROTOCOL_FROZEN"
            or c["frozen_sources"]["MOVECLIM"]["sha256"] != MSHA
            or c["frozen_sources"]["S1"]["sha256"] != SSHA
            or c["frozen_sources"]["MOVECLIM"]["url"] != MURL
            or c["frozen_sources"]["S1"]["url"] != SURL):
        raise ValueError("v1.281 protocol or fixed source identity invalid")
    result = {
        "schema": "structural.azores_moveclim_introduced_pressure_result.v1_281",
        "status": "SOURCE_STOP_NO_NEW_ECOLOGICAL_RESULT",
        "GEB_scientific_HOLD": True,
        "confirmatory_systems_admitted": 0,
        "other_protected_biological_endpoints_opened": 0,
        "eBird_used": False,
    }
    try:
        req = urllib.request.Request(MURL, headers={
            "User-Agent": "Structural-Azores-retrospective-native-plots-v1.281/1.0"})
        with urllib.request.urlopen(req, timeout=60) as source:
            raw = source.read(15_000_001)
        if len(raw) != 111299 or hashlib.sha256(raw).hexdigest() != MSHA:
            raise ValueError("2013 original source fingerprint mismatch")
        csic = download_original(SURL, 332776, 5_000_000)
        if hashlib.sha256(csic).hexdigest() != SSHA:
            raise ValueError("S1 original source fingerprint mismatch")
        events, obs = original_event_occurrence_records(raw)
        losses = parse_sheet_s1(csic)
        result = audit_introduced_pressure(events, obs, losses)
    except Exception as e:
        result["stop_type"] = type(e).__name__
        result["stop_reason"] = str(e)[:350]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    pico = result.get("by_island", {}).get("Pico", {})
    print(json.dumps({
        "status": result["status"],
        "plots": result.get("author_defined_independent_plots"),
        "Pico_focal_taxa": pico.get("focal_native_taxa"),
        "Pico_alien_taxon_positive_plots": pico.get("introduced_taxon_plot_positives"),
        "Pico_primary_focal_minus_ref": pico.get("primary_focal_minus_reference_intro_richness"),
        "Pico_elevation_adjusted_focal_minus_ref": pico.get("elevation_half_adjusted_focal_minus_reference_intro"),
        "other_protected_biological_endpoints_opened": 0,
        "stop_reason": result.get("stop_reason"),
    }, sort_keys=True))
    if result["status"] != "RETROSPECTIVE_PUBLISHED_NATIVE_PLOT_ASSOCIATION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
