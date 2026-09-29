from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_overlap_freeze_removes_176_and_keeps_5401():
 x=json.loads((ROOT/"development/global_mammals_historical_overlap_freeze_v1_41.json").read_text())
 assert x["result"]["unique_global_overlap_ids"]==176
 assert x["result"]["retained_after_historical_overlap"]==5401
 assert x["exclusion_scope"]["remove_from_species_source_pool"] is True
 assert x["response_boundary"]["occurrence_values_opened"] is False

def test_final_reference_request_binds_exact_post_overlap_population():
 x=json.loads((ROOT/"development/global_mammals_reference_operator_request_v1_42.json").read_text())
 assert x["expected_final_islands"]==5401
 assert x["final_partition_sha256"]=="317801c21355c9859d1e59fe5a17a6d54ccc7755f9e322636811ba11bc0507db"
 assert x["Appendix1_access_authorized"] is False
