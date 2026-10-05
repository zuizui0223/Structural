#!/usr/bin/env python3
"""Local handoff for an official eBird Sampling Event Data file.

Runs only the already-frozen response-independent v1.156 support chain and
writes a compact handoff receipt. Species-response access remains forbidden.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHAIN=ROOT/"scripts/run_ebird_sed_support_chain_v1_156.py"
CONTRACT=ROOT/"development/ebird_sed_acquisition_handoff_v1_157.json"
class Stop(RuntimeError): pass

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("sed_file",type=Path)
    ap.add_argument("island_geometry",type=Path)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(CONTRACT.read_text())
    if c.get("schema")!="structural.ebird_sed_acquisition_handoff.v1_157":
        raise Stop("contract schema drift")
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    try:
        sed_sha0=sha256(a.sed_file); geom_sha=sha256(a.island_geometry)
        cp=subprocess.run(
          [sys.executable,str(CHAIN),str(a.sed_file),str(a.island_geometry),"--output-dir",str(out/"support_chain")],
          cwd=ROOT,text=True,capture_output=True)
        if cp.returncode!=0:
            raise Stop("v1.156 support chain failed: "+(cp.stdout+"\n"+cp.stderr)[-8000:])
        sed_sha1=sha256(a.sed_file)
        if sed_sha1!=sed_sha0: raise Stop("SED bytes changed during handoff")
        chain_path=out/"support_chain"/"ebird_sed_support_chain_receipt.json"
        chain=json.loads(chain_path.read_text())
        req=c["success_requirements"]
        if chain.get("status")!=req["support_chain_status"]: raise Stop("support chain did not qualify")
        for key in ("species_identity_read","species_detection_read","species_nondetection_constructed",
                    "annual_species_occupancy_constructed","source_loss_events_constructed","response_access_authorized"):
            if chain.get(key) is not False: raise Stop(f"response boundary violated: {key}")
        if chain.get("sed_sha256")!=sed_sha0: raise Stop("support-chain SED SHA mismatch")
        if chain.get("island_geometry_sha256")!=geom_sha: raise Stop("geometry SHA mismatch")
        result={
          "schema":"structural.ebird_sed_acquisition_handoff_result.v1_157",
          "status":"OFFICIAL_SED_RESPONSE_INDEPENDENT_SUPPORT_SURFACE_READY",
          "candidate_id":c["candidate_id"],
          "sed_sha256":sed_sha0,
          "island_geometry_sha256":geom_sha,
          "support_chain_receipt_sha256":sha256(chain_path),
          "survey_surface_sha256":chain["survey_surface_sha256"],
          "surveyed_island_years":chain["surveyed_island_years"],
          "distinct_surveyed_islands":chain["distinct_surveyed_islands"],
          "species_response_opened":False,
          "source_loss_events_constructed":False,
          "response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False,
          "next_gate":c["next_gate"]
        };code=0
    except Exception as e:
        if isinstance(e,(KeyboardInterrupt,SystemExit)): raise
        result={
          "schema":"structural.ebird_sed_acquisition_handoff_result.v1_157",
          "status":"STOP","reason":str(e),
          "species_response_opened":False,
          "source_loss_events_constructed":False,
          "response_access_authorized":False,
          "counts_as_empirical_source_loss_evidence":False
        };code=2
    p=out/"ebird_sed_handoff_receipt.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
