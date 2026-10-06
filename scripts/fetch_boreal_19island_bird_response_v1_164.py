#!/usr/bin/env python3
"""Fetch the exact authorized boreal bird response as opaque bytes."""
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
from urllib.request import Request,build_opener
from scripts.fetch_boreal_mixed_files_v0_72 import StripAuthorizationOnCrossOriginRedirect

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_AUTH=ROOT/"development/boreal_19island_bird_pilot_authorization_v1_163.json"

class Stop(RuntimeError): pass

def load(path):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop("authorization must be object")
    return x

def canonical_sha256(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def validate(auth):
    if auth.get("schema")!="structural.boreal_19island_bird_pilot_authorization.v1_163": raise Stop("authorization schema drift")
    if auth.get("status")!="AUTHORIZED_ONE_SHOT_BIRD_PILOT_ONLY": raise Stop("authorization status drift")
    core=dict(auth); fp=core.pop("authorization_fingerprint",None)
    if fp!=canonical_sha256(core): raise Stop("authorization fingerprint mismatch")
    if auth.get("authorization_consumed") is not False: raise Stop("authorization already consumed")
    if auth.get("pilot_response_authorized") is not True: raise Stop("pilot not authorized")
    if auth.get("confirmatory_response_authorized") is not False: raise Stop("confirmatory ceiling violated")
    return auth["response_file"]

def fetch(auth,dest:Path,token=None,opener=None):
    target=validate(auth)
    token=os.environ.get("DRYAD_TOKEN","") if token is None else token
    if not token or "\n" in token or "\r" in token: raise Stop("DRYAD_TOKEN missing or malformed")
    dest.parent.mkdir(parents=True,exist_ok=True)
    part=dest.with_name("."+dest.name+".part")
    if dest.exists() or part.exists(): raise Stop("refusing overwrite")
    req=Request(target["download_url"],headers={
      "Authorization":f"Bearer {token}","Accept":"application/octet-stream","User-Agent":"Structural-bird-v1.164"})
    opener=opener or build_opener(StripAuthorizationOnCrossOriginRedirect())
    h=hashlib.sha256(); n=0
    try:
        with opener.open(req,timeout=120) as response,part.open("wb") as out:
            while True:
                chunk=response.read(1024*1024)
                if not chunk: break
                out.write(chunk);h.update(chunk);n+=len(chunk)
    except Exception as exc:
        if part.exists(): part.unlink()
        raise Stop(f"transport failed: {type(exc).__name__}") from None
    if n!=target["size_bytes"] or h.hexdigest()!=target["sha256"]:
        if part.exists(): part.unlink()
        raise Stop("exact-byte verification failed")
    os.replace(part,dest)
    return {
      "schema":"structural.boreal_19island_bird_response_transport.v1_164",
      "status":"EXACT_BIRD_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
      "candidate_id":auth["candidate_id"],
      "response_file":{"name":target["name"],"dryad_file_id":target["dryad_file_id"],"size_bytes":n,"sha256":h.hexdigest()},
      "response_semantics_opened":False,"authorization_consumed":False,
      "pilot_response_authorized":True,"confirmatory_response_authorized":False,
      "counts_as_empirical_evidence":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("destination",type=Path);p.add_argument("--authorization",type=Path,default=DEFAULT_AUTH);p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    try: result=fetch(load(a.authorization),a.destination);code=0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,Stop) as e:
        result={"schema":"structural.boreal_19island_bird_response_transport.v1_164","status":"STOP_PRE_ACCESS","reason":str(e),"response_semantics_opened":False,"authorization_consumed":False,"pilot_response_authorized":False,"confirmatory_response_authorized":False,"counts_as_empirical_evidence":False};code=2
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.receipt:a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(text,encoding="utf-8")
    print(text,end="");return code
if __name__=="__main__": raise SystemExit(main())
