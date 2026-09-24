#!/usr/bin/env python3
"""Freeze the response-blind overlap exclusion between GIFT and closed A-Islands.

Only geometry and metadata are accessed:
- GIFT 3.2 list/taxonomy metadata and centroid variables;
- A-Islands v1.0 shapefile members from Zenodo.

No GIFT species composition and no A-Islands species_data.csv are requested.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

import shapefile
from shapely.geometry import Point, shape
from shapely.ops import unary_union

from metadata_census_v0_1 import (
    NATIVE_SCOPE_COMPLETE,
    NATIVE_SCOPE_WIDE,
    PRIMARY_CHILD_CLASS,
    VERSION,
    conditional_rows,
    fetch,
    s,
    unique_entities,
)

AIS_RECORD = "10775810"
AIS_FILES = {
    "A-Island_shape.shp": "5d79c86181abd3db43690e0832962ca518339b350465c5d87bb066695711d251",
    "A-Island_shape.shx": "3d5a60a0057cf4476a25ae2e69fc12146a082f82dc9c8b798300544026312d4d",
    "A-Island_shape.dbf": "75210dad46b516a3ff93168e9569910169dd5f0c946da4666970792d46b5e4ee",
    "A-Island_shape.prj": "a02a27b1d1982c8516d83398e85a3c8b1aef1713c13ef4d84d7bde17430c07c4",
}
AIS_BASE = f"https://zenodo.org/records/{AIS_RECORD}/files/"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Structural-GIFT-closed-system-exclusion/0.1"})
    with urlopen(req, timeout=180) as response:
        return response.read()


def load_gift_predictor_only_universe():
    lists, lists_meta = fetch("lists")
    taxonomy, taxonomy_meta = fetch("taxonomy")
    wide, _ = conditional_rows(lists, taxonomy, NATIVE_SCOPE_WIDE)
    complete, _ = conditional_rows(lists, taxonomy, NATIVE_SCOPE_COMPLETE)
    complete_ids = {s(row["entity_ID"]) for row in complete}
    selected = [row for row in wide if s(row["entity_ID"]) in complete_ids]
    entities = unique_entities(selected, public_only=True)
    island_ids = {
        eid for eid, row in entities.items()
        if row["entity_class"] == PRIMARY_CHILD_CLASS
    }

    values = {}
    value_meta = {}
    for var in ("longitude", "latitude", "arch_lvl_1", "arch_lvl_2", "arch_lvl_3", "GMMC", "dist"):
        rows, meta = fetch("geoentities_env_misc", extra={"envvar": var})
        values[var] = {s(row.get("entity_ID")): row.get(var) for row in rows}
        value_meta[var] = meta

    usable = set()
    paths = {}
    for eid in island_ids:
        lon, lat = values["longitude"].get(eid), values["latitude"].get(eid)
        if lon in (None, "") or lat in (None, ""):
            continue
        usable.add(eid)
        path = tuple(
            s(values[var].get(eid)).strip()
            for var in ("arch_lvl_1", "arch_lvl_2", "arch_lvl_3")
            if values[var].get(eid) not in (None, "")
        )
        if path:
            paths[eid] = path

    return usable, paths, values, {
        "lists": lists_meta,
        "taxonomy": taxonomy_meta,
        **{f"env_{key}": meta for key, meta in value_meta.items()},
    }


def load_aislands_union(directory: Path):
    observed = {}
    for name, expected in AIS_FILES.items():
        url = AIS_BASE + name + "?download=1"
        data = fetch_bytes(url)
        digest = sha256_bytes(data)
        if digest != expected:
            raise RuntimeError(f"A-Islands geometry SHA mismatch for {name}: {digest} != {expected}")
        (directory / name).write_bytes(data)
        observed[name] = {"url": url, "bytes": len(data), "sha256": digest}

    reader = shapefile.Reader(str(directory / "A-Island_shape.shp"))
    geoms = []
    for shp in reader.shapes():
        geom = shape(shp.__geo_interface__)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if not geom.is_empty:
            geoms.append(geom)
    return unary_union(geoms), len(geoms), observed


def main() -> int:
    if VERSION != "3.2":
        raise RuntimeError(f"closed-system exclusion is frozen for GIFT 3.2, got {VERSION}")

    island_ids, paths, values, gift_meta = load_gift_predictor_only_universe()

    with tempfile.TemporaryDirectory() as td:
        union, n_ais_polygons, ais_meta = load_aislands_union(Path(td))

    excluded = []
    for eid in sorted(island_ids, key=lambda x: int(x)):
        lon = float(values["longitude"][eid])
        lat = float(values["latitude"][eid])
        if union.covers(Point(lon, lat)):
            excluded.append(eid)

    excluded_set = set(excluded)
    remaining = island_ids - excluded_set

    contaminated_paths = sorted({
        paths[eid]
        for eid in excluded_set
        if eid in paths
    })
    contaminated_path_set = set(contaminated_paths)
    conservative_remaining = {
        eid for eid in island_ids
        if paths.get(eid) not in contaminated_path_set
    }

    def group_counts(ids):
        groups = defaultdict(set)
        for eid in ids:
            path = paths.get(eid)
            if path:
                groups[path].add(eid)
        counts = Counter(len(v) for v in groups.values())
        by_min = {
            str(k): sum(len(v) >= k for v in groups.values())
            for k in (4, 8, 12, 20, 30)
        }
        top = []
        for path, members in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:60]:
            gmmc = [
                int(values["GMMC"][eid])
                for eid in members
                if values["GMMC"].get(eid) not in (None, "")
            ]
            top.append({
                "archipelago_path": list(path),
                "n_islands": len(members),
                "gmmc_connected_fraction": (
                    sum(v == 1 for v in gmmc) / len(gmmc)
                    if gmmc else None
                ),
            })
        return {
            "groups": len(groups),
            "groups_by_minimum_island_count": by_min,
            "top_groups": top,
        }

    payload = {
        "schema": "structural.gift_aislands_closed_system_exclusion.v0_1",
        "status": "response_blind_geometry_exclusion_frozen",
        "gift_version": VERSION,
        "response_values_accessed": False,
        "gift_species_composition_endpoint_called": False,
        "aislands_species_data_requested": False,
        "aislands_record_id": int(AIS_RECORD),
        "aislands_geometry_polygon_count": n_ais_polygons,
        "aislands_geometry_files": ais_meta,
        "gift_predictor_only_sources": gift_meta,
        "eligible_gift_islands_with_centroids": len(island_ids),
        "excluded_gift_entity_ids": excluded,
        "excluded_gift_entity_count": len(excluded),
        "remaining_gift_entity_count": len(remaining),
        "grouping_rule": "full non-null GIFT (arch_lvl_1, arch_lvl_2, arch_lvl_3) path",
        "before_exclusion": group_counts(island_ids),
        "after_exact_entity_exclusion": group_counts(remaining),
        "contaminated_archipelago_paths": [list(path) for path in contaminated_paths],
        "contaminated_archipelago_path_count": len(contaminated_paths),
        "conservative_group_remaining_gift_entity_count": len(conservative_remaining),
        "after_conservative_archipelago_exclusion": group_counts(conservative_remaining),
        "exclusion_rule": "first identify GIFT Islands whose centroid is covered by verified A-Islands v1.0 geometry; primary panel then removes the full GIFT archipelago path of every overlapping island",
        "exact_entity_overlap_count": len(excluded_set),
        "exclusion_uses_response_direction": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["receipt_sha256"] = sha256_bytes(canonical)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
