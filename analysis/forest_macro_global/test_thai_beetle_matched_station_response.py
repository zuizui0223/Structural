"""Known truth 18-site x two-round x canopy/understorey x 2 jars audit."""
import importlib.util
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_matched_station_response.py")
spec=importlib.util.spec_from_file_location("thai_beetle_matched_original",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture(swap=False):
    rows=[];occ=[]
    for forest in ("A","B"):
        for site in range(9):
            lat=14+(0.5 if forest=="B" else 0)+0.001*(site//3)
            lon=101+0.001*(site%3)
            for campaign,day in enumerate(("2019-06-01","2019-12-01")):
                for layer in ("canopy","understory"):
                    for jar in ("top","bottom"):
                        eid="event_"+str(len(rows))
                        rows.append({
                           "_core_id":eid,"eventID":eid,
                           "locationID":forest,
                           "samplingProtocol":f"SLAM Trap ({layer} {jar} jar)",
                           "decimalLatitude":str(lat+(0.0001 if layer=="canopy" else 0)),
                           "decimalLongitude":str(lon),
                           "eventDate":day,
                           "sampleSizeValue":"10",
                           "sampleSizeUnit":"days",
                           "samplingEffort":"10 days",
                        })
                        n=1 if layer=="understory" else 2
                        if swap and forest=="B":n=3-n
                        occ.append({"_core_id":eid,"individualCount":str(n),
                                    "family":"Curculionidae","taxonRank":"family"})
    return rows,occ

def test_exact_sites_not_jars_and_repeated_seasons_before_signflip():
    event,occ=fixture()
    r=m.paired_site_response(event,occ)
    assert r["original_independent_forests"]==2
    assert r["independent_physical_station_pairs_within_forests"]==18
    assert r["complete_pairs_station_x_campaign"]==36
    assert r["actual_original_SLAM_jar_events"]==144
    assert r["station_campaign_layer_trap_deployments"]==72
    assert r["canopy_total_beetles"]==72*2
    assert r["understorey_total_beetles"]==72
    assert r["mean_paired_canopy_minus_understorey_beetles_per_station_per_campaign"]==2
    assert r["site_means_positive_canopy_difference"]==18
    assert r["two_sided_site_signflip_exact_p_CONDITIONAL_ON_TWO_FORESTS"]==2/(2**18)
    assert r["within_forest_stratified_site_bootstrap_95CI_mean_paired_difference"]==[2,2]
    assert not r["not_an_estimate_of_canopy_height_causal_effect"] is False
    assert r["forest_fragment_or_island_source_connectivity_not_tested"] is True

def test_opposite_two_forest_directions_do_not_support_uniform_canopy_gain():
    event,occ=fixture(swap=True)
    r=m.paired_site_response(event,occ)
    assert r["site_means_positive_canopy_difference"]==9
    assert r["site_means_negative_canopy_difference"]==9
    assert r["mean_paired_canopy_minus_understorey_beetles_per_station_per_campaign"]==0
    assert r["two_sided_site_signflip_exact_p_CONDITIONAL_ON_TWO_FORESTS"]==1

def test_unequal_effort_and_ambiguous_pairs_stop():
    event,occ=fixture()
    event[0]["sampleSizeValue"]="2"
    try:
        m.paired_site_response(event,occ)
        assert False
    except ValueError as err:
        assert "unequal_original_SLAM_effort_metadata" in str(err)
    event,occ=fixture()
    event[0]["decimalLatitude"]=str(float(event[0]["decimalLatitude"])+0.01)
    try:
        m.paired_site_response(event,occ)
        assert False
    except ValueError as err:
        assert "nine_station_per_stratum_required" in str(err) or "matching" in str(err)
