from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_origin_audit_is_metadata_only():
 x=json.loads((ROOT/"development/gift_geological_origin_metadata_contract_v1_48.json").read_text())
 assert x["query_scope"].startswith("metadata table only")
 assert x["response_boundary"]["entity_level_origin_values_authorized"] is False
 assert "GIFT_env entity-level value query" in x["forbidden"]
 assert "GMMC" in x["if_no_candidates_found"]

def test_origin_script_never_calls_GIFT_env_values():
 s=(ROOT/"scripts/audit_gift_geological_origin_metadata_v1_48.R").read_text()
 assert "GIFT_env_meta_misc" in s
 assert "GIFT::GIFT_env(" not in s
 assert "GIFT_checklists" not in s
