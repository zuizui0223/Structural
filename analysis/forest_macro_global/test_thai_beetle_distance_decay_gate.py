"""Known-truth horizontal niche distance support and actual study grain tests."""
import importlib.util,json
from pathlib import Path

script=Path(__file__).with_name("thai_beetle_distance_decay_gate.py")
spec=importlib.util.spec_from_file_location("thai_beetle_h2_support",script)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def bins(xs=(100,200,300,400),ys=(.2,.4,.6,.8)):
    return [{"median_horizontal_distance_m":x,
             "mean_family_relative_BrayCurtis":y} for x,y in zip(xs,ys)]


def test_interpolation_only_within_real_measured_distance_support():
    q=m.distance_gate(.5,bins())
    assert q["status"]=="DESCRIPTIVE_WITHIN_OBSERVED_DISTANCE_SUPPORT"
    assert abs(q["interpolated_horizontal_equivalent_m_NOT_vertical_travel_distance"]-250)<1e-12
    assert q["vertical_target_within_observed_horizontal_quartile_beta_range"]
    assert q["horizontal_quartiles_monotonic_nondecreasing"]


def test_outside_support_and_nonmonotonic_cannot_generate_a_distance():
    outside=m.distance_gate(.9,bins())
    assert outside["status"]=="VERTICAL_BETA_OUTSIDE_HORIZONTAL_SUPPORT"
    assert outside["interpolated_horizontal_equivalent_m_NOT_vertical_travel_distance"] is None
    wrong=m.distance_gate(.5,bins(ys=(.25,.61,.50,.75)))
    assert wrong["status"]=="NO_MONOTONIC_HORIZONTAL_DISTANCE_DECAY"
    assert wrong["interpolated_horizontal_equivalent_m_NOT_vertical_travel_distance"] is None
    flat=m.distance_gate(.51,bins(ys=(.50,.51,.52,.53)))
    assert flat["status"]=="HORIZONTAL_BETA_RANGE_TOO_SMALL"
    duplicate=m.distance_gate(.50,bins(xs=(100,100,200,300)))
    assert duplicate["status"]=="DUPLICATE_OR_NONINCREASING_DISTANCE_QUARTILE"


def test_distance_quartile_ranges_and_slope():
    pairs=[(i*10.0,0.2+0.001*i) for i in range(40)]
    q=m.quarter_bins(pairs)
    assert len(q)==4
    assert all(x["horizontal_pair_comparisons_nonindependent"]==10 for x in q)
    assert abs(m._slope_per100m(pairs)-0.01)<1e-12


def source_synthetic():
    events=[]
    occs=[]
    for forest,baselat in (("SourceForestX",15.0),("SourceForestY",16.0)):
        for i in range(9):
            lat=baselat+(i//3)*0.004
            lon=101+(i%3)*0.004
            for when in ("2019-06-01","2019-12-01"):
                for layer in ("canopy","understory"):
                    for jar in ("top","bottom"):
                        eid=f"secret-{len(events)}"
                        events.append({
                          "_core_id":eid,"eventID":eid,"locationID":forest,
                          "samplingProtocol":f"SLAM Trap ({layer} {jar} jar)",
                          "decimalLatitude":str(lat+(0.00012 if layer=="canopy" else 0)),
                          "decimalLongitude":str(lon),"eventDate":when,
                          "sampleSizeValue":"10","sampleSizeUnit":"days","samplingEffort":"10 days"
                        })
                        family="Curculionidae" if i%2 else "Cerambycidae"
                        if layer=="understory" and i%3==0:family="Staphylinidae"
                        occs.append({"_core_id":eid,"family":family,
                                     "individualCount":"1","taxonRank":"genus"})
    occs[0]["individualCount"]=str(1622-len(occs)+1)
    return events,occs


def test_reports_four_eligible_forest_campaign_units_with_no_pseudoreplication():
    e,o=source_synthetic()
    x=m.analyze(e,o)
    assert x["forest_count"]==2
    assert x["physical_station_pairs"]==18
    assert x["source_beetle_individuals"]==1622
    assert len(x["forest_campaign_results"])==4
    assert x["no_raw_coordinates_eventIDs_taxa_exported"] is True
    assert x["no_causal_mechanism_or_global_generalization_estimated"] is True
    assert x["pairs_are_nonindependent_within_2_original_forests"]
    data=json.dumps(x)
    assert "SourceForestX" not in data and "secret-" not in data
    assert "Curculionidae" not in data
    assert all(row["horizontal_within_layer_pairwise_BC_n_nonindependent"]==72
               for row in x["forest_campaign_results"])
    assert all(row["vertical_paired_station_BC_n"]==9
               for row in x["forest_campaign_results"])
