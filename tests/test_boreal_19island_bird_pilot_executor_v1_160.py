from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "scripts/run_boreal_19island_bird_pilot_v1_160.py"
CONTRACT = ROOT / "development/boreal_19island_birds_pilot_contract_v1_159.json"
UNIVERSE = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"

FULL = [
    "BB","BC","BS","BT","CC","CD","CG","DF","DN","DS","EB","EI","EL","FD",
    "HF","HI","HU","IL","IS","JO","KA","KC","KP","KR","LQ","MI","MN","MT",
    "NH","NV","NW","OS","PP","PR","QC","SF","SG","SK","SR","TB","WD","WF"
]
PILOT = ["DN","FD","HU","IL","IS","PP"]


def load_module():
    spec = importlib.util.spec_from_file_location("bird_exec_v160", EXECUTOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def synthetic_matrix():
    species = [f"sp{i:02d}" for i in range(54)]
    lines = [b"Island," + b",".join(x.encode() for x in species)]
    for island in FULL:
        if island in PILOT:
            pos = PILOT.index(island)
            vals = []
            for j in range(54):
                if j < 20:
                    support = (j % 4) + 1
                    vals.append(b"1" if pos < support else b"0")
                else:
                    vals.append(b"0")
        else:
            vals = [b"SECRET"] * 54
        lines.append(island.encode() + b"," + b",".join(vals))
    return b"\n".join(lines) + b"\n"


def test_executor_passes_without_decoding_confirmatory_cells():
    module = load_module()
    raw = synthetic_matrix()
    contract = json.loads(CONTRACT.read_text())
    contract["response_file"]["expected_size_bytes"] = len(raw)
    contract["response_file"]["expected_sha256"] = hashlib.sha256(raw).hexdigest()
    result, snapshot = module.execute(
        raw,
        contract=contract,
        universe=json.loads(UNIVERSE.read_text()),
    )
    assert result["status"] == "BIRD_PILOT_QUALIFIED_TO_FREEZE_CONFIRMATORY_PREDICTIONS"
    assert result["pilot_target_values_parsed"] == 324
    assert result["eligible_species_count"] == 20
    assert result["confirmatory_target_values_parsed"] == 0
    assert result["excluded_target_values_parsed"] == 0
    assert snapshot is not None
    assert snapshot["confirmatory_occurrence_values_stored"] is False
    assert snapshot["excluded_occurrence_values_stored"] is False
    assert snapshot["confirmatory_response_authorized"] is False
