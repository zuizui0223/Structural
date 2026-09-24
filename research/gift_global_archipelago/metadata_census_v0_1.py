#!/usr/bin/env python3
"""Response-blind GIFT 3.1 metadata census for the prospective archipelago study.

This script intentionally fetches only GIFT metadata tables: versions, regions,
lists, taxonomy and polygon-overlap metadata. It never calls the checklist/species
endpoints and therefore never opens species composition.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://gift.uni-goettingen.de/api/extended/"
VERSIONS_URL = "https://gift.uni-goettingen.de/api/index.php?query=versions"
VERSION = os.environ.get("GIFT_VERSION", "3.2")
TARGET_TAXON = "Angiospermae"
ENTITY_CLASSES = {"Island", "Island Group", "Island Part"}
PRIMARY_CHILD_CLASS = "Island"
PRIMARY_PARENT_CLASS = "Island Group"

NATIVE_SCOPE_WIDE = {
    "all", "native", "native and naturalized",
    "native and historically introduced", "endangered", "endemic",
    "other subset",
}
NATIVE_SCOPE_COMPLETE = {
    "all", "native", "native and naturalized",
    "native and historically introduced",
}


def endpoint(query: str, *, version: str | None = VERSION) -> str:
    suffix = "" if version is None else version
    return BASE + f"index{suffix}.php?" + urlencode({"query": query})


def fetch(query: str, *, version: str | None = VERSION, extra: dict | None = None):
    if query == "versions":
        url = VERSIONS_URL
    else:
        suffix = "" if version is None else version
        params = {"query": query}
        if extra:
            params.update(extra)
        url = BASE + f"index{suffix}.php?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "Structural-GIFT-metadata-census/0.1"})
    with urlopen(req, timeout=180) as response:
        raw = response.read()
    value = json.loads(raw)
    if not isinstance(value, list):
        raise RuntimeError(f"{query}: expected JSON list, got {type(value).__name__}")
    return value, {
        "url": url,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(value),
    }


def canonical_sha256(value) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def s(x) -> str:
    return "" if x is None else str(x)


def i(x) -> int:
    return int(float(x))


def f(x) -> float:
    return float(x)


def conditional_rows(lists, taxonomy, allowed_scope):
    tax_by_id = {s(row["taxon_ID"]): row for row in taxonomy}
    target = next((row for row in taxonomy if s(row.get("taxon_name")) == TARGET_TAXON), None)
    if target is None:
        raise RuntimeError(f"{TARGET_TAXON} absent from GIFT taxonomy")

    left, right = f(target["lft"]), f(target["rgt"])
    target_range = right - left

    allowed_taxa = set()
    for row in taxonomy:
        lft, rgt = f(row["lft"]), f(row["rgt"])
        if (lft >= left and rgt <= right) or (lft < left and rgt > right):
            allowed_taxa.add(s(row["taxon_ID"]))

    rows = []
    for row in lists:
        if s(row.get("taxon_ID")) not in allowed_taxa:
            continue
        if s(row.get("subset")) not in allowed_scope:
            continue
        if s(row.get("entity_class")) not in ENTITY_CLASSES:
            continue
        if s(row.get("native_indicated")) != "1":
            continue
        if s(row.get("suit_geo")) != "1":
            continue
        tax = tax_by_id.get(s(row.get("taxon_ID")))
        if tax is None:
            continue
        copy = dict(row)
        copy["_range_covered"] = f(tax["rgt"]) - f(tax["lft"])
        rows.append(copy)

    max_by_entity = defaultdict(float)
    for row in rows:
        eid = s(row["entity_ID"])
        max_by_entity[eid] = max(max_by_entity[eid], row["_range_covered"])
    complete_entities = {eid for eid, span in max_by_entity.items() if span >= target_range}
    return [row for row in rows if s(row["entity_ID"]) in complete_entities], target


def unique_entities(rows, *, public_only=False):
    out = {}
    for row in rows:
        if public_only and s(row.get("restricted")) == "1":
            continue
        eid = s(row["entity_ID"])
        out[eid] = {
            "entity_ID": eid,
            "geo_entity": s(row.get("geo_entity")),
            "entity_class": s(row.get("entity_class")),
            "entity_type": s(row.get("entity_type") or row.get("entity_unit")),
        }
    return out


def main() -> int:
    versions, versions_meta = fetch("versions", version=None)
    available = {s(r.get("version")) for r in versions}
    if VERSION not in available:
        raise RuntimeError(f"pinned GIFT {VERSION} not listed; available={sorted(available)}")

    regions, regions_meta = fetch("regions")
    lists, lists_meta = fetch("lists")
    taxonomy, taxonomy_meta = fetch("taxonomy")
    traits_meta_rows, traits_meta_meta = fetch("traits_meta")
    trait_keywords = ("dispers", "seed mass", "seed_mass", "fruit")
    selected_trait_metadata = [
        row for row in traits_meta_rows
        if any(
            key in (
                s(row.get("Category")) + " "
                + s(row.get("Trait1")) + " "
                + s(row.get("Trait2")) + " "
                + s(row.get("comment"))
            ).lower()
            for key in trait_keywords
        )
    ]

    wide, target = conditional_rows(lists, taxonomy, NATIVE_SCOPE_WIDE)
    complete_floristic, _ = conditional_rows(lists, taxonomy, NATIVE_SCOPE_COMPLETE)
    complete_entity_ids = {s(r["entity_ID"]) for r in complete_floristic}
    selected = [r for r in wide if s(r["entity_ID"]) in complete_entity_ids]

    entities_all = unique_entities(selected, public_only=False)
    entities_public = unique_entities(selected, public_only=True)

    response_surface_rows = sorted(
        {
            (
                s(row.get("list_ID")),
                s(row.get("entity_ID")),
                s(row.get("ref_ID")),
                s(row.get("taxon_ID")),
                s(row.get("subset")),
            )
            for row in selected
            if s(row.get("restricted")) != "1"
            and s(row.get("entity_class")) == PRIMARY_CHILD_CLASS
        }
    )
    response_surface_manifest = {
        "role": "unopened_native_angiosperm_checklist_response_surface",
        "gift_version": VERSION,
        "record_fields": ["list_ID", "entity_ID", "ref_ID", "taxon_ID", "subset"],
        "record_count": len(response_surface_rows),
        "records_sha256": canonical_sha256(response_surface_rows),
        "response_values_accessed": False,
    }

    region_by_id = {s(r["entity_ID"]): r for r in regions}
    public_islands = {
        eid for eid, row in entities_public.items()
        if row["entity_class"] == PRIMARY_CHILD_CLASS
    }

    overlap, overlap_meta = fetch("overlap")
    env_misc, env_misc_meta = fetch("env_misc")
    selected_env_values = {}
    env_maps = {}
    for var in ("area", "dist", "SLMP", "GMMC", "arch_lvl_1", "arch_lvl_2", "arch_lvl_3"):
        rows, meta = fetch("geoentities_env_misc", extra={"envvar": var})
        env_maps[var] = {s(row.get("entity_ID")): row.get(var) for row in rows}
        selected_env_values[var] = {
            "meta": meta,
            "sample": rows[:8],
        }
    env_keywords = ("arch", "geolog", "origin", "gmmc", "glacial", "dist", "slmp", "area", "age", "latitude", "longitude")
    selected_env_misc = [
        row for row in env_misc
        if any(
            key in (s(row.get("variable")) + " " + s(row.get("description")) + " " + s(row.get("dataset"))).lower()
            for key in env_keywords
        )
    ]
    thresholds = (0.90, 0.95, 0.99)
    memberships = {th: defaultdict(set) for th in thresholds}
    multi_parent = {th: defaultdict(set) for th in thresholds}
    parent_candidates = {th: defaultdict(dict) for th in thresholds}

    for row in overlap:
        e1, e2 = s(row.get("entity1")), s(row.get("entity2"))
        r1, r2 = region_by_id.get(e1), region_by_id.get(e2)
        if r1 is None or r2 is None:
            continue
        c1, c2 = s(r1.get("entity_class")), s(r2.get("entity_class"))
        if c1 == PRIMARY_CHILD_CLASS and c2 == PRIMARY_PARENT_CLASS:
            child, parent, cover = e1, e2, f(row.get("overlap12", 0))
            parent_area = f(row.get("area2", 0))
        elif c2 == PRIMARY_CHILD_CLASS and c1 == PRIMARY_PARENT_CLASS:
            child, parent, cover = e2, e1, f(row.get("overlap21", 0))
            parent_area = f(row.get("area1", 0))
        else:
            continue
        if child not in public_islands:
            continue
        for th in thresholds:
            if cover >= th:
                memberships[th][parent].add(child)
                multi_parent[th][child].add(parent)
                parent_candidates[th][child][parent] = parent_area

    def class_counts(entities):
        return dict(sorted(Counter(v["entity_class"] for v in entities.values()).items()))

    # Standardized response-blind archipelago hierarchy from GIFT itself.
    # The tuple path is used instead of the terminal name alone to avoid
    # collisions between identically named subgroups in different parents.
    hierarchy_groups = defaultdict(set)
    hierarchy_path_by_island = {}
    for eid in sorted(public_islands):
        levels = tuple(
            s(env_maps[var].get(eid)).strip()
            for var in ("arch_lvl_1", "arch_lvl_2", "arch_lvl_3")
            if env_maps[var].get(eid) not in (None, "")
        )
        if not levels:
            continue
        hierarchy_groups[levels].add(eid)
        hierarchy_path_by_island[eid] = levels

    hierarchy_counts = sorted(
        (len(children), path) for path, children in hierarchy_groups.items()
    )
    hierarchy_by_min = {
        str(k): sum(n >= k for n, _ in hierarchy_counts)
        for k in (4, 8, 12, 20, 30)
    }
    hierarchy_top = []
    for n, path in sorted(hierarchy_counts, reverse=True)[:60]:
        children = hierarchy_groups[path]
        gmmc = [
            env_maps["GMMC"].get(eid)
            for eid in children
            if env_maps["GMMC"].get(eid) is not None
        ]
        gmmc_set = sorted(set(gmmc))
        if gmmc_set == [1]:
            historical_connection_class = "all_LGM_connected"
        elif gmmc_set == [0]:
            historical_connection_class = "all_LGM_disconnected"
        elif gmmc_set:
            historical_connection_class = "mixed_LGM_connection"
        else:
            historical_connection_class = "unknown"
        hierarchy_top.append({
            "archipelago_path": list(path),
            "n_eligible_individual_islands": n,
            "historical_connection_class": historical_connection_class,
            "gmmc_nonmissing": len(gmmc),
        })

    distances = sorted(
        float(env_maps["dist"][eid])
        for eid in public_islands
        if env_maps["dist"].get(eid) is not None
    )
    def empirical_quantile(values, p):
        if not values:
            return None
        pos = (len(values) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(values) - 1)
        frac = pos - lo
        return values[lo] * (1 - frac) + values[hi] * frac

    summary = {
        "schema": "structural.gift_archipelago_metadata_census.v0_1",
        "response_values_accessed": False,
        "species_composition_endpoint_called": False,
        "gift_version": VERSION,
        "target_taxon": TARGET_TAXON,
        "filters": {
            "geo_type": "Island",
            "entity_classes": sorted(ENTITY_CLASSES),
            "floristic_group": "native",
            "complete_floristic": True,
            "complete_taxon": True,
            "native_indicated": True,
            "suit_geo": True,
            "public_only_diagnostic": "restricted != 1",
        },
        "source_tables": {
            "versions": versions_meta,
            "regions": regions_meta,
            "lists": lists_meta,
            "taxonomy": taxonomy_meta,
            "overlap": overlap_meta,
            "env_misc": env_misc_meta,
            "traits_meta": traits_meta_meta,
        },
        "selected_environment_metadata": selected_env_misc,
        "selected_environment_value_audit": selected_env_values,
        "selected_trait_metadata": selected_trait_metadata,
        "response_surface_manifest": response_surface_manifest,
        "angiospermae_taxon_id": s(target.get("taxon_ID")),
        "eligible_entities_including_restricted": len(entities_all),
        "eligible_entities_public_only": len(entities_public),
        "entity_class_counts_including_restricted": class_counts(entities_all),
        "entity_class_counts_public_only": class_counts(entities_public),
        "individual_public_islands": len(public_islands),
        "gift_archipelago_hierarchy_diagnostic": {
            "rule": "group by full non-null (arch_lvl_1, arch_lvl_2, arch_lvl_3) path; no response data used",
            "assigned_individual_islands": len(hierarchy_path_by_island),
            "unassigned_individual_islands": len(public_islands - set(hierarchy_path_by_island)),
            "groups_with_at_least_one_island": len(hierarchy_groups),
            "groups_by_minimum_island_count": hierarchy_by_min,
            "top_groups": hierarchy_top,
        },
        "isolation_metadata_diagnostic": {
            "metric": "GIFT dist = coast-to-coast distance to nearest mainland, excluding Antarctica",
            "n_nonmissing": len(distances),
            "q70_km": empirical_quantile(distances, 0.70),
            "q75_km": empirical_quantile(distances, 0.75),
            "q80_km": empirical_quantile(distances, 0.80),
            "threshold_role": "diagnostic only until closed-system exclusions and final predictor-only universe are frozen",
        },
        "archipelago_overlap_diagnostic": {},
        "canonical_smallest_parent_diagnostic": {},
        "gift_archipelago_level_diagnostic": {},
    }

    # Native GIFT archipelago hierarchy diagnostic. This is preferred over
    # polygon containment because it is an explicit response-independent field
    # authored in GIFT itself.
    for level in ("arch_lvl_1", "arch_lvl_2", "arch_lvl_3"):
        groups = defaultdict(list)
        for island_id in sorted(public_islands):
            group = env_maps[level].get(island_id)
            if group is None or not s(group).strip():
                continue
            groups[s(group).strip()].append(island_id)

        rows = []
        for group, island_ids in groups.items():
            dists = [
                f(env_maps["dist"].get(i))
                for i in island_ids
                if env_maps["dist"].get(i) not in (None, "")
            ]
            gmmc = [
                i(env_maps["GMMC"].get(island_id))
                for island_id in island_ids
                if env_maps["GMMC"].get(island_id) not in (None, "")
            ]
            rows.append({
                "archipelago": group,
                "n_eligible_islands": len(island_ids),
                "dist_complete": len(dists),
                "dist_min_km": min(dists) if dists else None,
                "dist_max_km": max(dists) if dists else None,
                "gmmc_complete": len(gmmc),
                "gmmc_connected_n": sum(v == 1 for v in gmmc),
                "gmmc_disconnected_n": sum(v == 0 for v in gmmc),
                "gmmc_connected_fraction": (
                    sum(v == 1 for v in gmmc) / len(gmmc)
                    if gmmc else None
                ),
            })
        rows.sort(key=lambda row: (-row["n_eligible_islands"], row["archipelago"]))
        summary["gift_archipelago_level_diagnostic"][level] = {
            "groups_with_at_least_one_eligible_island": len(rows),
            "groups_by_minimum_island_count": {
                str(k): sum(row["n_eligible_islands"] >= k for row in rows)
                for k in (4, 8, 12, 20, 30)
            },
            "eligible_islands_assigned": sum(row["n_eligible_islands"] for row in rows),
            "groups_ge_12_with_complete_dist": sum(
                row["n_eligible_islands"] >= 12
                and row["dist_complete"] == row["n_eligible_islands"]
                for row in rows
            ),
            "groups_ge_12_with_complete_gmmc": sum(
                row["n_eligible_islands"] >= 12
                and row["gmmc_complete"] == row["n_eligible_islands"]
                for row in rows
            ),
            "groups_ge_12_with_both_gmmc_states": sum(
                row["n_eligible_islands"] >= 12
                and row["gmmc_connected_n"] > 0
                and row["gmmc_disconnected_n"] > 0
                for row in rows
            ),
            "top_groups": rows[:50],
        }

    for th in thresholds:
        parents = memberships[th]
        child_to_parents = multi_parent[th]
        assigned = set().union(*parents.values()) if parents else set()
        counts = sorted((len(children), pid) for pid, children in parents.items())
        by_min = {str(k): sum(n >= k for n, _ in counts) for k in (4, 8, 12, 20, 30)}
        top = []
        for n, pid in sorted(counts, reverse=True)[:40]:
            rr = region_by_id.get(pid, {})
            top.append({
                "entity_ID": pid,
                "geo_entity": s(rr.get("geo_entity")),
                "entity_type": s(rr.get("entity_type")),
                "country": s(rr.get("country")),
                "n_eligible_individual_islands": n,
            })
        summary["archipelago_overlap_diagnostic"][str(th)] = {
            "groups_with_at_least_one_eligible_island": len(parents),
            "groups_by_minimum_island_count": by_min,
            "assigned_individual_islands": len(assigned),
            "unassigned_individual_islands": len(public_islands - assigned),
            "islands_with_multiple_parent_groups": sum(len(v) > 1 for v in child_to_parents.values()),
            "top_groups": top,
        }

        # Response-blind canonicalization diagnostic:
        # every individual island is assigned to exactly one containing Island Group,
        # choosing the smallest-area parent at the same overlap threshold. Ties use
        # entity_ID, making the rule deterministic without inspecting species data.
        canonical = defaultdict(set)
        for child, candidates in parent_candidates[th].items():
            if not candidates:
                continue
            parent = min(candidates, key=lambda pid: (candidates[pid], pid))
            canonical[parent].add(child)
        canonical_counts = sorted((len(children), pid) for pid, children in canonical.items())
        canonical_by_min = {
            str(k): sum(n >= k for n, _ in canonical_counts)
            for k in (4, 8, 12, 20, 30)
        }
        canonical_top = []
        for n, pid in sorted(canonical_counts, reverse=True)[:40]:
            rr = region_by_id.get(pid, {})
            canonical_top.append({
                "entity_ID": pid,
                "geo_entity": s(rr.get("geo_entity")),
                "entity_type": s(rr.get("entity_type")),
                "country": s(rr.get("country")),
                "n_assigned_individual_islands": n,
            })
        canonical_assigned = set().union(*canonical.values()) if canonical else set()
        summary["canonical_smallest_parent_diagnostic"][str(th)] = {
            "rule": "among containing Island Group polygons, assign each Island to the minimum parent area; tie-break by entity_ID",
            "groups_with_at_least_one_assigned_island": len(canonical),
            "groups_by_minimum_island_count": canonical_by_min,
            "assigned_individual_islands": len(canonical_assigned),
            "unassigned_individual_islands": len(public_islands - canonical_assigned),
            "islands_with_multiple_assignments_after_resolution": 0,
            "top_groups": canonical_top,
        }

    summary["source_fingerprint"] = canonical_sha256({
        "gift_version": VERSION,
        "target_taxon": TARGET_TAXON,
        "filters": summary["filters"],
        "source_table_sha256": {
            key: value["sha256"] for key, value in summary["source_tables"].items()
        },
        "environment_value_sha256": {
            key: value["meta"]["sha256"]
            for key, value in summary["selected_environment_value_audit"].items()
        },
        "response_surface_manifest_sha256": response_surface_manifest["records_sha256"],
    })

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
