#!/usr/bin/env python3
"""Pre-access binary prediction header inspection; no ecological labels opened."""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path

ACTUAL=b"STRUCTURAL_MAMMAL_ULTRARARE_PRED_V1\n"
NULL=b"STRUCTURAL_MAMMAL_ULTRARARE_NULL_PRED_V1\n"
H={
  "actual":"3307a2e058f5f8223eaf0c2d69241acd938e96b93cb02643b1b7d63b425fae04",
  "null":"300f0001d250dde01bc0240be3d20898399300fcac5f405e76bfd0f8524495c3"
}
class Stop(ValueError): pass

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def inspect(path,magic,header_dims,payload_shape,expected_sha=None):
    with path.open("rb") as f:
        if f.read(len(magic))!=magic:raise Stop("prediction magic drift")
        got=struct.unpack("<"+"I"*len(header_dims),f.read(4*len(header_dims)))
    if tuple(got)!=tuple(header_dims):raise Stop("prediction header dimensions drift")
    required=len(magic)+len(header_dims)*4+8*mathprod(payload_shape)
    if path.stat().st_size!=required:raise Stop("prediction binary payload size drift")
    if expected_sha is not None and sha(path)!=expected_sha:raise Stop("prediction SHA drift")
    return {"header_dims":list(got),"payload_shape":list(payload_shape),"bytes":required,
            "sha256":sha(path) if expected_sha is None else expected_sha}

def mathprod(seq):
    v=1
    for x in seq:v*=int(x)
    return v

def main():
    p=argparse.ArgumentParser()
    p.add_argument("actual",type=Path)
    p.add_argument("null",type=Path)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        v=inspect(a.actual,ACTUAL,(4126,529),(4126,529,2),H["actual"])
        w=inspect(a.null,NULL,(20,4126,529),(20,4126,529),H["null"])
        out={"schema":"structural.global_mammals_prediction_header_preflight.v1_195",
             "status":"FROZEN_BINARY_HEADERS_VALIDATED_BEFORE_ANY_EXTERNAL_OUTCOME",
             "actual":v,"null":w,"external_ala_pairs_opened_during_preflight":0,
             "original_mammal_heldout_labels_read":0,"score_computed":False,
             "v1_194_rerun_authorized":False,"eBird_used":False}
        code=0
    except (Stop,OSError,struct.error,ValueError) as e:
        out={"schema":"structural.global_mammals_prediction_header_preflight.v1_195",
             "status":"STOP_PREDICTION_HEADER_PREFLIGHT","reason":str(e),
             "external_ala_pairs_opened_during_preflight":0,
             "original_mammal_heldout_labels_read":0,"score_computed":False,
             "v1_194_rerun_authorized":False,"eBird_used":False}
        code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
