"""v1.335 45 source Event-only original forests, common elevation strict 2-island rule."""
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slamii_original_forest_elevation_event_v1_335 import evaluate,normalize,classify_habitat

N={"COR":(0,1,0),"FLO":(2,1,2),"SMR":(3,5,8),"TER":(3,11,9)}
ISLAND={"COR":"Corvo","FLO":"Flores","SMR":"Santa Maria","TER":"Terceira"}

def p():return json.loads((ROOT/"development/slamii_original_45forest_event_elevation_contract_v1_335.json").read_text())

def source(*,extra_ter_overlap=False):
    rows=[]
    for code,(n,m,e) in N.items():
        counter=0
        for k,count in (("native",n),("mixed",m),("exotic",e)):
            for i in range(count):
                if code=="FLO":
                    h=([381,769] if k=="native" else [106] if k=="mixed" else [315,607])[i]
                elif code=="SMR":
                    h=([192,355,374] if k=="native" else
                       [150,240,325,420,480] if k=="mixed" else
                       [170,200,260,280,300,340,390,450])[i]
                elif code=="TER":
                    h=([300,420,500] if extra_ter_overlap else [600,750,900])[i] if k=="native" else (
                       [240,260,290,320,350,380,410,450,470,520,640] if k=="mixed" else
                       [220,270,310,360,400,440,480,530,610])[i]
                else:h=248
                row={
                    "__original_coreid":f"{code}-{counter:03}",
                    "eventID":f"EVENT-{code}-{counter:03}",
                    "locationID":f"FOREST-{code}-{counter:03}",
                    "island":ISLAND[code],
                    "habitat":f"{k.title()} Forest - Example trees",
                    "minimumElevationInMeters":str(h),
                    "decimalLatitude":str(38.1+len(rows)*.01),
                    "decimalLongitude":str(-27.1-len(rows)*.01),
                    "eventDate":"2019-05-15" if len(rows)%2 else "2020-06-16",
                    "year":"2019" if len(rows)%2 else "2020",
                    "sampleSizeUnit":"month",
                    "sampleSizeValue":"3",
                    "samplingProtocol":"SLAM trap"
                }
                rows.append(row);counter+=1
    assert len(rows)==45
    return rows

def test_original_source_landscape_sorted_by_elevation_without_two_islands():
    r=evaluate(source(),p())
    assert r["status"]=="TERMINAL_NATIVE_VS_ALTERED_ELEVATION_COMMON_SUPPORT_LT_TWO_ISLANDS"
    assert r["original_Event_values_read"]==45 and r["original_Occurrence_values_read"]==0
    assert r["original_author_physical_site_n"]==45
    assert r["original_4island_physical_sites"]=={"COR":1,"FLO":5,"SMR":16,"TER":23}
    assert r["original_habitat_site_totals"]=={"native":8,"mixed":18,"exotic":19}
    assert r["islands_with_two_native_and_two_altered_inside_common_elevation_support"]==["SMR"]
    assert r["original_per_island_habitat_elevation"]["TER"]["common_elevation_interval_m"]==[600.,640.]
    assert r["original_per_island_habitat_elevation"]["FLO"]["common_elevation_interval_m"]==[381.,607.]
    assert r["original_per_island_habitat_elevation"]["FLO"]["n_original_native_plots_in_common_elevation_range"]==1
    assert r["source_original_plot_IDs_species_and_coordinates_not_exported"]
    assert "FOREST-FLO" not in json.dumps(r)
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]

def test_ecological_species_followup_requires_2_geographic_source_islands():
    r=evaluate(source(extra_ter_overlap=True),p())
    assert r["status"]=="ORIGINAL_FOREST_ELEVATION_2ISLAND_COMMON_SUPPORT_TAXA_SEALED"
    assert r["islands_with_two_native_and_two_altered_inside_common_elevation_support"]==["SMR","TER"]
    assert r["original_Occurrence_values_read"]==0

def test_original_forest_metadata_unknown_habitat_is_no_contrast_not_imputed():
    q=source();q[3]["habitat"]="unclassified mangrove"
    r=evaluate(q,p())
    assert r["status"]=="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
    assert r["original_source_site_metadata_invalid_counts"]["unknown_original_forest_type"]==1
    assert r["original_Occurrence_values_read"]==0

def test_original_physical_site_mismatch_hard_stops():
    q=source();q[3]["locationID"]=q[2]["locationID"]
    r=evaluate(q,p())
    assert r["status"]=="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
    assert r["original_source_site_metadata_invalid_counts"]["repeated_source_physical_plot_key"]==1

def test_all_45_source_events_and_2019_2020_calendar_are_fixed():
    with pytest.raises(ValueError,match="45"):
        evaluate(source()[:-1],p())
    q=source();q[4]["year"]="2018"
    r=evaluate(q,p())
    assert r["status"]=="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
    assert r["original_source_site_metadata_invalid_counts"]["outside_source_calendar_or_source_year_mismatch"]==1
    assert classify_habitat("Native Forest - Erica azorica",p())=="native"
    assert classify_habitat("Mixed Forest - Acacia",p())=="mixed"
    assert classify_habitat("Exotic Forest - Cryptomeria",p())=="exotic"
