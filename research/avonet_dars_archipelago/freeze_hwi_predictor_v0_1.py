#!/usr/bin/env python3
"""Freeze AVONET-derived HWI predictor metadata before any DARs bird matrix opens."""
from __future__ import annotations

import csv, hashlib, io, json
from urllib.request import Request, urlopen

REPO="txm676/DARs"
COMMIT="8b381ff26e3d6f4da17730dda0c5ab7dbad12eed"
PATH="Data/Species_datasets/Traits_all_species_PublVer.csv"
URL=f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{PATH}"
EXPECTED_GIT_BLOB_SHA="f6ef8e15c51396706167f5847f138fce8be2b3ce"
EXPECTED_SIZE=2218702

def fetch(url):
    req=Request(url,headers={"User-Agent":"Structural-AVONET-trait-freeze/0.1"})
    with urlopen(req,timeout=180) as r: raw=r.read()
    return raw

def git_blob_sha(raw:bytes)->str:
    head=f"blob {len(raw)}\0".encode()
    return hashlib.sha1(head+raw).hexdigest()

def sha(x)->str:
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def finite_float(x):
    try:
        v=float(x)
        return v if v==v and abs(v)!=float("inf") else None
    except (TypeError,ValueError):
        return None

def main():
    raw=fetch(URL)
    if len(raw)!=EXPECTED_SIZE:
        raise RuntimeError(f"trait bytes drift {len(raw)} != {EXPECTED_SIZE}")
    blob=git_blob_sha(raw)
    if blob!=EXPECTED_GIT_BLOB_SHA:
        raise RuntimeError(f"trait Git blob drift {blob}")
    digest=hashlib.sha256(raw).hexdigest()
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    required=("Species 2","Family 2","Order3","Hand-Wing Index","Mass","Migration")
    missing=[c for c in required if c not in (rows[0].keys() if rows else [])]
    if missing: raise RuntimeError("missing trait columns: "+", ".join(missing))

    names=[]
    hwi=[]
    mass=[]
    migration=[]
    duplicate=0
    seen=set()
    for r in rows:
        name=(r.get("Species 2") or "").strip()
        if not name: continue
        if name in seen: duplicate+=1
        seen.add(name); names.append(name)
        v=finite_float(r.get("Hand-Wing Index"))
        if v is not None: hwi.append(v)
        m=finite_float(r.get("Mass"))
        if m is not None: mass.append(m)
        mig=(r.get("Migration") or "").strip()
        if mig and mig!="NA": migration.append(mig)

    payload={
      "schema":"structural.avonet_dars_trait_predictor.v0_1",
      "status":"PREDICTOR_OPEN_RESPONSE_SEALED",
      "response_values_accessed":False,
      "dars_species_matrices_opened":False,
      "source":{
        "repository":REPO,"commit":COMMIT,"path":PATH,"url":URL,
        "bytes":len(raw),"git_blob_sha":blob,"sha256":digest,
      },
      "columns":{
        "species":"Species 2","family":"Family 2","order":"Order3",
        "HWI":"Hand-Wing Index","mass":"Mass","migration":"Migration",
      },
      "HWI_semantics":"use the published AVONET Hand-Wing Index column directly; higher HWI indicates greater flight/dispersal morphology; no post-response transformation or alternate wing metric",
      "rows":len(rows),
      "unique_species_names":len(seen),
      "duplicate_species_names":duplicate,
      "HWI_nonmissing":len(hwi),
      "HWI_missing":len(rows)-len(hwi),
      "HWI_min":min(hwi),"HWI_max":max(hwi),
      "mass_nonmissing":len(mass),
      "migration_nonmissing":len(migration),
      "species_name_set_sha256":sha(sorted(seen)),
      "trait_values_opened":True,
      "trait_role":"response-independent predictor only",
    }
    payload["trait_fingerprint"]=sha(payload)
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
