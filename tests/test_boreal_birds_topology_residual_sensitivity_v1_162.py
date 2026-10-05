from __future__ import annotations
import csv,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_birds_topology_residual_sensitivity_v1_162.py"
DESIGN=ROOT/"development/boreal_birds_topology_residual_preintake_v1_162.json"
GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"
def mod():
    s=importlib.util.spec_from_file_location("b162",SCRIPT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def test_response_free_topology_residual_surface_is_estimable():
    surface,receipt=mod().freeze(DESIGN,GEOMETRY)
    rows=list(csv.DictReader(surface.splitlines()));r=json.loads(receipt)
    assert len(rows)==78
    assert {int(x["n"]) for x in rows}=={1,2,3,4,5,6}
    assert r["target_count"]==13
    assert r["H_topo_unique_count"]>1
    assert float.fromhex(r["H_topo_min_hex"])<0.01
    assert float.fromhex(r["H_topo_max_hex"])>2.0
    assert r["bird_file_opened"] is False
    assert r["bird_response_values_opened"]==0
