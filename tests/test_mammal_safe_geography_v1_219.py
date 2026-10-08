import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v219",ROOT/"scripts/compare_mammal_safe_geography_v1_219.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_safe_id_and_quantile():
    assert m.ident("001")=="1"
    for x in ("-1","2.0"," 2","2 "):
        try:m.ident(x)
        except ValueError:pass
        else:raise AssertionError(x)
    assert m.describe([1,2,3,4])["median"]==2.5
    assert m.describe([1,2,3,4])["q25"]==1.75
def test_contract_forbids_mammal_or_model_reads():
    r=json.loads((ROOT/"development/mammal_safe_geography_request_v1_219.json").read_text())
    assert r["source_all"]["rows"]==17883 and r["source_selected"]["rows"]==5401
    assert r["no_species_response_or_prediction_read"] is True
    assert r["nonselected_label"].endswith("NOT necessarily mammal-zero")
    assert all(z is False for z in r["policy"].values())
