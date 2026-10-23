"""Source-free synthetic pre-response study test for new 90-plot ForestEco2 v1.288."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
from foresteco2_nine_cell_focal_original_v1_288 import score_original,statistic,quantile
from test_foresteco2_event_only_qualification_v1_286 import make_rows

ROOT=Path(__file__).resolve().parents[1]
def contract():
    return json.loads((ROOT/"development/foresteco2_nine_cell_focal_composition_protocol_v1_288.json").read_text())

def example():
    events=make_rows()
    for island in ("Pico","São Miguel","Terceira"):
        for e in events:
            if e["island"]==island and e["habitat"]=="NF":
                e["habitat"]="EW"
                break
    for e in events:
        e["habitat"]={"NF":"Natural Forest","EW":"Exotic Woodland","PF":"Production Forest"}[e["habitat"]]
    ranks=["Alpha alba","Beta beta","Canna alba","Delta alba","Epsilon alba","Ficus alba",
           "Garcinia alba","Hoya alba","Ilex alba","Juniperus alba","Kalmia alba",
           "Laurus alba","Morus alba","Nerium alba","Opuntia alba","Piper alba",
           "Quercus alba","Rubus alba","Salix alba","Taxus alba"]
    losses=[]
    for k,taxon in enumerate(ranks):
        for isl in (["Pico","Terceira"] if k<4 else ["Pico"]):
            losses.append({"Species":taxon,"Archipelago":"Azores",
               "Category":"Well-supported","Extinction category":"Extirpation (Island level)","Island":isl})
    observations=[]
    for event in events:
        core=event["source_coreid"]
        observations.append({"coreid":core,"taxonRank":"species",
                             "scientificName":"Rho alba","establishmentMeans":"native"})
        if event["habitat"]=="Natural Forest":
            for t in ranks[:2]:
                observations.append({"coreid":core,"taxonRank":"species",
                       "scientificName":t,"establishmentMeans":"native"})
        observations.append({"coreid":core,"taxonRank":"species",
                        "scientificName":"Alienus rubra","establishmentMeans":"introduced"})
    while len(observations)<1150:
        observations.append({"coreid":events[0]["source_coreid"],"taxonRank":"species",
                         "scientificName":"Rho alba","establishmentMeans":"native"})
    return events,observations,losses

def test_primary_and_2000_draws_of_predeclared_uneven_strata():
    events,obs,losses=example()
    r=score_original(events,obs,losses,contract())
    assert r["status"]=="RETROSPECTIVE_INDEPENDENT_FOREST_SOURCE_DESCRIPTIVE_SCORE"
    assert r["total_original_event_rows"]==90
    assert r["total_original_occurrence_rows"]==1150
    assert r["fixed_historical_loss_taxa"]==20
    assert r["strict_historical_loss_taxon_island_pairs"]==24
    assert r["focal_native_taxa_detected_count"]==2
    assert r["focal_islands_detected_count"]==3
    assert r["focal_prediction_scored"] is True
    assert r["bootstrap_replicates"]==2000
    assert r["bootstrap_seed"]==1729
    assert r["primary_D"]>0
    assert r["bootstrap_CI95"][0]>0
    assert r["original_v1_286_gate_remains_terminal"]
    assert r["new_confirmatory_systems"]==0 and r["GEB_scientific_HOLD"]
    assert r["no_taxon_plot_island_label_pairs_or_raw_records_exported"]
    assert "Alpha alba" not in json.dumps(r)
    assert "Pico-NF" not in json.dumps(r)

def test_unexpected_biological_row_count_is_a_stop_not_resample():
    e,o,l=example()
    try:score_original(e,o[:-1],l,contract())
    except ValueError as ex:assert "totals" in str(ex)
    else:raise AssertionError("Source response row threshold was changed")

def test_fixed_jeffreys_smoothing_and_quantile():
    x={(i,t):[(1,4,0)]*9 for i in ("Pico","São Miguel","Terceira") for t in ("NF","EW","PF")}
    v,d,summary=statistic(x)
    assert v==0
    assert len(d)==3
    assert quantile([0,1,2,3,4],.25)==1
