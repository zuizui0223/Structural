import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_active_priority_v126_points_to_bala_without_opening_response():
    x=json.loads((ROOT/"development/structural_active_priority_v1_126.json").read_text())
    assert x["preferred_candidate_preintake"].endswith("bala_source_loss_preintake_v1_126.json")
    assert "Event core only" in " ".join(x["do_now"])
    assert any("event-by-taxon" in s for s in x["do_not"])
    assert "confirmatory queue remains empty" in x["next_scientific_event"]
