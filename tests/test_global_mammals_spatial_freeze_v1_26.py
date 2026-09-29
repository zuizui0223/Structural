from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/global_mammals_spatial_pilot_freeze_v1_26.json"
CONTRACT = ROOT / "development/global_mammals_spatial_pilot_contract_v1_25.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v126_freezes_exact_successful_v125_artifact():
    x = load(FREEZE)
    assert x["schema"] == "structural.global_mammals_spatial_pilot_freeze.v1_26"
    assert x["status"] == "GLOBAL_SPATIAL_PILOT_ARTIFACT_COMMITTED_BY_PROVENANCE"
    src = x["source_execution"]
    assert src["workflow_run_id"] == 36527735618
    assert src["workflow_head_sha"] == (
        "9333854097f15617b25a09ba79a67db4854c6b3f"
    )
    assert src["artifact_id"] == 11015850157
    assert src["artifact_digest"] == (
        "sha256:b34b0a30676b6294676860cdda4923e013c11a3263da46cb2e0b1f35680bb08c"
    )
    files = x["artifact_files"]
    assert files["island_partition.csv"]["sha256"] == (
        "3f85efb3b71423a8392cb1f7a5590c7b03cedef377fee0997df457a029b998bd"
    )
    assert files["block_table.csv"]["sha256"] == (
        "4646034c1e5cd408e252c6d187a763e292850edd5c7d1619567b634e410bb27d"
    )
    assert files["spatial_receipt.json"]["raw_sha256"] == (
        "0282a503943b8d63a8ff3e104da72fa210713fca5a357c64669225ecef7d1727"
    )


def test_v126_partition_matches_v125_predeclared_design():
    x = load(FREEZE)
    c = load(CONTRACT)
    p = x["partition"]
    assert p["island_count"] == 5592
    assert p["bioregion_count"] == 12
    assert p["total_block_count"] == c["spatial_blocks"]["expected_total_block_count"] == 219
    assert p["singleton_block_count"] == c["spatial_blocks"]["expected_singleton_block_count"] == 31
    assert p["pilot_block_count"] == c["pilot_split"]["expected_pilot_block_count"] == 50
    assert p["confirmatory_block_count"] == c["pilot_split"]["expected_confirmatory_block_count"] == 169
    assert p["pilot_island_count"] == c["pilot_split"]["expected_pilot_island_count"] == 1307
    assert p["confirmatory_island_count"] == c["pilot_split"]["expected_confirmatory_island_count"] == 4285
    assert p["current_isolation_q75_hex"] == c["primary_regime_freeze"]["expected_q75_hex"]
    assert p["extreme_confirmatory_island_count"] == (
        c["primary_regime_freeze"]["expected_extreme_island_count"]
    )


def test_every_bioregion_retains_confirmatory_support():
    x = load(FREEZE)
    audit = x["regional_audit"]
    assert len(audit) == 12
    for region, row in audit.items():
        assert row["pilot_blocks"] >= 1, region
        assert row["confirmatory_blocks"] >= 2, region
        assert row["pilot_islands"] >= 1, region
        assert row["confirmatory_islands"] >= 1, region


def test_v126_preserves_contaminated_macro_only_boundary():
    x = load(FREEZE)
    assert x["analysis_route"] == "contaminated_macro_analysis_only"
    b = x["response_boundary"]
    assert b["response_used_in_spatial_design"] is False
    assert b["Appendix_1_reopened"] is False
    assert b["mammal_species_names_opened"] is False
    assert b["mammal_occurrence_values_opened"] is False
    assert b["counts_as_fresh_confirmation"] is False
    assert b["fresh_system_denominator_contribution"] == 0
    assert b["original_fresh_chain_restored"] is False
    assert x["macro_model_reference_may_be_built"] is True
