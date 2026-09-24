#!/usr/bin/env python3
"""Freeze the predictor-complete GIFT archipelago universe before response access.

This freezes:
- the exact island and checklist universe;
- conservative A-Islands-contaminated archipelago removal;
- current-environment reference completeness;
- within-archipelago q75/q70/q80 isolation ranks;
- deterministic 4-block spatial MST holdout labels;
- a metadata-stratified burned-pilot/confirmatory archipelago split.

No GIFT species-composition endpoint is called.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
import math
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
    f,
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
CLIMATE_LAYERS = [
    "wc2.0_bio_30s_01",
    "wc2.0_bio_30s_05",
    "wc2.0_bio_30s_06",
    "wc2.0_bio_30s_12",
    "wc2.0_bio_30s_15",
]
MISC_VARS = [
    "area", "dist", "SLMP", "GMMC",
    "longitude", "latitude",
    "arch_lvl_1", "arch_lvl_2", "arch_lvl_3",
]
MIN_ARCHIPELAGO_ISLANDS = 20
N_SPATIAL_BLOCKS = 4


def sha(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Structural-GIFT-analysis-universe/0.1"})
    with urlopen(req, timeout=180) as response:
        return response.read()


def aislands_union() -> tuple[object, dict]:
    meta = {}
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, expected in AIS_FILES.items():
            data = fetch_bytes(AIS_BASE + name + "?download=1")
            digest = hashlib.sha256(data).hexdigest()
            if digest != expected:
                raise RuntimeError(f"A-Islands geometry SHA mismatch for {name}")
            (root / name).write_bytes(data)
            meta[name] = {"bytes": len(data), "sha256": digest}
        reader = shapefile.Reader(str(root / "A-Island_shape.shp"))
        geoms = []
        for shp in reader.shapes():
            geom = shape(shp.__geo_interface__)
            if not geom.is_valid:
                geom = geom.buffer(0)
            if not geom.is_empty:
                geoms.append(geom)
        return unary_union(geoms), {
            "record_id": int(AIS_RECORD),
            "polygon_count": len(geoms),
            "files": meta,
        }


def haversine_km(lon1, lat1, lon2, lat2):
    r = 6371.0088
    a1, a2 = math.radians(lat1), math.radians(lat2)
    da = a2 - a1
    dl = math.radians(lon2 - lon1)
    x = math.sin(da / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(x)))


class DSU:
    def __init__(self, nodes):
        self.p = {n: n for n in nodes}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if int(a) > int(b):
            a, b = b, a
        self.p[b] = a
        return True


def mst_blocks(ids, lon, lat, k=N_SPATIAL_BLOCKS):
    ids = sorted(ids, key=int)
    if len(ids) < k:
        raise RuntimeError("archipelago smaller than spatial block count")
    edges = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            d = haversine_km(float(lon[a]), float(lat[a]), float(lon[b]), float(lat[b]))
            edges.append((d, int(a), int(b), a, b))
    edges.sort()
    dsu = DSU(ids)
    mst = []
    for edge in edges:
        if dsu.union(edge[3], edge[4]):
            mst.append(edge)
            if len(mst) == len(ids) - 1:
                break
    if len(mst) != len(ids) - 1:
        raise RuntimeError("MST construction failed")
    cut = set((e[3], e[4]) for e in sorted(mst, reverse=True)[: k - 1])
    dsu2 = DSU(ids)
    for e in mst:
        if (e[3], e[4]) not in cut:
            dsu2.union(e[3], e[4])
    groups = defaultdict(list)
    for eid in ids:
        groups[dsu2.find(eid)].append(eid)
    comps = sorted(
        (sorted(v, key=int) for v in groups.values()),
        key=lambda members: int(members[0]),
    )
    if len(comps) != k:
        raise RuntimeError(f"expected {k} MST blocks, got {len(comps)}")
    out = {}
    for idx, members in enumerate(comps, start=1):
        for eid in members:
            out[eid] = f"B{idx}"
    return out, [len(m) for m in comps]


def rank_tail(ids, dist, fraction):
    ids = sorted(ids, key=lambda eid: (-float(dist[eid]), int(eid)))
    n = max(1, math.ceil(len(ids) * fraction))
    return sorted(ids[:n], key=int)


def history_bin(frac):
    if frac <= 0.25:
        return "low_GMMC"
    if frac >= 0.75:
        return "high_GMMC"
    return "mid_GMMC"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exclusion-json", type=Path, required=True)
    args = parser.parse_args()

    if VERSION != "3.2":
        raise RuntimeError(f"analysis universe is frozen for GIFT 3.2, got {VERSION}")

    lists, lists_meta = fetch("lists")
    taxonomy, taxonomy_meta = fetch("taxonomy")
    wide, _ = conditional_rows(lists, taxonomy, NATIVE_SCOPE_WIDE)
    complete, _ = conditional_rows(lists, taxonomy, NATIVE_SCOPE_COMPLETE)
    complete_ids = {s(row["entity_ID"]) for row in complete}
    selected = [
        row for row in wide
        if s(row["entity_ID"]) in complete_ids
        and s(row.get("restricted")) != "1"
        and s(row.get("entity_class")) == PRIMARY_CHILD_CLASS
    ]
    entities = unique_entities(selected, public_only=True)
    islands = {
        eid for eid, row in entities.items()
        if row["entity_class"] == PRIMARY_CHILD_CLASS
    }
    lists_by_entity = defaultdict(set)
    for row in selected:
        lists_by_entity[s(row["entity_ID"])].add(s(row["list_ID"]))

    misc = {}
    misc_meta = {}
    for var in MISC_VARS:
        rows, meta = fetch("geoentities_env_misc", extra={"envvar": var})
        misc[var] = {s(row["entity_ID"]): row.get(var) for row in rows}
        misc_meta[var] = meta

    climate = {}
    climate_meta = {}
    for layer in CLIMATE_LAYERS:
        rows, meta = fetch(
            "geoentities_env_raster",
            extra={"layername": layer, "sumstat": "mean"},
        )
        climate[layer] = {
            s(row["entity_ID"]): row.get("mean")
            for row in rows
        }
        climate_meta[layer] = meta

    required_misc = ("area", "dist", "SLMP", "GMMC", "longitude", "latitude")
    predictor_complete = {
        eid for eid in islands
        if all(misc[var].get(eid) not in (None, "") for var in required_misc)
        and all(climate[layer].get(eid) not in (None, "") for layer in CLIMATE_LAYERS)
        and any(
            misc[var].get(eid) not in (None, "")
            for var in ("arch_lvl_1", "arch_lvl_2", "arch_lvl_3")
        )
    }

    path_by_island = {}
    for eid in predictor_complete:
        path = tuple(
            s(misc[var].get(eid)).strip()
            for var in ("arch_lvl_1", "arch_lvl_2", "arch_lvl_3")
            if misc[var].get(eid) not in (None, "")
        )
        if path:
            path_by_island[eid] = path

    exclusion = json.loads(args.exclusion_json.read_text(encoding="utf-8"))
    if exclusion.get("schema") != "structural.gift_aislands_closed_system_exclusion.v0_1":
        raise RuntimeError("unexpected closed-system exclusion receipt schema")
    if exclusion.get("response_values_accessed") is not False:
        raise RuntimeError("closed-system exclusion receipt is not response blind")
    if exclusion.get("aislands_species_data_requested") is not False:
        raise RuntimeError("closed-system exclusion opened A-Islands species data")
    expected_exclusion_receipt = "ac3a6ae7d49350b3d908119458c0e710be90e9efec38ccb9665988e1a9a1f644"
    if exclusion.get("receipt_sha256") != expected_exclusion_receipt:
        raise RuntimeError(
            "closed-system exclusion receipt drifted: "
            f"{exclusion.get('receipt_sha256')} != {expected_exclusion_receipt}"
        )
    exact_overlap = set(exclusion.get("excluded_gift_entity_ids", []))
    contaminated_paths = {
        tuple(path) for path in exclusion.get("contaminated_archipelago_paths", [])
    }
    ais_meta = {
        "receipt_sha256": exclusion["receipt_sha256"],
        "record_id": exclusion["aislands_record_id"],
        "polygon_count": exclusion["aislands_geometry_polygon_count"],
        "geometry_files": exclusion["aislands_geometry_files"],
    }
    clean_islands = {
        eid for eid in predictor_complete
        if path_by_island.get(eid) not in contaminated_paths
    }

    groups = defaultdict(list)
    for eid in clean_islands:
        path = path_by_island.get(eid)
        if path:
            groups[path].append(eid)
    groups = {
        path: sorted(ids, key=int)
        for path, ids in groups.items()
        if len(ids) >= MIN_ARCHIPELAGO_ISLANDS
    }

    frozen_island_ids = sorted(
        {eid for ids in groups.values() for eid in ids},
        key=int,
    )
    global_q75 = set(rank_tail(frozen_island_ids, misc["dist"], 0.25))
    global_q70 = set(rank_tail(frozen_island_ids, misc["dist"], 0.30))
    global_q80 = set(rank_tail(frozen_island_ids, misc["dist"], 0.20))

    group_rows = []
    for path, ids in sorted(groups.items()):
        gmmc = [int(float(misc["GMMC"][eid])) for eid in ids]
        frac = sum(gmmc) / len(gmmc)
        blocks, block_sizes = mst_blocks(
            ids, misc["longitude"], misc["latitude"], N_SPATIAL_BLOCKS
        )
        q75 = [eid for eid in ids if eid in global_q75]
        q70 = [eid for eid in ids if eid in global_q70]
        q80 = [eid for eid in ids if eid in global_q80]
        island_rows = []
        for eid in ids:
            island_rows.append({
                "entity_ID": eid,
                "list_IDs": sorted(lists_by_entity[eid], key=int),
                "dist_km": float(misc["dist"][eid]),
                "GMMC": int(float(misc["GMMC"][eid])),
                "spatial_block": blocks[eid],
                "extreme_q75": eid in set(q75),
                "extreme_q70": eid in set(q70),
                "extreme_q80": eid in set(q80),
            })
        group_rows.append({
            "archipelago_id": " / ".join(path),
            "archipelago_path": list(path),
            "n_islands": len(ids),
            "gmmc_connected_fraction": frac,
            "history_bin": history_bin(frac),
            "block_sizes": block_sizes,
            "q75_extreme_n": len(q75),
            "q75_nonextreme_n": len(ids) - len(q75),
            "h1_extreme_contributor": len(q75) >= 3,
            "h1_nonextreme_contributor": (len(ids) - len(q75)) >= 3,
            "h1_paired_contributor": len(q75) >= 3 and (len(ids) - len(q75)) >= 3,
            "q75_extreme_fraction": len(q75) / len(ids),
            "membership_sha256": sha(ids),
            "list_id_set_sha256": sha(sorted(
                {lid for eid in ids for lid in lists_by_entity[eid]},
                key=int,
            )),
            "islands": island_rows,
        })

    extreme_only = sorted(
        [
            row for row in group_rows
            if row["h1_extreme_contributor"] and not row["h1_nonextreme_contributor"]
        ],
        key=lambda row: (row["n_islands"], row["archipelago_id"]),
    )
    mixed_regime = sorted(
        [row for row in group_rows if row["h1_paired_contributor"]],
        key=lambda row: (row["n_islands"], row["archipelago_id"]),
    )
    nonextreme_only = sorted(
        [
            row for row in group_rows
            if row["h1_nonextreme_contributor"] and not row["h1_extreme_contributor"]
        ],
        key=lambda row: (row["n_islands"], row["archipelago_id"]),
    )
    if len(extreme_only) < 2 or not mixed_regime or not nonextreme_only:
        raise RuntimeError(
            "response-blind pilot cannot cover two extreme-only, one paired, and one non-extreme-only archipelago"
        )

    # The checklist API exposes complete list contents, so evidence partitions
    # are disjoint archipelago/list surfaces. Pilot selection is geometry-only:
    # two extreme-only groups, one paired group, and one non-extreme-only group.
    # This leaves any additional paired group(s) available for the non-rescuing
    # paired H1 sensitivity.
    pilot_ids = {
        extreme_only[0]["archipelago_id"],
        extreme_only[1]["archipelago_id"],
        mixed_regime[0]["archipelago_id"],
        nonextreme_only[0]["archipelago_id"],
    }
    pilot = [row for row in group_rows if row["archipelago_id"] in pilot_ids]
    confirmatory = [row for row in group_rows if row["archipelago_id"] not in pilot_ids]

    all_final_islands = sorted(
        [i["entity_ID"] for row in group_rows for i in row["islands"]],
        key=int,
    )
    response_surface = sorted(
        [
            (row["archipelago_id"], i["entity_ID"], lid)
            for row in group_rows
            for i in row["islands"]
            for lid in i["list_IDs"]
        ]
    )

    payload = {
        "schema": "structural.gift_global_archipelago_universe.v0_1",
        "status": "predictor_complete_response_sealed_universe_frozen",
        "gift_version": VERSION,
        "response_values_accessed": False,
        "species_composition_endpoint_called": False,
        "target": "native Angiospermae checklist incidence",
        "filters": {
            "suit_geo": True,
            "complete_taxon": True,
            "complete_floristic": True,
            "native_indicated": True,
            "entity_class": PRIMARY_CHILD_CLASS,
            "public_only": True,
            "predictor_complete": True,
            "minimum_archipelago_islands": MIN_ARCHIPELAGO_ISLANDS,
        },
        "current_environment_reference": {
            "dataset": "WorldClim 2.0",
            "summary": "polygon mean",
            "layers": CLIMATE_LAYERS,
        },
        "isolation_metric": "GIFT dist",
        "extreme_rules": {
            "primary_q75": "top ceil(0.25*N) islands by GIFT dist across the complete frozen eligible-island universe; entity_ID tie-break",
            "sensitivity_q70": "top ceil(0.30*N) islands by GIFT dist across the complete frozen eligible-island universe; entity_ID tie-break; cannot rescue q75",
            "sensitivity_q80": "top ceil(0.20*N) islands by GIFT dist across the complete frozen eligible-island universe; entity_ID tie-break; cannot rescue q75",
            "primary_unchanged_from_prospective_v0_3": True,
        },
        "spatial_holdout": {
            "blocks_per_archipelago": N_SPATIAL_BLOCKS,
            "algorithm": "great-circle complete graph -> deterministic Kruskal MST -> cut the three longest MST edges; ties by entity_ID; components labelled by smallest entity_ID",
        },
        "closed_system_exclusion": {
            "rule": "exclude entire GIFT archipelago path if any predictor-complete member centroid is covered by verified A-Islands v1.0 polygon",
            "exact_overlap_islands": len(exact_overlap),
            "contaminated_archipelago_paths": [list(x) for x in sorted(contaminated_paths)],
            "aislands_geometry": ais_meta,
        },
        "n_final_archipelagos": len(group_rows),
        "n_final_islands": len(all_final_islands),
        "h1_support_counts": {
            "all_extreme_contributors": sum(row["h1_extreme_contributor"] for row in group_rows),
            "all_nonextreme_contributors": sum(row["h1_nonextreme_contributor"] for row in group_rows),
            "all_paired_contributors": sum(row["h1_paired_contributor"] for row in group_rows),
            "confirmatory_extreme_contributors": sum(row["h1_extreme_contributor"] for row in confirmatory),
            "confirmatory_nonextreme_contributors": sum(row["h1_nonextreme_contributor"] for row in confirmatory),
            "confirmatory_paired_contributors": sum(row["h1_paired_contributor"] for row in confirmatory),
        },
        "global_extreme_counts": {
            "q75": len(global_q75),
            "q70": len(global_q70),
            "q80": len(global_q80),
        },
        "final_island_set_sha256": sha(all_final_islands),
        "response_surface_manifest_sha256": sha(response_surface),
        "groups": group_rows,
        "partition_rule": {
            "axis": "archipelago/list_ID response surface",
            "reason": "GIFT checklist API exposes complete list contents and has no server-side work_ID response filter; strict pilot/confirmatory sealing therefore requires disjoint list surfaces",
            "pilot_selection": "geometry-only: two smallest extreme-only q75 contributors + smallest paired-regime q75 contributor + smallest non-extreme-only q75 contributor; ties by archipelago_id",
            "selection_uses_response": False,
            "pilot_effect_estimation_allowed": False,
        },
        "pilot_archipelagos": [row["archipelago_id"] for row in pilot],
        "confirmatory_archipelagos": [row["archipelago_id"] for row in confirmatory],
        "pilot_archipelago_count": len(pilot),
        "confirmatory_archipelago_count": len(confirmatory),
        "source_tables": {
            "lists": lists_meta,
            "taxonomy": taxonomy_meta,
            "misc": misc_meta,
            "climate": climate_meta,
        },
    }
    payload["universe_fingerprint"] = sha({
        "gift_version": VERSION,
        "filters": payload["filters"],
        "source_table_sha256": {
            "lists": lists_meta["sha256"],
            "taxonomy": taxonomy_meta["sha256"],
            "misc": {k: v["sha256"] for k, v in misc_meta.items()},
            "climate": {k: v["sha256"] for k, v in climate_meta.items()},
        },
        "closed_system_exclusion": payload["closed_system_exclusion"],
        "final_island_set_sha256": payload["final_island_set_sha256"],
        "response_surface_manifest_sha256": payload["response_surface_manifest_sha256"],
        "group_membership": {
            row["archipelago_id"]: row["membership_sha256"] for row in group_rows
        },
        "partition": {
            "pilot": payload["pilot_archipelagos"],
            "confirmatory": payload["confirmatory_archipelagos"],
        },
    })
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
