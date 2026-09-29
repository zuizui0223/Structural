from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/global_mammals_appendix2_safe_rows_freeze_v1_24.json"
CONTRACT = ROOT / "development/global_mammals_appendix2_safe_rows_contract_v1_23.json"
FIREWALL = ROOT / "development/global_mammals_appendix2_column_firewall_v1_22.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v124_freezes_successful_v123_artifact_identity():
    x = load(FREEZE)
    assert x["schema"] == (
        "structural.global_mammals_appendix2_safe_rows_freeze.v1_24"
    )
    assert x["status"] == (
        "APPENDIX2_5592_SAFE_ROWS_COMMITTED_BY_ARTIFACT_PROVENANCE"
    )
    src = x["source_execution"]
    assert src["workflow_run_id"] == 36524988694
    assert src["workflow_head_sha"] == (
        "ea565b98419f8aacde9fb13c26724bb385635b95"
    )
    assert src["artifact_id"] == 11013887248
    assert src["artifact_digest"] == (
        "sha256:f740c6762a7414f624c7d920a5a4316a062cba803ed9ad426e4f97d36598d9e8"
    )
    files = x["artifact_files"]
    assert files["appendix2_safe_rows.csv"] == {
        "size_bytes": 1310008,
        "sha256": "b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8",
    }
    assert files["safe_rows_receipt.json"]["raw_sha256"] == (
        "b303251ba2a50a664e39434739c3f1751969e1b694063de0afb6e5a8e52acc78"
    )


def test_v124_population_matches_predeclared_v123_ceiling():
    x = load(FREEZE)
    c = load(CONTRACT)
    firewall = load(FIREWALL)
    pop = x["safe_population"]
    assert pop["row_count"] == c["source"]["expected_data_row_count"] == 5592
    assert pop["distinct_id_count"] == 5592
    assert pop["safe_column_count"] == len(c["safe_columns_in_source_order"]) == 13
    assert x["safe_columns"] == c["safe_columns_in_source_order"]
    assert x["safe_columns"] == firewall["safe_columns_in_source_order"]
    assert pop["safe_csv_sha256"] == (
        "b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8"
    )
    assert pop["routing_id_order_sha256"] == (
        "438b76e167b302fdf79827a2c9f6f9eb8bf354af5730f44506536f15d8af92a6"
    )
    assert pop["null_counts_all_zero"] is True
    assert x["spatial_design_may_be_built"] is True


def test_v124_does_not_restore_freshness_or_response_access():
    x = load(FREEZE)
    boundary = x["semantic_boundary"]
    assert x["analysis_route"] == "contaminated_macro_analysis_only"
    assert boundary["Appendix_1_response_file_reopened"] is False
    assert boundary["biological_response_values_opened_in_v1_23"] is False
    assert boundary["closed_unneeded_cell_values_decoded"] == 0
    assert boundary["protected_response_derived_cell_values_decoded"] == 0
    assert boundary["counts_as_empirical_evidence"] is False
    assert boundary["counts_as_fresh_confirmation"] is False
    assert boundary["fresh_system_denominator_contribution"] == 0
    assert boundary["original_global_mammal_fresh_chain_restored"] is False
