"""Token never appears in a URL, log or output; no unauthorized NEON downloads."""
import importlib.util, json, urllib.error
from pathlib import Path

p=Path(__file__).with_name("neon_authenticated_beetle_catalog_gate.py")
spec=importlib.util.spec_from_file_location("authenticated_neon_file_catalog",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Response:
    def __enter__(self):return self
    def __exit__(self,*args):return False
    status=200
    def read(self,*args):
        return json.dumps({"data":{"files":[
            {"name":"NEON.DP1.10022.001.basic.csv",
             "url":"https://temporary-signed-token-SECRET/expires-7-days"},
            {"name":"README.txt"}]}}).encode()


def test_not_configured_means_no_original_data_endpoint_request():
    def no_open(req,timeout):raise AssertionError("must not request without secret")
    x=m.probe(token=None,opener=no_open)
    assert x["access_status"]=="SCIENTIFIC_SOURCE_STOP_SECRET_NOT_CONFIGURED"
    assert not x["source_api_authentication_verified"]
    assert x["original_beetle_data_files_downloaded"]==0


def test_original_secure_header_only_and_no_url_or_secret_export():
    requests=[]
    def fake(req,timeout):
        requests.append(req)
        return Response()
    secret="THIS_IS_THE_LOCAL_SYNTHETIC_TEST_TOKEN_NEVER_EXPORTED"
    x=m.probe(token=secret,opener=fake)
    assert x["access_status"]=="ORIGINAL_SOURCE_FILE_CATALOG_ACCESS_GRANTED"
    assert x["source_api_authentication_verified"]
    assert x["original_file_catalog_n"]==2
    assert x["file_extension_aggregates"][".csv"]==1
    assert len(requests)==1
    assert requests[0].get_header("X-api-token")==secret
    assert secret not in requests[0].full_url
    assert secret not in json.dumps(x)
    assert "temporary-signed-token-SECRET" not in json.dumps(x)
    assert x["original_beetle_data_files_downloaded"]==0


def test_secret_present_but_auth_403_is_stop_not_biological_result():
    def forbidden(req,timeout):
        raise urllib.error.HTTPError(req.full_url,403,"Forbidden",{},None)
    x=m.probe(token="local_fake",opener=forbidden)
    assert x["access_status"]=="SOURCE_HTTP_403_ACCESS_STOP"
    assert not x["source_api_authentication_verified"]
    assert not x["forest_beetle_temperature_or_movement_effect_scored"]
    assert x["raw_token_or_signed_URL_or_taxa_never_saved"]
