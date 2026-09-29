from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_origin_route_uses_only_two_published_tables():
 x=json.loads((ROOT/"development/gift_public_geology_contract_v1_53.json").read_text())
 assert x["public_API"]["allowed_queries"]==["geoentities_geology","geology"]
 assert x["public_API"]["species_or_checklist_query_forbidden"] is True
 assert x["response_boundary"]["GIFT_species_composition_authorized"] is False
def test_origin_recode_keeps_mixed_separate():
 x=json.loads((ROOT/"development/gift_public_geology_contract_v1_53.json").read_text())
 assert "shelf" in x["geology_simple_recode"]["continental"]
 assert "volcanic" in x["geology_simple_recode"]["oceanic"]
 assert "shelf/volcanic" in x["geology_simple_recode"]["mixed"]
 assert x["primary_adjustment"]["mixed"].startswith("separate")
def test_fetcher_contains_no_species_query():
 s=(ROOT/"scripts/fetch_gift_public_geology_v1_53.py").read_text()
 assert 'base+"geoentities_geology"' in s
 assert 'base+"geology"' in s
 assert 'base+"checklists"' not in s\n assert 'base+"species"' not in s
