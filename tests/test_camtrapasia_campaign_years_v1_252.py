import json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v252",R/"scripts/camtrapasia_campaign_years_v1_252.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_study_interval_not_persistent_population():
    assert m.parse_year("2017")==2017
    assert m.parse_year("2017.0") is None
    assert m.parse_year("") is None
    c=json.loads((R/"development/camtrapasia_campaign_year_contract_v1_252.json").read_text())
    assert c["predeclared_campaign_rules"]["threshold_year_for_IUCN_vintage"]==2017
    assert c["ecological_limits"]["separated_campaigns_do_not_demonstrate_continuous_population_persistence"] is True
    assert all(v is False for v in c["safeguards"].values())
def test_repeated_taxa_7_equal_prior_frozen_taxa():
    p=json.loads((R/"development/camtrapasia_cross_island_photo_replicability_freeze_v1_251.json").read_text())
    assert set(p["replicated_each_island_two_plus_survey_IDs_and_all_non_domestic_records"])==m.STRICT7
    assert len(m.STRICT7)==7
