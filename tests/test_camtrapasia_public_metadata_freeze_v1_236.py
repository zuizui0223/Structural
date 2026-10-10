import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_official_source_file_sizes_and_provenance_freeze():
    a=json.loads((R/"development/camtrapasia_public_metadata_freeze_v1_236.json").read_text())
    assert a["status"]=="PASS_OFFICIAL_ZENODO_FILE_IDENTITY_ONLY"
    assert a["test_count_passed"]==3
    assert a["file_manifest"]["CamTrapAsia_Metadata_20231031_csv"]["bytes"]==245677
    assert a["file_manifest"]["Species_Traits_20231031_csv"]["bytes"]==67450
    assert a["source_biological_rows_opened"]==0
    assert a["original_mammal_heldout_response_reopened"] is False
