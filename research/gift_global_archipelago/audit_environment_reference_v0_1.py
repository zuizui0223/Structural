#!/usr/bin/env python3
"""Audit candidate GIFT climate raster layers without opening species composition."""
from __future__ import annotations
import json
from metadata_census_v0_1 import VERSION, fetch, s

TOKENS = ("bio", "bioclim", "worldclim", "chelsa", "temperature", "precipitation")
TARGET_NUMBERS = ("01", "05", "06", "12", "15")

def main() -> int:
    if VERSION != "3.2":
        raise RuntimeError(f"environment audit frozen for GIFT 3.2, got {VERSION}")
    rows, meta = fetch("env_raster")
    candidates=[]
    for row in rows:
        text=" ".join(
            s(row.get(k)) for k in ("dataset","layer_name","layer","description","version")
        ).lower()
        if not any(tok in text for tok in TOKENS):
            continue
        if any(
            marker in s(row.get("layer_name")).lower()
            for marker in (
                "_01","_05","_06","_12","_15",
                "bio1","bio5","bio6","bio12","bio15"
            )
        ):
            candidates.append(row)
    payload={
        "schema":"structural.gift_environment_reference_metadata_audit.v0_1",
        "status":"response_blind_metadata_only",
        "gift_version":VERSION,
        "species_composition_accessed":False,
        "source":meta,
        "candidate_layers":candidates,
    }
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
