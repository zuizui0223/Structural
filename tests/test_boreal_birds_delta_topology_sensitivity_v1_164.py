from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_birds_delta_topology_sensitivity_v1_164.py"
DESIGN=ROOT/"development/boreal_birds_delta_topology_preintake_v1_164.json"

def module():
    spec=importlib.util.spec_from_file_location("birddelta164",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_delta_topology_surface_is_exact_and_response_free():
    surface,receipt=module().freeze(DESIGN)
    rows=list(csv.DictReader(surface.splitlines()))
    r=json.loads(receipt)
    assert len(rows)==78
    assert {int(x["n"]) for x in rows}=={1,2,3,4,5,6}
    assert r["surface_sha256"]=="d62e76e3addeba6af3ab47638386214c6d2c854e6dbda4003d7f74dc4f9feb3a"
    assert r["targets_with_delta_H_positive"]==10
    assert r["delta_H_min_hex"]=="-0x1.ca731328d2bb2p-4"
    assert r["delta_H_max_hex"]=="0x1.f38c6960b55ebp+0"
    assert r["bird_file_opened"] is False
    assert r["bird_header_opened"] is False
    assert r["bird_response_values_opened"]==0
    assert r["pilot_response_authorized"] is False
    assert r["confirmatory_response_authorized"] is False

def test_delta_topology_primary_is_signed_actual_minus_null():
    d=json.loads(DESIGN.read_text())
    assert "H_actual_i - mean_k(H_null_k_i)" in d["actual_minus_null_moderator"]["delta_H_i"]
    assert d["primary_scoring"]["favourable_direction"]=="negative"
    assert d["primary_scoring"]["all_cell_fallback_authorized"] is False
