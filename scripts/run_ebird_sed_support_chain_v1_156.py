#!/usr/bin/env python3
"""Run the response-independent eBird SED support chain on identical bytes."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/ebird_sed_support_chain_contract_v1_156.json"
AUDIT=ROOT/"scripts/audit_ebird_sampling_event_metadata_v1_154.py"
SURVEY=ROOT/"scripts/build_ebird_island_year_survey_surface_v1_155.py"

class Stop(RuntimeError): pass

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def run_child(args:list[str]):
    cp=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    if cp.returncode!=0:
        tail=(cp.stdout+"\n"+cp.stderr)[-8000:]
        raise Stop(f"child failed ({cp.returncode}): {tail}")
    return cp

def validate_receipts(audit:dict,survey:dict,contract:dict):
    req=contract["success_requirements"]
    if audit.get("status")!=req["metadata_status"]:raise Stop("metadata audit did not qualify")
    if survey.get("status")!=req["survey_status"]:raise Stop("survey surface did not qualify")
    if audit.get("detected_protocol_schema")!=survey.get("detected_protocol_schema"):
        raise Stop("child protocol-schema disagreement")
    if int(audit.get("species_headers_seen",-1))!=0:raise Stop("metadata audit saw species headers")
    if int(audit.get("species_values_read",-1))!=0:raise Stop("metadata audit read species values")
    if int(audit.get("species_nondetections_constructed",-1))!=0:raise Stop("metadata audit constructed nondetections")
    for k in ("species_identity_read","species_detection_read","species_nondetection_constructed",
              "annual_species_occupancy_constructed","source_loss_events_constructed"):
        if survey.get(k) not in (False,0):raise Stop(f"survey response boundary violated: {k}")
    if audit.get("response_access_authorized") is not False or survey.get("response_access_authorized") is not False:
        raise Stop("child response authorization drift")
    return True

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("sed_file",type=Path)
    ap.add_argument("island_geometry",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()

    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if c.get("schema")!="structural.ebird_sed_support_chain_contract.v1_156":
        raise Stop("contract schema drift")
    out=args.output_dir
    audit_out=out/"audit";survey_out=out/"survey"
    audit_out.mkdir(parents=True,exist_ok=True);survey_out.mkdir(parents=True,exist_ok=True)

    try:
        sed0=sha256(args.sed_file)
        geom=sha256(args.island_geometry)

        run_child([sys.executable,str(AUDIT),str(args.sed_file),"--output-dir",str(audit_out)])
        sed1=sha256(args.sed_file)
        if sed1!=sed0:raise Stop("SED bytes changed during metadata audit")

        run_child([sys.executable,str(SURVEY),str(args.sed_file),str(args.island_geometry),"--output-dir",str(survey_out)])
        sed2=sha256(args.sed_file)
        if sed2!=sed0:raise Stop("SED bytes changed during island-year build")

        ar=audit_out/"ebird_sed_schema_receipt.json"
        sr=survey_out/"ebird_island_year_survey_receipt.json"
        sf=survey_out/"ebird_island_year_survey_surface.csv"
        audit=json.loads(ar.read_text())
        survey=json.loads(sr.read_text())
        validate_receipts(audit,survey,c)
        if survey.get("sed_sha256")!=sed0:raise Stop("survey receipt SED SHA mismatch")
        if survey.get("island_geometry_sha256")!=geom:raise Stop("survey receipt geometry SHA mismatch")

        receipt={
          "schema":"structural.ebird_sed_support_chain_result.v1_156",
          "status":"SAME_BYTE_RESPONSE_INDEPENDENT_SED_SUPPORT_CHAIN_FROZEN",
          "candidate_id":c["candidate_id"],
          "sed_sha256":sed0,
          "island_geometry_sha256":geom,
          "detected_protocol_schema":audit["detected_protocol_schema"],
          "metadata_audit_receipt_sha256":sha256(ar),
          "survey_receipt_sha256":sha256(sr),
          "survey_surface_sha256":sha256(sf),
          "checklist_rows":audit["checklist_rows"],
          "complete_checklists":audit["complete_checklists"],
          "surveyed_island_years":survey["surveyed_island_years"],
          "distinct_surveyed_islands":survey["distinct_surveyed_islands"],
          "species_identity_read":False,
          "species_detection_read":False,
          "species_nondetection_constructed":False,
          "annual_species_occupancy_constructed":False,
          "source_loss_events_constructed":False,
          "raw_sed_rows_persisted":False,
          "response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False
        };code=0
    except Exception as e:
        if isinstance(e,(KeyboardInterrupt,SystemExit)):raise
        receipt={
          "schema":"structural.ebird_sed_support_chain_result.v1_156","status":"STOP","reason":str(e),
          "species_identity_read":False,"species_detection_read":False,"species_nondetection_constructed":False,
          "annual_species_occupancy_constructed":False,"source_loss_events_constructed":False,
          "raw_sed_rows_persisted":False,"response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False
        };code=2

    out.mkdir(parents=True,exist_ok=True)
    (out/"ebird_sed_support_chain_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
