from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "src/structural/boreal_19island_bird_pilot_router.py"

FULL = [
    "BB","BC","BS","BT","CC","CD","CG","DF","DN","DS","EB","EI","EL","FD",
    "HF","HI","HU","IL","IS","JO","KA","KC","KP","KR","LQ","MI","MN","MT",
    "NH","NV","NW","OS","PP","PR","QC","SF","SG","SK","SR","TB","WD","WF"
]
PILOT = ["DN","FD","HU","IL","IS","PP"]
CONFIRM = ["BB","BT","DF","EB","HF","MI","NH","OS","PR","SF","SK","WD","WF"]


def load_module():
    spec = importlib.util.spec_from_file_location("bird_router", ROUTER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def matrix(confirmatory_payload=b"SECRET"):
    species = [f"sp{i:02d}" for i in range(54)]
    lines = [b"Island," + b",".join(x.encode() for x in species)]
    for island in FULL:
        if island in PILOT:
            # First 20 species have supports cycling 1..4 across the six pilot islands.
            values = []
            pos = PILOT.index(island)
            for j in range(54):
                if j < 20:
                    support = (j % 4) + 1
                    values.append(b"1" if pos < support else b"0")
                else:
                    values.append(b"0")
            row = island.encode() + b"," + b",".join(values)
        else:
            # These bytes deliberately are not valid 0/1 values. Success proves
            # confirmatory/excluded occurrence cells were never decoded.
            row = island.encode() + b"," + b",".join(
                [confirmatory_payload] * 54
            )
        lines.append(row)
    return b"\n".join(lines) + b"\n"


def test_router_reads_only_six_pilot_islands():
    module = load_module()
    routed = module.route_bird_pilot(
        response_csv_bytes=matrix(),
        full_expected_islands=FULL,
        pilot_islands=PILOT,
        confirmatory_islands=CONFIRM,
        expected_species_count=54,
        min_support=1,
        max_support=4,
        minimum_eligible_species=12,
    )
    assert routed.source_response_rows_seen == 42
    assert routed.routing_island_fields_decoded == 42
    assert routed.pilot_island_rows_semantically_parsed == 6
    assert routed.pilot_target_values_parsed == 324
    assert routed.confirmatory_target_values_parsed == 0
    assert routed.excluded_target_values_parsed == 0
    assert routed.eligible_species_count == 20
    assert routed.confirmatory_occurrence_values_stored is False
    assert routed.excluded_occurrence_values_stored is False


def test_router_stops_if_too_few_eligible_species():
    module = load_module()
    try:
        module.route_bird_pilot(
            response_csv_bytes=matrix(),
            full_expected_islands=FULL,
            pilot_islands=PILOT,
            confirmatory_islands=CONFIRM,
            expected_species_count=54,
            min_support=1,
            max_support=4,
            minimum_eligible_species=30,
        )
    except module.Boreal19BirdPilotRouterError as exc:
        assert "eligible bird species gate failed" in str(exc)
    else:
        raise AssertionError("pilot should have stopped")


def test_contract_does_not_authorize_execution():
    import json
    x = json.loads(
        (
            ROOT / "development/boreal_19island_birds_pilot_contract_v1_159.json"
        ).read_text()
    )
    assert x["execution_authorized_now"] is False
    assert x["semantic_access"]["required_confirmatory_target_values_parsed"] == 0
    assert x["semantic_access"]["required_excluded_target_values_parsed"] == 0
    assert x["eligibility_gate"]["pilot_support_min"] == 1
    assert x["eligibility_gate"]["pilot_support_max"] == 4
