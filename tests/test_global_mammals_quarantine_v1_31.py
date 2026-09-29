from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_quarantine_is_whole_block_and_never_restores_freshness():
 x=json.loads((ROOT/"development/global_mammals_contamination_quarantine_contract_v1_31.json").read_text())
 q=x["quarantine_rule"]
 assert q["unit"].startswith("entire pre-frozen v1.25 spatial block")
 assert q["remove_from_targets"] is True
 assert q["remove_from_training"] is True
 assert q["remove_from_species_source_pool"] is True
 assert q["replacement_block_allowed"] is False
 assert x["interpretation"]["fresh_status_restored"] is False
 assert x["Appendix1_access_authorized"] is False
def test_workflow_never_fetches_response():
 s=(ROOT/".github/workflows/global-mammals-quarantine-v1_31.yml").read_text()
 assert "Appendix_1" not in s
 assert "quarantine_global_mammals_exposed_block_v1_31.py" in s
 assert "actions/download-artifact@v4" in s
