"""v1.339 source publisher original ZIP availability only, never GET or decompress."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from galapagos_ant_source_transport_v1_339 import probe

class Response:
    status=200
    headers={"Content-Type":"application/zip","Content-Length":"100000"}
    def geturl(self):return "https://test.invalid/ipt/archive.do?r=test"
    def __enter__(self):return self
    def __exit__(self,*args):return False

def test_original_publisher_HEAD_uses_no_body_and_does_not_swap_versions():
    candidates=[
       {"source":"PENSOFT_SEPT2026","dataset_uuid":"new","url":"https://one.invalid/a","version_tag":"Sep"},
       {"source":"ECUADOR_JUN2026","dataset_uuid":"old","url":"https://two.invalid/b","version_tag":"Jun"}
    ]
    requested=[]
    def request(url,timeout):
        requested.append(url)
        return Response()
    rows=probe(candidates,requester=request)
    assert requested==["https://one.invalid/a","https://two.invalid/b"]
    assert rows[0]["source_dataset_UUID"]=="new"
    assert rows[1]["source_dataset_UUID"]=="old"
    assert all(x["response_body_bytes_read"]==0 for x in rows)
    assert all(x["HTTP_HEAD_source_accessible"] for x in rows)

def test_transport_error_is_recorded_as_not_source_evidence():
    import urllib.error
    def failed(url,timeout):raise urllib.error.HTTPError(url,404,"Not Found",{},None)
    r=probe([{"source":"A","dataset_uuid":"n","url":"https://one.invalid/a","version_tag":"Sep"}],requester=failed)
    assert r[0]["HTTP_HEAD_source_accessible"] is False
    assert r[0]["HTTP_error_status"]==404
    assert r[0]["response_body_bytes_read"]==0
