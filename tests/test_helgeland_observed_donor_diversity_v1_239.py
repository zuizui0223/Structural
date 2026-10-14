"""Known-truth counts, no actual bird observations opened in tests."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_observed_donor_diversity_v1_239 import source_stats,source_sharing,EXPECTED_COUNTS

def test_extreme_single_source_concentration():
    x=source_stats({1:9,2:1,3:0})
    assert x["incoming"]==10
    assert x["hill_simpson"]==pytest.approx(100/82)
    assert x["prob_same_source_two_distinct_migrants"]==pytest.approx(72/90)
    assert x["dominant_id"]==1
    assert x["dominant_fraction"]==pytest.approx(.9)

def test_two_balanced_donors_with_sample_correction():
    a=source_stats({1:5,2:5})
    assert a["source_richness"]==2
    assert a["hill_simpson"]==pytest.approx(2)
    assert a["prob_same_source_two_distinct_migrants"]==pytest.approx(40/90)

def test_no_immigrants_is_missing_not_zero_effective_donors():
    a=source_stats({1:0,2:0})
    assert a["incoming"]==0
    assert a["hill_simpson"] is None
    assert a["prob_same_source_two_distinct_migrants"] is None

def test_shared_donor_between_distinct_destinations():
    assert source_sharing({1:2},{1:1,2:1})==pytest.approx(.5)
    assert source_sharing({1:2},{2:3})==pytest.approx(0)
    assert source_sharing({1:0},{2:3}) is None

def test_frozen_three_cohorts():
    assert EXPECTED_COUNTS=={"historical":259,"bridge":28,"later":173}

def test_full_frozen_schema_path_uses_marked_not_renamed_field():
    from helgeland_observed_donor_diversity_v1_239 import compute
    counts={"historical":259,"bridge":28,"later":173}
    roster=list(range(1,12))
    source={"schema":"structural.helgeland_nestling_origin_nextyear_resight_freeze.v1_231",
      "data":{"n_model_islands":11,"source_rows":73593,
      "per_origin":[{"era":era,"origin":i,"island_name":f"island_{i}",
          "marked":count+1 if i==1 else 1,
          "retained":1,"exported":count if i==1 else 0}
          for era,count in counts.items() for i in roster],
      "observed_cross_island_edges":[
          {"era":era,"origin":1,"destination":2,"observed_n":count}
          for era,count in counts.items()]}}
    x=compute(source)
    for era,count in counts.items():
        rows=x["periods"][era]["all_recipient_islands"]
        assert len(rows)==11
        recipient=next(r for r in rows if r["island_id"]==2)
        assert recipient["incoming"]==count
        assert recipient["hill_simpson"]==1
        assert recipient["observed_immigrant_fraction_of_known_nextyear_recruits"]==pytest.approx(count/(count+1))
