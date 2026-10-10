#!/usr/bin/env python3
"""v1.220: identification limits of terminal landscape-level joint retention.

Constructive known-truth demonstration. No empirical source outcome is opened.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path


def overlap_bounds(patches: int, g_patches: int, s_patches: int) -> tuple[int, int]:
    """Tight bounds for count of patches occupied by BOTH guilds.

    Only patch count and marginal numbers of occupied patches are known.
    """
    if any(type(x) is not int for x in (patches, g_patches, s_patches)):
        raise TypeError("Integer patch occupancy counts required")
    if not (patches >= 1 and 0 <= g_patches <= patches and 0 <= s_patches <= patches):
        raise ValueError("Counts must lie in [0, patches]")
    return max(0, g_patches + s_patches - patches), min(g_patches, s_patches)


def allocate_extreme(patches: int, g_patches: int, s_patches: int,
                     kind: str) -> dict[str, list[int] | int]:
    """Construct arrangements realizing each endpoint of the tight bound."""
    lower, upper = overlap_bounds(patches, g_patches, s_patches)
    g = list(range(g_patches))
    if kind == "lower":
        s = list(range(patches - s_patches, patches))
        expected = lower
    elif kind == "upper":
        s = list(range(min(g_patches, s_patches)))
        remaining = s_patches - len(s)
        s.extend(range(g_patches, g_patches + remaining))
        expected = upper
    else:
        raise ValueError("kind must be lower or upper")
    actual = len(set(g) & set(s))
    if actual != expected or len(set(s)) != s_patches:
        raise AssertionError("Constructive proof failed")
    return {"g_occupied_patch_ids": g, "s_occupied_patch_ids": s,
            "co_occupied_patches": actual}


def landscape_endpoint(layout: dict[str, list[int] | int]) -> dict[str, bool]:
    """Landscape-level binary endpoint used in the published 176-row table."""
    return {
        "generalist_somewhere": bool(layout["g_occupied_patch_ids"]),
        "specialist_somewhere": bool(layout["s_occupied_patch_ids"]),
        "both_guilds_somewhere": (bool(layout["g_occupied_patch_ids"])
                                  and bool(layout["s_occupied_patch_ids"]))
    }


def patch_transition(source_t: list[int], final_t1: list[int], patches: int) -> dict[str, int]:
    if any(not 0 <= x < patches for x in source_t + final_t1):
        raise ValueError("Out-of-bounds patch ID")
    a, b = set(source_t), set(final_t1)
    return {
        "occupied_at_t": len(a), "occupied_at_t1": len(b),
        "local_0_to_1": len(b-a), "local_1_to_0": len(a-b),
        "local_1_to_1": len(a & b)
    }


def run() -> dict:
    # The real Wolfe six-patch heterogeneous treatment has 12,12,12,4,4,4 mL.
    # These are SYNTHETIC allocations, NOT reconstructions of its six patches.
    size_ml = [12, 12, 12, 4, 4, 4]
    separated = allocate_extreme(6, 2, 2, "lower")
    shared = allocate_extreme(6, 2, 2, "upper")
    stable = patch_transition([0, 1], [0, 1], 6)
    colonization = patch_transition([1], [0, 1], 6)
    assert landscape_endpoint(separated) == landscape_endpoint(shared)
    assert separated["co_occupied_patches"] == 0
    assert shared["co_occupied_patches"] == 2
    assert stable["local_0_to_1"] == 0 and colonization["local_0_to_1"] == 1
    return {
        "schema": "structural.wolfe_terminal_endpoint_identifiability.v1_220",
        "status": "PASS_SYNTHETIC_KNOWN_TRUTH_NOT_BIOLOGICAL_REANALYSIS",
        "patch_sizes_ml": size_ml,
        "marginal_patch_occupancies_synthetic": {"G":2,"S":2},
        "tight_local_joint_patch_count_bounds": list(overlap_bounds(6,2,2)),
        "arrangements": {"segregated":separated, "co_located":shared},
        "landscape_endpoint_both": landscape_endpoint(separated),
        "spatial_arrangements_indistinguishable_to_terminal_landscape_endpoint": True,
        "same_final_generalist_patch_map_different_histories": {
            "without_colonization":stable,"with_colonization":colonization
        },
        "local_colonization_unidentifiable_from_t1_only": True,
        "reference_is_published_landscape_data": False,
        "raw_Wolfe_outcomes_accessed": False,
        "empirical_occupancy_or_transition_claim": False,
        "eBird_used": False, "GEB_submission_authorized": False
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    a=p.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run(), sort_keys=True))

if __name__=="__main__":
    main()
