"""Known-truth one-shot NEON source file-catalog access gate, no species rows."""
import importlib.util,io,json,urllib.error
from pathlib import Path

p=Path(__file__).with_name("probe_neon_beetle_original_file_access.py")
spec=importlib.util.spec_from_file_location("neon_original_access",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(url):
    code=url.split("/products/")[1].split("?")[0]
    return {
        "productCode":code,
        "siteCodes":[{"siteCode":"BART","availableReleases":[
          {"release":"RELEASE-2025","availableMonths":["2018-01"]},
          {"release":"RELEASE-2026","availableMonths":["2021-08","2021-07"]}
        ]}]
    }


class FileResponse:
    status=200
    def __init__(self,obj):self.content=json.dumps(obj).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,*args):return self.content


def test_http_200_reports_public_catalog_but_not_accessed_species():
    urls=[]
    def open_stub(request, timeout):
        urls.append(request.full_url)
        return FileResponse({"data":{"files":[{"name":"genus.csv"},{"name":"README.txt"}]}})
    r=m.probe(product_get=fixture,opener=open_stub)
    assert r["access_status"]=="PUBLIC_ORIGINAL_FILE_CATALOG_AVAILABLE"
    assert r["source_confirmed_three_product_sample_month"]=="2021-07"
    assert r["source_original_files_in_catalog"]==2
    assert r["original_file_types_catalog_frequency"][".csv"]==1
    assert r["downloaded_file_contents"] is False
    assert not r["original_beetle_species_count_or_plot_join_verified"]
    assert len(urls)==1
    assert "/DP1.10022.001/BART/2021-07?" in urls[0]


def test_access_401_is_not_non_support_of_thermal_hypothesis():
    calls=[]
    def unauthorized(request,timeout):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url,401,"Unauthorized",{},None)
    r=m.probe(product_get=fixture,opener=unauthorized)
    assert r["anonymous_Neon_beetle_file_catalog_http_status"]==401
    assert r["access_status"]=="ORIGINAL_FILES_REQUIRE_AUTHENTICATION_OR_ACCESS"
    assert r["source_original_files_in_catalog"] is None
    assert r["file_names_original_taxon_response_data_not_opened"]
    assert len(calls)==1


def test_no_source_three_product_month_intersection_stops_before_file_request():
    n=[0]
    def no_common(url):
        item=fixture(url)
        if "DP1.00002.001" in url:
            item["siteCodes"][0]["availableReleases"][-1]["availableMonths"]=["2022-01"]
        return item
    def no_files(req,timeout):
        n[0]+=1
        raise AssertionError("file download must not happen")
    try:
        m.probe(product_get=no_common,opener=no_files)
        assert False
    except ValueError as e:
        assert "no_common_original_site_calendar_month" in str(e)
    assert n[0]==0
