"""v1.321 original-source-opaque physical site and island sampling tests."""
import copy,json,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from pribes_original_event_sites_v1_321 import audit,normalized_island,alphabetize

def contract():
    return json.loads((ROOT/"development/pribes_original_event_site_contract_v1_321.json").read_text(encoding="utf-8"))

def fixture():
    island_counts={"FAI":12,"FLO":12,"PIC":12,"TER":12,"SMG":12,"SMR":12,"COR":7}
    names={"FAI":"Faial","FLO":"Flores","PIC":"Pico","TER":"Terceira",
           "SMG":"São Miguel","SMR":"Santa Maria","COR":"Corvo"}
    out=[]
    for code,n in island_counts.items():
        for i in range(n):
            original_id=f"PRIBES-{code}-{i:02d}"
            out.append({
                "original_coreid":original_id,
                "eventID":original_id,
                "eventDate":"2021-07-07",
                "year":"2021",
                "island":names[code],
                "locationID":f"SITE_{code}_{i:02d}",
                "samplingProtocol":"One-hour beating",
                "sampleSizeValue":"1",
                "sampleSizeUnit":"hour",
                "decimalLatitude":str(38.5+i*.001),
                "decimalLongitude":str(-27.2-i*.001)
            })
    assert len(out)==79
    out.append({**out[0],"original_coreid":"ZZZ-PRIBES-FAI-00-REPEAT",
                "eventID":"ZZZ-PRIBES-FAI-00-REPEAT"})
    return out

def test_all_six_fixed_overlap_islands_original_79_sites_from_80_events():
    out=audit(fixture(),contract())
    assert out["status"]=="PRIBES_6_ISLAND_SOURCE_PHYSICAL_EFFORT_ELIGIBLE_TAXA_SEALED"
    assert out["original_Event_rows_examined"]==80
    assert out["source_physical_location_key_n"]==79
    assert out["source_duplicate_Event_over_physical_key_n"]==1
    assert out["source_duplicate_site_conflicts"]==0
    assert out["overlapping_BALA_island_site_count"]==72
    assert out["selected_six_overlap_original_Event_count"]==72
    assert out["source_method_and_effort_identical_across_six_islands"]
    assert out["observed_island_physical_site_counts"]=={
        "COR":7,"FAI":12,"FLO":12,"PIC":12,"SMG":12,"SMR":12,"TER":12}
    assert len(out["selected_six_overlap_island_original_coreids_sha256"])==64
    assert out["PRIBES_Original_Occurrence_rows_opened"]==0
    assert not out["BALA_original_species_response_reopened"]
    assert out["original_GEB_mammal_scientific_HOLD"]
    assert out["new_confirmatory_systems"]==0 and not out["eBird_used"]
    assert "SITE_FAI" not in json.dumps(out)
    assert "PRIBES-FAI" not in json.dumps(out)

def test_ambiguous_original_duplicate_site_geography_terminal_without_species():
    data=fixture()
    data[-1]["decimalLatitude"]="39.99"
    out=audit(data,contract())
    assert out["status"]=="PRIBES_EVENT_SOURCE_SITE_OR_EFFORT_TERMINAL_NO_SPECIES_OPEN"
    assert out["source_duplicate_site_conflicts"]==1
    assert out["PRIBES_Original_Occurrence_rows_opened"]==0

def test_original_island_missing_minimum_is_not_reassigned():
    data=fixture()
    for e in data:
        if e["island"]=="Faial" and int(e["locationID"].split("_")[-1])>2:
            e["island"]="Corvo"
    result=audit(data,contract())
    assert result["status"]=="PRIBES_EVENT_SOURCE_SITE_OR_EFFORT_TERMINAL_NO_SPECIES_OPEN"
    assert result["observed_island_physical_site_counts"]["FAI"]==3
    assert not result["has_exactly_six_BALA_overlap_islands"]

def test_nonuniform_original_sampling_duration_stops_island_correlation():
    data=fixture()
    data[15]["sampleSizeValue"]="2"
    r=audit(data,contract())
    assert r["status"]=="PRIBES_EVENT_SOURCE_SITE_OR_EFFORT_TERMINAL_NO_SPECIES_OPEN"
    assert not r["source_method_and_effort_identical_across_six_islands"]

def test_original_source_year_outside_2019_2025_is_hard_stop():
    data=fixture()
    data[15]["eventDate"]="2018-02-01"
    data[15]["year"]="2018"
    with pytest.raises(ValueError,match="date outside"):
        audit(data,contract())

def test_only_predeclared_island_and_id_grammar():
    p=contract()
    assert normalized_island("São Miguel",p["field_contract"]["island_mapping_predeclared"])=="SMG"
    assert normalized_island("Sao Miguel",p["field_contract"]["island_mapping_predeclared"])=="SMG"
    assert alphabetize("PRIBES-SÃO-001")=="PRIBESSAO001"
