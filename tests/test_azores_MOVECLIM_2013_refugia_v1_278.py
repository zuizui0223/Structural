"""Synthetic-only 2013 MOVECLIM native-forest plot detection and elevation contrast."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_MOVECLIM_2013_refugia_v1_278 import audit_plot_frame


def synthetic():
    ev=[]
    for island in ("Pico","Flores"):
        for plot_no,elevation in (("1",100),("2",500),("3",900)):
            for subplot in range(1,5):
                ev.append({"coreid":f"{island}-{plot_no}-{subplot}",
                           "eventID":f"EVENT-{island}-{plot_no}-{subplot}",
                           "locationID":f"{island}-plot{plot_no}",
                           "island":island,
                           "year":"2013","eventDate":"2013-08-01",
                           "minimumElevationInMeters":str(elevation),
                           "maximumElevationInMeters":str(elevation)})
    observations=[]
    def add(island,plot_no,subplot,name,means="native",cover="5",rank="species"):
        observations.append({"coreid":f"{island}-{plot_no}-{subplot}",
                             "scientificName":name,"genus":name.split(" ")[0],
                             "specificEpithet":name.split(" ")[1],
                             "taxonRank":rank,"establishmentMeans":means,
                             "organismQuantity":cover,"organismQuantityType":"OTV"})
    # Loss taxon A occurs only in the upper plot on Pico, in lower plot on Flores.
    for j in (1,2,3,4): add("Pico","3",j,"Alpha alba")
    add("Flores","1",1,"Alpha alba")
    # Five indigenous reference species on Pico at the lower/middle plots.
    for i,name in enumerate(("Beta beta","Gamma gamma","Delta delta","Epsilon epsilon","Zeta zeta")):
        add("Pico","1" if i<4 else "2",1,name)
    add("Pico","1",3,"Introduced introduced",means="introduced")
    add("Pico","2",1,"Subspecies beta",rank="subspecies")
    # Uncertain/nonnumeric cover records excluded from detected site taxon.
    add("Pico","3",3,"Invalid cover",cover="NA")
    # Source S1 has historical losses on both study and other island.
    losses=[
      {"Species":"Alpha alba","Archipelago":"Azores","Island":"Pico",
       "Category":"Well-supported","Extinction category":"Extirpation (Island level)"},
      {"Species":"Alpha alba","Archipelago":"Azores","Island":"São Miguel",
       "Category":"Well-supported","Extinction category":"Extirpation (Island level)"},
      {"Species":"Another another","Archipelago":"Azores","Island":"Flores",
       "Category":"Doubtful","Extinction category":"Extirpation (Island level)"}]
    return ev,observations,losses


def test_subplot_repeats_collapse_to_independent_plots_and_altitude():
    e,o,l=synthetic()
    r=audit_plot_frame(e,o,l,expected_plots=6,expected_events=24,
                       min_reference_species=5,min_affected_species=1)
    assert r["physical"]["event_subplots"]==24
    assert r["physical"]["distinct_permanent_plots"]==6
    assert r["physical"]["plots_by_island"]=={"Flores":3,"Pico":3}
    assert r["incidence"]["eligible_native_plot_taxon_positives"]==7
    assert r["historical"]["distinct_S1_loss_taxa"]==1
    assert r["historical"]["S1_loss_taxa_detected_in_2013"]==1
    assert r["historical"]["historically_lost_taxon_island_pairs_with_2013_positive_plot"]==1
    pico=r["by_island"]["Pico"]
    assert pico["affected_native_taxa"]==1 and pico["reference_native_taxa"]==5
    assert pico["affected_mean_elevation_percentile"]==1.0
    assert pico["reference_mean_elevation_percentile"]<0.5
    assert pico["elevation_percentile_difference_affected_minus_reference"]>0.5
    assert r["sampling_warning"]["not_independent_subplots"] is True
    assert r["sampling_warning"]["not_historical_extinction_risk"] is True
    assert "Alpha alba" not in str(r) and "Pico-plot" not in str(r)


def test_missing_subplots_and_duplicate_author_coreid_fail_closed():
    e,o,l=synthetic()
    try:
        audit_plot_frame(e[:-1],o,l,expected_plots=6,expected_events=24)
    except ValueError as ex:
        assert "Event" in str(ex) or "four" in str(ex).lower()
    else:raise AssertionError("Missing one of four subplots cannot be silently added")
    e,o,l=synthetic()
    e[-1]["coreid"]=e[0]["coreid"]
    try:
        audit_plot_frame(e,o,l,expected_plots=6,expected_events=24)
    except ValueError as ex:
        assert "coreid" in str(ex).lower()
    else:raise AssertionError("Different eventID cannot share original primary Event core ID")


def test_unmatched_negative_is_plot_nondetection_not_whole_island_absence():
    e,o,l=synthetic()
    r=audit_plot_frame(e,o,l,expected_plots=6,expected_events=24,
                       min_reference_species=5,min_affected_species=1)
    assert r["sampling_warning"]["plot_local_nondetection_not_island_absence"] is True
    assert r["historical"]["S1_loss_taxa_not_seen_in_2013"]==0
    assert r["by_island"]["Flores"]["reference_native_taxa"]==0
    assert r["by_island"]["Flores"]["comparison_estimable"] is False


def test_multiple_islands_and_non_native_cannot_fake_native_reference():
    e,o,l=synthetic()
    # More introduced records must not affect native reference numerator.
    o.extend([{**o[0], "coreid":"Pico-2-4","scientificName":"Alien alien",
               "establishmentMeans":"introduced","genus":"Alien",
               "specificEpithet":"alien"}])
    r=audit_plot_frame(e,o,l,expected_plots=6,expected_events=24,
                       min_reference_species=5,min_affected_species=1)
    assert r["by_island"]["Pico"]["reference_native_taxa"]==5
    assert r["incidence"]["nonnative_or_unknown_plot_taxon_records"]>=2


def test_elevation_spread_more_than_thirty_metres_is_not_valid_independent_plot():
    e,o,l=synthetic()
    e[1]["minimumElevationInMeters"]="220"
    try:audit_plot_frame(e,o,l,expected_plots=6,expected_events=24)
    except ValueError as ex:assert "elevation" in str(ex).lower()
    else:raise AssertionError("Source-defined same 10x10m plot 120m span invalid")
