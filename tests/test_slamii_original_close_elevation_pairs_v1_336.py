"""v1.336 post-source-design, pre-species exact altitude same-effort pairs.

Never treats original v1.335 frozen all-Event original class-frequency STOP as
a success. Strict same-source (year, effort, method), <=100m, two separate
islands, independent source original physical sites.
"""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slamii_original_close_elevation_pairs_v1_336 import compare,_best_pairs
from slamii_original_forest_elevation_event_v1_335 import evaluate

def protocols():
    p=json.loads((ROOT/"development/slamii_close_elevation_source_only_protocol_v1_336.json").read_text())
    old=json.loads((ROOT/"development/slamii_original_45forest_event_elevation_contract_v1_335.json").read_text())
    return p,old

def source():
    d={
      "COR":{"mixed":[248]},
      "FLO":{"native":[381,769],"mixed":[106],"exotic":[315,607]},
      "SMR":{"native":[192,355,377],
             "mixed":[61,90,120,150,180,185,242,300,360,400,420],
             "exotic":[440,460]},
      "TER":{"native":[392,440,500,652],"mixed":[18],
             "exotic":[80,100,120,160,200,230,250,260,276.5,300,330,370,392,430,480,520,560,584]}
    }
    island_names={"COR":"Corvo","FLO":"Flores","SMR":"Santa Maria","TER":"Terceira"}
    out=[]
    for island,categories in d.items():
        count=0
        for typ,elevs in categories.items():
            for height in elevs:
                out.append({
                   "__original_coreid":f"{island}-ORIG-{count:03}",
                   "eventID":f"{island}-FIELD-{count:03}",
                   "locationID":f"FOREST-{island}-{count:03}",
                   "island":island_names[island],
                   "habitat":f"{typ.title()} Forest - source trees",
                   "minimumElevationInMeters":str(height),
                   "decimalLatitude":str(38.1+len(out)*.001),
                   "decimalLongitude":str(-27.3-len(out)*.001),
                   "eventDate":"2019-05-15/2019-09-15",
                   "year":"2019",
                   "samplingProtocol":"SLAM trap",
                   "sampleSizeValue":"3" if island=="FLO" else "6",
                   "sampleSizeUnit":"months"
                })
                count+=1
    assert len(out)==45
    return out

def test_post_source_exact_two_island_matching_and_v335_stop_preserved():
    p,old=protocols()
    prior=evaluate(source(),old)
    assert prior["status"]=="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
    assert prior["original_habitat_site_totals"]=={"native":9,"mixed":14,"exotic":22}
    assert prior["original_per_island_habitat_elevation"]["SMR"]["common_elevation_interval_m"]==[192,377]
    assert prior["original_per_island_habitat_elevation"]["TER"]["common_elevation_interval_m"]==[392,584]
    out=compare(source(),p,old)
    assert out["status"]=="NEW_SEPARATE_SMRT_TER_FOREST_ELEVATION_PAIR_FRAME_TAXON_SEALED"
    assert out["source_islands_passing_2_pairs_and_matched_sampling"]==["SMR","TER"]
    assert out["source_matched_plot_pairs_by_island"]["SMR"]["matched_one_to_one_original_forest_plot_pairs"]==3
    assert out["source_matched_plot_pairs_by_island"]["TER"]["matched_one_to_one_original_forest_plot_pairs"]==3
    assert out["original_Source_Occurrence_rows_opened"]==0
    assert out["previous_v1_335_original_author_class_gate"]=="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
    assert out["GEB_scientific_HOLD"] and out["new_confirmatory_systems"]==0 and not out["eBird_used"]
    assert "FOREST-TER" not in json.dumps(out)
    assert len(out["source_matched_source_coreid_triplets_SHA256"])==64

def test_no_equal_effort_source_pair_stops_not_reweights():
    d=source()
    for e in d:
        if e["island"]=="Terceira" and e["habitat"].startswith(("Exotic","Mixed")):
            e["sampleSizeValue"]="4"
    p,old=protocols()
    out=compare(d,p,old)
    assert out["status"]=="TERMINAL_NO_TWO_ISLANDS_ELEVATION_YEAR_EFFORT_PAIRED_FOREST_PLOTS"
    assert out["source_matched_plot_pairs_by_island"]["TER"]["matched_one_to_one_original_forest_plot_pairs"]==0
    assert out["original_Source_Occurrence_rows_opened"]==0

def test_year_confounded_source_pairs_not_retained():
    d=source()
    for e in d:
        if e["island"]=="Santa Maria" and e["habitat"].startswith(("Exotic","Mixed")):
            e["eventDate"]="2020-05-15/2020-09-15"
            e["year"]="2020"
    p,old=protocols()
    out=compare(d,p,old)
    assert out["status"]=="TERMINAL_NO_TWO_ISLANDS_ELEVATION_YEAR_EFFORT_PAIRED_FOREST_PLOTS"
    assert out["source_matched_plot_pairs_by_island"]["SMR"]["matched_one_to_one_original_forest_plot_pairs"]==0

def test_pair_algorithm_max_cardinality_min_elevation_gap_and_no_taxa():
    base={"year":"2019","unit":"months","size":"6","method":"slam trap"}
    a=[dict(base,core="n1",elevation=350.),dict(base,core="n2",elevation=500.)]
    b=[dict(base,core="a1",elevation=355.),dict(base,core="a2",elevation=510.),
       dict(base,core="a3",elevation=900.)]
    pairs=_best_pairs(a,b,100.)
    assert sorted((x["core"],y["core"]) for x,y in pairs)==[("n1","a1"),("n2","a2")]
    assert len(_best_pairs(a,[dict(base,core="a4",elevation=350.,year="2020")],100.))==0
