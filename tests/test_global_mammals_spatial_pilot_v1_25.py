from __future__ import annotations

import json
from pathlib import Path

from scripts.freeze_global_mammals_spatial_pilot_v1_25 import (
    block_id,
    block_key,
    freeze,
    type7_quantile,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/global_mammals_spatial_pilot_contract_v1_25.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_real_contract_freezes_global_response_independent_design():
    x = load_contract()
    assert x["analysis_route"] == "contaminated_macro_analysis_only"
    assert x["safe_artifact"]["safe_row_count"] == 5592
    assert x["spatial_blocks"]["tile_width_degrees"] == 10.0
    assert x["spatial_blocks"]["expected_total_block_count"] == 219
    assert x["pilot_split"]["expected_bioregion_count"] == 12
    assert x["pilot_split"]["expected_pilot_block_count"] == 50
    assert x["pilot_split"]["expected_confirmatory_block_count"] == 169
    assert x["pilot_split"]["expected_pilot_island_count"] == 1307
    assert x["pilot_split"]["expected_confirmatory_island_count"] == 4285
    assert x["primary_regime_freeze"]["expected_q75_hex"] == (
        "-0x1.72b020c49ba5ep-1"
    )
    assert x["primary_regime_freeze"]["expected_extreme_island_count"] == 1074
    boundary = x["response_boundary"]
    assert boundary["Appendix_1_may_be_reopened"] is False
    assert boundary["response_used_in_spatial_design"] is False
    assert boundary["fresh_system_denominator_contribution"] == 0
    assert boundary["original_fresh_chain_restored"] is False


def test_block_key_wraps_dateline_and_separates_bioregions():
    left = block_key(
        bioregion="Oceanina",
        latitude=0.0,
        longitude=-180.0,
    )
    right = block_key(
        bioregion="Oceanina",
        latitude=0.0,
        longitude=180.0,
    )
    assert left == right
    other = block_key(
        bioregion="Australian",
        latitude=0.0,
        longitude=-180.0,
    )
    assert other != left
    assert block_id(left).startswith("GB_")
    assert len(block_id(left)) == 15


def test_type7_quantile_is_frozen_linear_rule():
    assert type7_quantile([0.0, 1.0, 2.0, 3.0, 4.0], 0.75) == 3.0
    assert type7_quantile([0.0, 10.0], 0.25) == 2.5


def test_small_realm_stratified_split_is_disjoint_and_complete():
    contract = load_contract()
    contract = json.loads(json.dumps(contract))
    contract["validation"]["expected_total_islands"] = 6
    contract["spatial_blocks"]["expected_total_block_count"] = 6
    contract["spatial_blocks"]["expected_singleton_block_count"] = 6
    contract["pilot_split"]["expected_bioregion_count"] = 2
    contract["pilot_split"]["expected_pilot_block_count"] = 2
    contract["pilot_split"]["expected_confirmatory_block_count"] = 4
    contract["pilot_split"]["expected_pilot_island_count"] = 2
    contract["pilot_split"]["expected_confirmatory_island_count"] = 4

    raw = [
        ("1", "A", -10.0, -170.0, -3.0),
        ("2", "A", 0.0, -20.0, -2.0),
        ("3", "A", 10.0, 120.0, -1.0),
        ("4", "B", -30.0, -100.0, 0.0),
        ("5", "B", 20.0, 10.0, 1.0),
        ("6", "B", 40.0, 130.0, 2.0),
    ]
    rows = [
        {
            "ID": island,
            "bioregion": region,
            "latitude": lat,
            "longitude": lon,
            "current_isolation": isolation,
            "block_key": block_key(
                bioregion=region,
                latitude=lat,
                longitude=lon,
            ),
        }
        for island, region, lat, lon, isolation in raw
    ]

    # Freeze the expected response-independent Q75 after deriving the synthetic
    # split under the identical rule, then rerun through the full validator.
    # This does not use any biological response.
    import hashlib, math
    from collections import defaultdict

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["block_key"]].append(row)
    by_region = defaultdict(list)
    for key in grouped:
        by_region[key.split("|", 1)[0]].append(key)
    pilot = set()
    salt = contract["pilot_split"]["ranking_salt"]
    for region, keys in by_region.items():
        ordered = sorted(
            keys,
            key=lambda key: (
                hashlib.sha256(f"{salt}|{key}".encode()).hexdigest(),
                key,
            ),
        )
        pilot.add(ordered[0])
    confirm_values = [
        row["current_isolation"]
        for row in rows
        if row["block_key"] not in pilot
    ]
    q75 = type7_quantile(confirm_values, 0.75)
    contract["primary_regime_freeze"]["expected_q75_hex"] = float(q75).hex()
    contract["primary_regime_freeze"]["expected_extreme_island_count"] = sum(
        value >= q75 for value in confirm_values
    )

    receipt, island_text, block_text = freeze(rows, contract)
    assert receipt["island_count"] == 6
    assert receipt["total_block_count"] == 6
    assert receipt["pilot_block_count"] == 2
    assert receipt["confirmatory_block_count"] == 4
    assert receipt["pilot_island_count"] == 2
    assert receipt["confirmatory_island_count"] == 4
    assert receipt["response_used_in_spatial_design"] is False
    assert receipt["Appendix_1_reopened"] is False
    assert receipt["mammal_occurrence_values_opened"] is False
    assert receipt["fresh_system_denominator_contribution"] == 0
    assert "pilot" in island_text
    assert "confirmatory" in island_text
    assert block_text.count("\n") == 7
