from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
 p=ROOT/"scripts/build_global_mammals_reference_operator_v1_40.py"
 spec=importlib.util.spec_from_file_location("gmv140",p)
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_region_specific_k_can_differ():
 m=load_module()
 # One compact chain connects at k=1.
 a=[("a1",0.0,0.0),("a2",0.0,0.1),("a3",0.0,0.2)]
 ka,_=m.choose_region_graph(a)
 # Two tight pairs need k>1 to bridge.
 b=[("b1",0.0,0.0),("b2",0.0,0.01),("b3",0.0,10.0),("b4",0.0,10.01)]
 kb,_=m.choose_region_graph(b)
 assert ka==1
 assert kb>ka

def test_v140_contract_waits_for_post_overlap_population():
 x=json.loads((ROOT/"development/global_mammals_reference_operator_contract_v1_40.json").read_text())
 assert x["population"]["must_use_successful_v1_39_post_historical_overlap_partition"] is True
 assert x["generic_network_R2"]["common_k_across_bioregions"] is False
 assert x["response_boundary"]["Appendix1_access_authorized"] is False

def test_overlap_retry_changes_no_science():
 x=json.loads((ROOT/"development/global_mammals_historical_overlap_retry_request_v1_39.json").read_text())
 assert x["matching_rules_changed"] is False
 assert x["failed_run"]["failed_before_overlap_script_body"] is True
 assert x["Appendix1_access_authorized"] is False
