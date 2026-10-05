#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/ebird_prebiology_handoff_contract_v1_159.json"
ACQ=ROOT/"scripts/run_ebird_sed_handoff_v1_157.py"
DESIGN=ROOT/"scripts/build_ebird_three_wave_design_v1_158.py"
class Stop(RuntimeError): pass

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def run(args):
    cp=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    if cp.returncode!=0:
        raise Stop((cp.stdout+"\n"+cp.stderr)[-8000:])

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("sed_file",type=Path)
    ap.add_argument("island_geometry",type=Path)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(CONTRACT.read_text())
    if c.get("schema")!="structural.ebird_prebiology_handoff_contract.v1_159":
        raise Stop("contract schema drift")
    out=a.output_dir; out.mkdir(parents=True,exist_ok=True)
    try:
        s0=sha256(a.sed_file); g0=sha256(a.island_geometry)
        acq=out/"acquisition"
        run([sys.executable,str(ACQ),str(a.sed_file),str(a.island_geometry),"--output-dir",str(acq)])
        if sha256(a.sed_file)!=s0 or sha256(a.island_geometry)!=g0: raise Stop("input bytes changed after acquisition chain")
        ar=json.loads((acq/"ebird_sed_handoff_receipt.json").read_text())
        sr=json.loads((acq/"support_chain"/"ebird_sed_support_chain_receipt.json").read_text())
        req=c["required_parent_status"]
        if ar.get("status")!=req["acquisition"]: raise Stop("acquisition handoff did not qualify")
        if sr.get("status")!=req["support_chain"]: raise Stop("support chain did not qualify")

        design=out/"design"; design.mkdir(parents=True,exist_ok=True)
        surface=acq/"support_chain"/"survey"/"ebird_island_year_survey_surface.csv"
        run([sys.executable,str(DESIGN),str(surface),
             "--windows-output",str(design/"ebird_three_wave_windows.csv"),
             "--islands-output",str(design/"ebird_three_wave_islands.csv"),
             "--receipt",str(design/"ebird_three_wave_design_receipt.json")])
        if sha256(a.sed_file)!=s0 or sha256(a.island_geometry)!=g0: raise Stop("input bytes changed after three-wave design")
        dr=json.loads((design/"ebird_three_wave_design_receipt.json").read_text())
        if dr.get("status")!=req["three_wave_design"]: raise Stop("three-wave design did not qualify")
        if int(dr.get("confirmatory_windows",0))<int(c["success_requirements"]["minimum_confirmatory_windows"]):
            raise Stop("confirmatory window minimum drift")
        for obj in (ar,sr,dr):
            for k in ("species_identity_opened","species_detection_opened","species_nondetection_constructed",
                      "annual_species_occupancy_constructed","source_loss_events_constructed","t2_outcome_opened"):
                if k in obj and obj[k] not in (False,0): raise Stop(f"response boundary violated: {k}")
        result={
          "schema":"structural.ebird_prebiology_handoff_result.v1_159",
          "status":"RESPONSE_INDEPENDENT_PREBIOLOGY_HANDOFF_COMPLETE",
          "candidate_id":c["candidate_id"],
          "sed_sha256":s0,"island_geometry_sha256":g0,
          "acquisition_receipt_sha256":sha256(acq/"ebird_sed_handoff_receipt.json"),
          "support_chain_receipt_sha256":sha256(acq/"support_chain"/"ebird_sed_support_chain_receipt.json"),
          "three_wave_design_receipt_sha256":sha256(design/"ebird_three_wave_design_receipt.json"),
          "windows_sha256":dr["windows_sha256"],"islands_sha256":dr["islands_sha256"],
          "pilot_window_ids":dr["pilot_window_ids"],"confirmatory_window_ids":dr["confirmatory_window_ids"],
          "species_response_opened":False,"source_loss_events_constructed":False,
          "response_access_authorized":False,"counts_as_empirical_source_loss_evidence":False
        };code=0
    except Exception as e:
        if isinstance(e,(KeyboardInterrupt,SystemExit)): raise
        result={"schema":"structural.ebird_prebiology_handoff_result.v1_159","status":"STOP","reason":str(e),
                "species_response_opened":False,"source_loss_events_constructed":False,
                "response_access_authorized":False,"counts_as_empirical_source_loss_evidence":False};code=2
    (out/"ebird_prebiology_handoff_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code
if __name__=="__main__": raise SystemExit(main())
