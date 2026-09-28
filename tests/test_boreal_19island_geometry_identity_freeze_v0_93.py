from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/boreal_19island_geometry_identity_freeze_v0_93.json"


def test_v093_freezes_v092_identity_before_any_header_access():
    x = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert x["schema"] == "structural.boreal_19island_geometry_identity_freeze.v0_93"
    assert x["status"] == "OPAQUE_BYTE_IDENTITY_FROZEN_BEFORE_HEADER_ACCESS"
    assert x["source_execution"]["run_id"] == 36409002955
    assert x["source_execution"]["head_sha"] == (
        "8a86b478d50eeb574b8a62c1ab9ab0179c880cd5"
    )
    assert x["file"] == {
        "name": "alpha_diversity_model_selection_19islands.csv",
        "dryad_file_id": 4569035,
        "dryad_version_id": 422440,
        "dryad_version_number": 7,
        "size_bytes": 2486,
        "sha256": "e40a653de7b01e5ba4c54f69577842d4d246cf179cdfc41d487693eb3c2baf43",
    }
    access = x["access_state_at_freeze"]
    assert access["header_decoded"] is False
    assert access["data_rows_semantically_opened"] == 0
    assert access["safe_row_values_opened"] is False
    assert access["biological_response_values_opened"] is False
    assert access["counts_as_empirical_evidence"] is False
    assert x["header_access_authorized_by_this_freeze"] is False
    assert x["safe_row_projection_authorized"] is False
