"""BALA seven-island original source aggregate consistency tests, no species."""
import copy,json,sys,math
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_7island_sourcefree_replacement_audit_v1_315 import audit

def original():
    return json.loads((ROOT/"development/bala_seven_island_species_replacement_original_result_v1_314.json").read_text())

def test_original_seven_island_observational_replacement_conclusions_are_consistent():
    r=audit(original())
    assert r["status"]=="SOURCE_FREE_ORIGINAL_SEVEN_ISLAND_REPLACEMENT_RECONCILED"
    assert r["source_original_independent_transects"]==29
    assert r["source_longitudinal_island_count"]==7
    assert r["pitfall_observable_transect_guild_B1_B3_comparisons"]==57
    assert r["pitfall_guild_comparisons_with_balanced_replacement_and_at_most_one_species_net_difference"]==23
    assert math.isclose(r["fraction_of_pitfall_guild_comparisons_with_replacement_and_near_stable_richness"],23/57)
    assert r["islands_with_positive_spider_replacement"]==7
    assert r["islands_with_positive_beetle_replacement"]==7
    assert r["islands_with_beetle_mean_simpson_replacement_greater_than_spider_mean"]==6
    assert r["pitfall_island_equal_beetle_sorensen_total"]>r["pitfall_island_equal_spider_sorensen_total"]
    assert r["pitfall_island_equal_beetle_simpson_replacement"]>r["pitfall_island_equal_spider_simpson_replacement"]
    assert r["no_original_Event_or_Occurrence_rows_reopened"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]

def test_corrupted_island_conclusion_or_original_source_hash_is_hard_stop():
    a=original()
    a["pitfall_primary"]["coleoptera"]["per_island_replacement_simpson"]["pic"]=0
    with pytest.raises(ValueError,match="directions"):audit(a)
    a=original()
    a["original_source"]["original_archive_sha256"]="tampered"
    with pytest.raises(ValueError,match="identity"):audit(a)
    a=original()
    a["firewall"]["GEB_scientific_HOLD"]=False
    with pytest.raises(ValueError,match="identity"):audit(a)
