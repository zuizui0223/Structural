import json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("v251",ROOT/"scripts/camtrapasia_replicated_field_positives_v1_251.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def test_postoutcome_reuse_only_and_no_global_claim():
    c=json.loads((ROOT/"development/camtrapasia_replicated_wild_positives_contract_v1_251.json").read_text())
    assert c["frozen_input"]["workflow_run_id"]==37893632648
    assert c["no_source_camera_CSV_re_read"] is True
    assert c["no_original_IUCN_heldout_values_reopen"] is True
    assert c["no_global_GEB_model_validation"] is True
def test_reject_absent_original_evidence():
    try:m.evaluate({"status":"PASS_EXPLORATORY_FIELD_POSITIVE_ONLY_NO_MODEL_SCORE"})
    except ValueError:pass
    else:raise AssertionError("Unverified upstream biology aggregate accepted")
