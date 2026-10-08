import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_terminal_zhoushan_source_transport():
    x=json.loads((R/"development/zhoushan_official_source_terminal_v1_225.json").read_text())
    assert x["v225"]["source_docx_verified"] is False
    assert x["biological_outcomes_opened"]==0
    assert x["supplement_tables_opened"]==0
    assert x["same_official_endpoints_next_auto_retry_authorized"] is False
    assert x["GEB_HOLD"] is True
def test_biological_direction_is_literature_not_map_validation():
    x=json.loads((R/"development/marten_source_direction_literature_v1_226.json").read_text())
    assert len(x["ecological_contrast"])==2
    assert x["cannot_claim_general_source_reversal_new"] is True
    assert x["freshwater_example_not_original_marine_graph_validation"] is True
    assert x["GEB_scientific_HOLD"] is True
    assert x["eBird"] is False
