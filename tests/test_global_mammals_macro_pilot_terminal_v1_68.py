from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_mammal_macro_pilot_failure_is_terminal_and_not_ecological_evidence():
    x=json.loads((ROOT/"development/global_mammals_macro_pilot_terminal_freeze_v1_68.json").read_text())
    assert x["status"]=="TERMINAL_MACRO_MAMMAL_PILOT_AFTER_SEMANTIC_ACCESS"
    assert x["terminal_result"]["pilot_response_consumed"] is True
    assert x["terminal_result"]["confirmatory_occurrence_values_decoded"]==0
    assert x["interpretation"]["ecological_primary_result_available"] is False
    assert x["interpretation"]["counts_as_support_or_non_support_for_C_minus_R3"] is False
    assert x["interpretation"]["same_protocol_retry_authorized"] is False
    assert x["response_boundary"]["counts_as_primary_confirmatory_evidence"] is False
