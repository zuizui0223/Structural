"""v1.346 source-free seven-island uncertainty & scientific claim guard."""
import copy,json,math,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_jbi_island_unit_uncertainty_sourcefree_v1_346 import (
   analyze_uncertainty, island_unit_summary, T6_975
)

def read():
    def get(name):return json.loads((ROOT/"development"/name).read_text(encoding="utf-8"))
    return (get("bala_within_campaign_detection_original_result_freeze_v1_316.json"),
            get("bala_spatial_original_result_freeze_v1_318.json"),
            get("bala_temporal_spatial_cross_axis_sourcefree_protocol_v1_344.json"),
            get("bala_jbi_island_unit_uncertainty_protocol_v1_346.json"))

def test_scientifically_valid_island_level_uncertainty_no_full_archipelago_significance():
    v316,v318,old,p=read()
    out=analyze_uncertainty(v316,v318,old,p)
    assert out["status"]=="SOURCE_FREE_ISLAND_UNIT_UNCERTAINTY_RECONCILED_NOT_CONFIRMATORY"
    b=out["guilds"]["coleoptera"]["within_island_spatial_simpson_B3_minus_B1"]
    a=out["guilds"]["araneae"]["within_island_spatial_simpson_B3_minus_B1"]
    assert out["island_sample_n"]==7
    assert math.isclose(T6_975,2.4469118511449692,rel_tol=0,abs_tol=1e-14)
    assert math.isclose(b["island_equal_mean"],-.17530148423005568,abs_tol=1e-12)
    assert math.isclose(a["island_equal_mean"],.02240713745815786,abs_tol=1e-12)
    assert b["source_islands_negative"]==4 and b["source_islands_positive"]==3
    assert b["descriptive_t95_interval_conditional_on_seven_islands"][0]<-.439
    assert .089 < b["descriptive_t95_interval_conditional_on_seven_islands"][1] < .090
    assert b["t95_interval_includes_zero"] and a["t95_interval_includes_zero"]
    assert b["symmetric_sign_flip_null_permutations"]==128
    assert b["symmetric_sign_flip_two_sided_tail_count"]==24
    assert math.isclose(b["symmetric_sign_flip_two_sided_p_exploratory"],.1875)
    assert math.isclose(a["symmetric_sign_flip_two_sided_p_exploratory"],.6875)
    assert out["beetle_original_mean_still_negative_under_all_seven_LOO"]
    assert out["beetle_original_18_half_salts_still_negative"]
    assert out["beetle_island_level_spatial_interval_includes_zero"]
    assert out["no_independent_taxon_guild_interaction_demonstrated"]

def test_temporal_half_sample_excess_more_consistent_but_still_observation_based():
    v316,v318,old,p=read()
    out=analyze_uncertainty(v316,v318,old,p)
    for guild in ("araneae","coleoptera"):
        q=out["guilds"][guild]["temporal_species_identity_excess_sorensen"]
        assert q["source_islands_positive"]==7 and q["source_islands_negative"]==0
        assert not q["t95_interval_includes_zero"]
        assert q["symmetric_sign_flip_null_permutations"]==128
        assert q["symmetric_sign_flip_two_sided_tail_count"]==2
        assert math.isclose(q["symmetric_sign_flip_two_sided_p_exploratory"],.015625)
        assert q["descriptive_t95_interval_conditional_on_seven_islands"][0]>0
    b=out["guilds"]["coleoptera"]["temporal_species_identity_excess_sorensen"]
    assert math.isclose(b["island_equal_mean"],.22120879931840728,abs_tol=1e-12)

def test_guild_difference_paired_at_island_level_not_demonstrated():
    v316,v318,old,p=read()
    out=analyze_uncertainty(v316,v318,old,p)
    d=out["paired_beetle_minus_spider_spatial_simpson_delta"]
    assert math.isclose(d["island_equal_mean"],-.19770862168821354,abs_tol=1e-12)
    assert d["t95_interval_includes_zero"]
    lo,hi=d["descriptive_t95_interval_conditional_on_seven_islands"]
    assert -.498<lo<-.496 and .100<hi<.103
    assert d["symmetric_sign_flip_two_sided_tail_count"]==22
    assert math.isclose(d["symmetric_sign_flip_two_sided_p_exploratory"],.171875)
    assert out["paired_guild_island_level_interval_includes_zero"]

def test_all_sign_flip_null_invariant_under_source_island_order_and_effect_flip():
    x=[.17777777777777776,-.5603174603174603,.09722222222222221,
       -.4166666666666667,.004960317460317443,-.40151515151515155,-.12857142857142856]
    q=island_unit_summary(x)
    for other in (list(reversed(x)),[-v for v in x]):
        w=island_unit_summary(other)
        assert math.isclose(w["symmetric_sign_flip_two_sided_p_exploratory"],
                            q["symmetric_sign_flip_two_sided_p_exploratory"],abs_tol=1e-15)
        assert w["t95_interval_includes_zero"]==q["t95_interval_includes_zero"]
    with pytest.raises(ValueError,match="seven finite source island values"):
        island_unit_summary(x[:6])
    with pytest.raises(ValueError,match="seven finite source island values"):
        island_unit_summary(x[:6]+[float("nan")])

def test_immutable_archive_seal_and_no_event_species_or_pseudo_independent_island_replication():
    v316,v318,old,p=read()
    q=analyze_uncertainty(v316,v318,old,p)
    assert q["no_new_original_event_occurrence_or_species_rows_opened"]
    assert q["original_v314_v316_v318_scorers_SEALED"]
    assert q["n7_islands_from_one_archipelago_only"]
    assert q["retrospective_exploratory_sign_flip_not_a_prespecified_significance_test"]
    assert q["source_field_species_colonization_or_extinction_not_measured"]
    assert q["GEB_scientific_HOLD"] and q["new_confirmatory_systems"]==0 and not q["eBird_used"]
    assert "scientificName" not in json.dumps(q)
    bad=copy.deepcopy(v318);bad["original_evidence"]["original_result_JSON_SHA256"]="wrong"
    with pytest.raises(ValueError,match="original source SHA|source field data identity"):
        analyze_uncertainty(v316,bad,old,p)
    bad=copy.deepcopy(p);bad["source"]["original_independent_islands"]=49
    with pytest.raises(ValueError,match="not frozen"):
        analyze_uncertainty(v316,v318,old,bad)
