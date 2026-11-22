#!/usr/bin/env python3
"""Cours2026 original RData: plot/site/resource NONRESPONSE audit only."""
import argparse, json, subprocess, tempfile
from pathlib import Path
import cours2026_rdata_schema_only as original

def known():
    assert original.SIZE==33531 and original.MD5=="34312f823dafa60568fa0cd92926ee37"
    print("COURS2026_RESPONSE_SEALED_NONRESPONSE_QA_FIXTURE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="cours2026_site_resource_QA/receipt.json")
    a=p.parse_args()
    known()
    if a.test:return
    result={
        "schema":"structural.cours2026_98source_plot_site_wood_resource_QA.v1",
        "original_DOI":original.DOI,
        "original_publisher_md5":original.MD5,
        "original_author_RData_bytes_uploaded":False,
        "new_beetle_response_cells_read":0,
        "new_scientific_effects_fitted":0,
        "prior_Ramberg2026_sci_STOP_unchanged":True,
        "prior_Korhonen2024_Dryad_401_unchanged":True,
        "eBird_used":False,"TinyFish_used":False,
        "status":"SOURCE_ORIGINAL_NONRESPONSE_QA_NOT_STARTED"
    }
    try:
        with tempfile.TemporaryDirectory(prefix="cours2026-QA-noresponse-") as temp:
            pth=Path(temp)/original.FILENAME
            pth.write_bytes(original.pinned_source())
            out=Path(temp)/"source_only_QA.json"
            cmd=["Rscript","analysis/forest_macro_global/cours2026_98_plot_site_resource_QA_only.R",
                 str(pth),str(out)]
            cp=subprocess.run(cmd,capture_output=True,text=True,timeout=75)
            if cp.returncode!=0 or not out.exists():
                raise ValueError("SOURCE_98PLOT_R_NONRESPONSE_RUNTIME_STOP")
            data=json.loads(out.read_text())
            if data.get("schema")!="structural.cours2026_original_98plot_site_resource_nonresponse_QA.v1":
                raise ValueError("SOURCE_ORIGINAL_NONRESPONSE_QA_SCHEMA_STOP")
            if (data.get("original_beetle_species_or_guild_response_cells_read")!=0 or
                data.get("original_new_predictive_scientific_score_count")!=0):
                raise ValueError("SOURCE_BEETLE_OR_PREDICTIVE_VALUES_OPENED_STOP")
            if data.get("original_source_row_total")!=98 or data.get("original_context_n")!=3:
                raise ValueError("SOURCE_ORIGINAL_98ROW_3CONTEXT_STOP")
            result["source_only_original_field_QA"]=data
            result["status"]="SOURCE_98ROW_SITE_RESOURCE_NONRESPONSE_QA_PASS"
    except Exception as e:
        result["status"]="SOURCE_ORIGINAL_SITE_RESOURCE_QA_STOP"
        result["error_type"]=type(e).__name__
        result["error_code"]=str(e)[:180] if isinstance(e,ValueError) else ""
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("COURS2026_ORIGINAL_SITE_RESOURCE_QA",result["status"])
    print("BEETLE_RESPONSE_ROWS_OPENED",result["new_beetle_response_cells_read"])
    print("NEW_ECOLOGICAL_SCORES",result["new_scientific_effects_fitted"])
if __name__=="__main__":
    main()
