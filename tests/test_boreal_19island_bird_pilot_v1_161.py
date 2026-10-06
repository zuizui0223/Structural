from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
ROUTER=ROOT/"src/structural/boreal_19island_bird_pilot_router_v1_161.py"
EXEC=ROOT/"scripts/run_boreal_19island_bird_pilot_v1_161.py"
CONTRACT=ROOT/"development/boreal_19island_birds_pilot_contract_v1_161.json"
UNIVERSE=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
FULL=["BB","BC","BS","BT","CC","CD","CG","DF","DN","DS","EB","EI","EL","FD","HF","HI","HU","IL","IS","JO","KA","KC","KP","KR","LQ","MI","MN","MT","NH","NV","NW","OS","PP","PR","QC","SF","SG","SK","SR","TB","WD","WF"]
PILOT=["DN","FD","HU","IL","IS","PP"]

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def matrix():
    species=[f"sp{i:02d}" for i in range(54)]
    lines=[b"Islands,"+b",".join(s.encode() for s in species)]
    for island in FULL:
        if island in PILOT:
            pos=PILOT.index(island);vals=[]
            for j in range(54):
                if j<20:
                    support=(j%4)+1;vals.append(b"1" if pos<support else b"0")
                else: vals.append(b"0")
        else:
            vals=[b"SECRET"]*54
        lines.append(island.encode()+b","+b",".join(vals))
    return b"\n".join(lines)+b"\n"

def test_v161_normalizes_only_known_routing_header():
    m=load(ROUTER,"bird_router_v161")
    raw=matrix()
    normalized=m.normalize_routing_header_only(raw)
    assert normalized.startswith(b"Island,")
    assert b"SECRET" in normalized

def test_v161_executor_passes_synthetic_without_confirmatory_decode():
    m=load(EXEC,"bird_exec_v161")
    raw=matrix()
    c=json.loads(CONTRACT.read_text())
    c["response_file"]["expected_size_bytes"]=len(raw)
    c["response_file"]["expected_sha256"]=hashlib.sha256(raw).hexdigest()
    result,snapshot=m.execute(raw,contract=c,universe=json.loads(UNIVERSE.read_text()))
    assert result["status"]=="BIRD_PILOT_V161_QUALIFIED_TO_FREEZE_CONFIRMATORY_PREDICTIONS"
    assert result["eligible_species_count"]==20
    assert result["pilot_target_values_parsed"]==324
    assert result["confirmatory_target_values_parsed"]==0
    assert result["excluded_target_values_parsed"]==0
    assert snapshot["confirmatory_occurrence_values_stored"] is False
    assert snapshot["excluded_occurrence_values_stored"] is False

def test_scientific_rules_unchanged_from_v158():
    c=json.loads(CONTRACT.read_text())
    assert c["eligibility_gate"]=={
        "pilot_support_min":1,
        "pilot_support_max":4,
        "minimum_eligible_species":12,
        "changed_after_v1_160":False
    }
    assert c["evidence_class"]["species_identity_exposed"] is False
    assert c["evidence_class"]["pilot_occurrence_values_exposed"] is False
