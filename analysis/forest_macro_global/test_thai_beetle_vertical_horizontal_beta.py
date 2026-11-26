"""Known truth for vertical vs horizontal family distance, 2 forests not 288 forests."""
import importlib.util
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_vertical_horizontal_beta.py")
spec=importlib.util.spec_from_file_location("thai_beta_axes",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def original_fixture(between_layers=True):
    events=[];occ=[]
    for f,base in (("forest1",12),("forest2",14)):
        for i in range(9):
            y=base+(i//3)*0.01
            x=101+(i%3)*0.01
            for day in ("2019-06-01","2019-12-01"):
                for layer in ("canopy","understory"):
                    for jar in ("top","bottom"):
                        k=f"event_{len(events)}"
                        e={"_core_id":k,"eventID":k,
                           "locationID":f,"samplingProtocol":f"SLAM trap ({layer} {jar} jar)",
                           "decimalLatitude":str(y+(0.0001 if layer=="canopy" else 0)),
                           "decimalLongitude":str(x),"eventDate":day,
                           "sampleSizeValue":"10","sampleSizeUnit":"days","samplingEffort":"10 days"}
                        events.append(e)
                        kfamily=("Curculionidae" if i%3==0 else "Cerambycidae")
                        if between_layers and layer=="understory":
                            kfamily=("Staphylinidae" if i%3==0 else "Throscidae")
                        occ.append({"_core_id":k,"individualCount":"1",
                                    "family":kfamily,"taxonRank":"family"})
    # total 1622 guaranteed, but every site-layer holds only one family
    occ[0]["individualCount"]=str(1+1622-len(occ))
    return events,occ

def test_vertical_strata_can_be_stronger_than_horizontal_separation():
    e,o=original_fixture(True)
    r=m.compare(e,o)
    assert r["source_original_SLAM_jar_events"]==144
    assert r["source_beetle_individual_count"]==1622
    assert r["original_physical_station_pair_n"]==18
    assert r["pooled_vertical_within_station_family_BrayCurtis_mean"]==1
    assert abs(r["pooled_horizontal_within_stratum_family_BrayCurtis_mean"]-0.5)<1e-10
    assert r["forest_campaign_direction_count_vertical_greater_than_horizontal"]==4
    assert r["horizontal_comparisons_n_NOT_independent"]==288
    assert r["vertical_comparisons_n"]==36
    assert r["not_abundance_corrected_to_equal_individual_coverage"]

def test_vertical_strata_can_be_less_different_than_horizontally_distributed_sites():
    e,o=original_fixture(False)
    r=m.compare(e,o)
    assert r["pooled_vertical_within_station_family_BrayCurtis_mean"]==0
    assert r["pooled_horizontal_within_stratum_family_BrayCurtis_mean"]>0
    assert r["forest_campaign_direction_count_vertical_greater_than_horizontal"]==0

def test_sample_source_effort_mismatch_fails_closed():
    e,o=original_fixture(True)
    e[0]["sampleSizeValue"]="3"
    try:
        m.compare(e,o)
        assert False
    except ValueError as exc:
        assert "effort" in str(exc)

def test_source_not_288_independent_woods_and_no_species_inference():
    e,o=original_fixture(True)
    r=m.compare(e,o)
    assert r["forest_site_n_not_36_or_288"]==2
    assert not r["new_global_effect_or_mechanistic_claim"]
    assert r["raw_ids_coordinates_and_family_labels_not_exported"]
    assert "Curculionidae" not in str(r)
    assert "forest1" not in str(r)
