"""Synthetic beetle family resolution, method balance, original forest-level summaries."""
import importlib.util
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_canopy_family_response.py")
spec=importlib.util.spec_from_file_location("canopy_family",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    protocols=[
        "light trap (canopy)","light trap (understory)",
        "slam trap (canopy top jar)","slam trap (canopy bottom jar)",
        "slam trap (understory top jar)","slam trap (understory bottom jar)",
        "fit with yellow pan (canopy)","fit with yellow pan (understory)"
    ]
    events=[]
    for protocol in protocols:
        for i in range(36):
            events.append({"_core_id":"id"+str(len(events)),"eventID":"orig"+str(len(events)),
                "locationID":"forestA" if i<18 else "forestB",
                "samplingProtocol":protocol,"sampleSizeUnit":"day",
                "sampleSizeValue":"10","samplingEffort":"10 days","eventDate":"2020-03-01"})
    top=next(e["_core_id"] for e in events if "slam trap (canopy top" in e["samplingProtocol"])
    low=next(e["_core_id"] for e in events if "slam trap (understory top" in e["samplingProtocol"])
    btop=next(e["_core_id"] for e in events if "slam trap (canopy top" in e["samplingProtocol"] and e["locationID"]=="forestB")
    blow=next(e["_core_id"] for e in events if "slam trap (understory top" in e["samplingProtocol"] and e["locationID"]=="forestB")
    occ=[
        {"_core_id":top,"individualCount":"600","family":"Curculionidae","taxonRank":"genus"},
        {"_core_id":low,"individualCount":"200","family":"Curculionidae","taxonRank":"family"},
        {"_core_id":btop,"individualCount":"400","family":"Staphylinidae","taxonRank":"genus"},
        {"_core_id":blow,"individualCount":"422","family":"Staphylinidae","taxonRank":"species"},
    ]
    return events,occ

def test_protocol_and_family_filtering():
    assert m.protocol_category("SLAM trap (Canopy Top Jar)")==("SLAM","canopy")
    assert m.protocol_category("light trap (understory)")==("LIGHT","understorey")
    assert m.valid_family("Staphylinidae")=="Staphylinidae"
    assert m.valid_family("Coleoptera") is None
    assert m.valid_family("unknown") is None
    assert m.bray_relative({"A":2,"B":2},{"A":1,"B":1})==0
    assert m.bray_relative({"A":2},{"B":1})==1.0

def test_original_record_scope_does_not_become_288_forests():
    original=m.original_tables
    try:
        m.original_tables=lambda data:fixture()
        r=m.analyze(b"synthetic")
    finally:
        m.original_tables=original
    assert r["source_field_original_event_count"]==288
    assert r["source_original_occurrence_rows"]==4
    assert r["published_beetle_specimens_reproduced"]==1622
    assert r["canopy_SLAM_beetle_individuals"]==1000
    assert r["understorey_SLAM_beetle_individuals"]==622
    assert r["unique_forest_study_regions"]==2
    assert r["SLAM_jar_events_per_layer"]=={"canopy":72,"understorey":72}
    assert r["causal_canopy_height_effect_estimated"] is False
    assert r["species_level_richness_estimable_from_publisher_rows"] is False
    assert r["data_release_covers_only_two_forest_regions"] is True
    assert r["no_raw_coordinates_or_source_eventIDs_exported"] is True
