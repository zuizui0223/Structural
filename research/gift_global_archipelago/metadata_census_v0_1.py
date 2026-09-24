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
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://gift.uni-goettingen.de/api/extended/"\nVERSIONS_URL = "https://gift.uni-goettingen.de/api/index.php?query=versions"
VERSION = "3.1"
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


def fetch(query: str, *, version: str | None = VERSION):
    url = VERSIONS_URL if query == "versions" else endpoint(query, version=version)
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

    wide, target = conditional_rows(lists, taxonomy, NATIVE_SCOPE_WIDE)
    complete_floristic, _ = conditional_rows(lists, taxonomy, NATIVE_SCOPE_COMPLETE)
    complete_entity_ids = {s(r["entity_ID"]) for r in complete_floristic}
    selected = [r for r in wide if s(r["entity_ID"]) in complete_entity_ids]

    entities_all = unique_entities(selected, public_only=False)
    entities_public = unique_entities(selected, public_only=True)

    region_by_id = {s(r["entity_ID"]): r for r in regions}
    public_islands = {
        eid for eid, row in entities_public.items()
        if row["entity_class"] == PRIMARY_CHILD_CLASS
    }

    overlap, overlap_meta = fetch("overlap")
    thresholds = (0.90, 0.95, 0.99)
    memberships = {th: defaultdict(set) for th in thresholds}
    multi_parent = {th: defaultdict(set) for th in thresholds}

    for row in overlap:
        e1, e2 = s(row.get("entity1")), s(row.get("entity2"))
        r1, r2 = region_by_id.get(e1), region_by_id.get(e2)
        if r1 is None or r2 is None:
            continue
        c1, c2 = s(r1.get("entity_class")), s(r2.get("entity_class"))
        if c1 == PRIMARY_CHILD_CLASS and c2 == PRIMARY_PARENT_CLASS:
            child, parent, cover = e1, e2, f(row.get("overlap12", 0))
        elif c2 == PRIMARY_CHILD_CLASS and c1 == PRIMARY_PARENT_CLASS:
            child, parent, cover = e2, e1, f(row.get("overlap21", 0))
        else:
            continue
        if child not in public_islands:
            continue
        for th in thresholds:
            if cover >= th:
                memberships[th][parent].add(child)
                multi_parent[th][child].add(parent)

    def class_counts(entities):
        return dict(sorted(Counter(v["entity_class"] for v in entities.values()).items()))

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
        },
        "angiospermae_taxon_id": s(target.get("taxon_ID")),
        "eligible_entities_including_restricted": len(entities_all),
        "eligible_entities_public_only": len(entities_public),
        "entity_class_counts_including_restricted": class_counts(entities_all),
        "entity_class_counts_public_only": class_counts(entities_public),
        "individual_public_islands": len(public_islands),
        "archipelago_overlap_diagnostic": {},
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

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
