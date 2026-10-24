"""Pico previously-consumed S1 taxa: recurrence on identical source GPS proxy, synthetic data only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_Pico_spatial_positive_recurrence_v1_276 import (
    aggregate_positive_site_year, gps_round_site_key)


def record(name,year,lat,lon):
    return {"name":name,"year":year,"lat":lat,"lon":lon,
            "uncertainty_m":100}


def sample():
    return [
        record("alpha alba",2020,38.471234,-28.341234),
        record("alpha alba",2021,38.471234,-28.341234),
        record("alpha alba",2021,38.471234,-28.341234), # repeat rows do not become years
        record("beta beta",2020,38.500012,-28.411112),
        record("beta beta",2021,38.500032,-28.411132), # GPS4 overlap, GPS5 difference
        record("gamma gamma",2020,38.500012,-28.411112),
        record("gamma gamma",2021,38.700012,-28.511112),
        record("delta delta",2021,38.65001,-28.33001)
    ]


def test_case_taxon_island_year_counts_separate_from_same_site_recurring():
    result=aggregate_positive_site_year(sample(),{"alpha alba","beta beta","gamma gamma","delta delta","never found"})
    assert result["fixed_S1_loss_taxa"]==5
    assert result["Pico_taxa_seen_in_2plus_distinct_years"]==3
    assert result["Pico_taxa_seen_in_only_one_year"]==1
    assert result["Pico_positive_taxon_year_pairs"]==7
    assert result["GPS5_S1_taxa_positive_at_same_site_in_2plus_years"]==1
    assert result["GPS4_S1_taxa_positive_at_same_site_in_2plus_years"]==2
    assert result["GPS5_S1_taxon_site_proxies_repeated_in_2plus_years"]==1
    assert result["record_missing_never_called_absent"] is True
    assert not any(name in str(result) for name in ("alpha alba","beta beta","gamma gamma"))


def test_identical_source_coords_required_for_primary_one_meter_proxy():
    assert gps_round_site_key(38.471234,-28.341234,5)==gps_round_site_key(38.471232,-28.341234,5)
    assert gps_round_site_key(38.471234,-28.341234,5)!=gps_round_site_key(38.471244,-28.341234,5)


def test_invalid_coordinates_fail_closed_not_pseudo_same_location():
    data=[record("alpha",2020,None,-28.3),record("alpha",2021,38.4,None)]
    r=aggregate_positive_site_year(data,{"alpha"})
    assert r["GPS5_S1_taxa_positive_at_same_site_in_2plus_years"]==0
    assert r["S1_field_records_with_missing_geocoordinates"]==2


def test_no_spurious_same_site_across_different_years_when_only_one_year_positive():
    data=[record("same",2020,38.45,-28.45),
          record("same",2020,38.45,-28.45)]
    r=aggregate_positive_site_year(data,{"same"})
    assert r["Pico_taxa_seen_in_2plus_distinct_years"]==0
    assert r["GPS5_S1_taxa_positive_at_same_site_in_2plus_years"]==0


def test_ignore_non_cohort_taxon_and_do_not_disclose_taxon_names():
    r=aggregate_positive_site_year(sample()+[record("not target",2022,38.45,-28.45)],{"alpha alba"})
    assert r["Pico_taxa_positive_any_year"]==1
    assert r["S1_field_positive_rows_after_filtering"]==3
    assert "not target" not in str(r)
