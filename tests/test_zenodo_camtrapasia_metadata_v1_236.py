import json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v236",R/"scripts/zenodo_camtrapasia_metadata_v1_236.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_metadata_source_files_without_biological_values():
    payload={"id":10780971,"doi":m.DOI,
      "files":[{"key":k,"checksum":"md5:"+v,"size":1000} for k,v in m.EXPECTED.items()]}
    out=m.verify(payload)
    assert out["status"]=="PASS_OFFICIAL_ZENODO_FILE_IDENTITY_ONLY"
    assert out["file_bodies_downloaded"]==0
    assert out["camera_capture_rows_read"]==0
    assert out["original_mammal_heldout_response_read"]==0
def test_reject_wrong_data_file():
    p={"id":10780971,"doi":m.DOI,
       "files":[{"key":k,"checksum":"md5:"+v,"size":1000} for k,v in m.EXPECTED.items()]}
    p["files"][0]["checksum"]="md5:bad"
    try:m.verify(p)
    except ValueError:pass
    else:raise AssertionError("Invalid file checksum admitted")
def test_original_heldout_and_eBird_remain_closed():
    z=json.loads((R/"development/camtrapasia_public_source_contract_v1_236.json").read_text())
    assert z["api_permissions"]["forbid_file_download_in_v236"] is True
    assert z["research_intent"]["can_admit_as_global_mammal_validation"] is False
    assert all(v is False for v in z["safeguards"].values())
