"""Synthetic dated Event + Occurrence DwC-A; no actual Macaronesian records."""
import io
import zipfile
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores2020_SaoJorge_field_record_crosscheck_v1_269 import parse_event_occurrence, audit_dated_matches


def make_dwca():
    base="http://rs.tdwg.org/dwc/terms/"
    meta='''<?xml version="1.0"?>
    <archive xmlns="http://rs.tdwg.org/dwc/text/">
    <core rowType="'''+base+'''Event" encoding="UTF-8" ignoreHeaderLines="1">
     <files><location>event.txt</location></files><id index="0"/>
     <field index="1" term="'''+base+'''eventID"/>
     <field index="2" term="'''+base+'''eventDate"/>
     <field index="3" term="'''+base+'''island"/>
     <field index="4" term="'''+base+'''decimalLatitude"/>
    </core>
    <extension rowType="'''+base+'''Occurrence" encoding="UTF-8" ignoreHeaderLines="1">
     <files><location>occurrence.txt</location></files><coreid index="0"/>
     <field index="1" term="'''+base+'''scientificName"/>
     <field index="2" term="'''+base+'''taxonRank"/>
     <field index="3" term="'''+base+'''occurrenceStatus"/>
    </extension>
    </archive>'''
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("event.txt",("id\\teventID\\teventDate\\tisland\\tlat\\n"
                               "e01\\tpublic-1\\t2020-07-13\\tSão Jorge\\t38.6\\n"
                               "e02\\tpublic-2\\t2010\\tSão Jorge\\t38.6\\n"
                               "e03\\tpublic-3\\t2020-07-19\\tSão Jorge\\t38.7\\n").replace("\\t","\t").replace("\\n","\n"))
        z.writestr("occurrence.txt",("coreid\\tname\\trank\\tstatus\\n"
                                    "e01\\tAlpha alba\\tspecies\\tpresent\\n"
                                    "e01\\tBeta beta\\tspecies\\tpresent\\n"
                                    "e02\\tAlpha alba\\tspecies\\tpresent\\n"
                                    "e03\\tAlpha alba\\tspecies\\tpresent\\n"
                                    "e03\\tGenus species\\tsubspecies\\tpresent\\n").replace("\\t","\t").replace("\\n","\n"))
    return b.getvalue()


def loss(name,island):
    return {"Species":name,"Archipelago":"Azores","Island":island,
            "Extinction category":"Extirpation (Island level)",
            "Category":"Well-supported","Date":"1888"}

def test_dated_2020_field_events_link_by_real_event_coreid():
    r=parse_event_occurrence(make_dwca(),source_island="São Jorge")
    assert r["core_event_row_count"]==3
    assert r["occurrence_row_count"]==5
    assert r["valid_post_2017_event_count"]==2
    assert r["source_event_years"]=={"2020":2}
    assert r["observations_by_event_year"]["2020"]==3
    assert r["invalid_or_nominal_date_event_count"]==1
    assert r["source_island_location_validated"] is True
    assert len(r["valid_occurrences"])==3
    assert all(x["year"]==2020 and x["island"]=="São Jorge" for x in r["valid_occurrences"])


def test_2020_observed_species_on_previously_loss_record_is_not_called_recolonization():
    x=audit_dated_matches(parse_event_occurrence(make_dwca(),"São Jorge"),
                          [loss("Alpha alba","São Jorge"),loss("Beta beta","Pico")])
    assert x["strict_S1_Azores_taxa_submitted"]==2
    assert x["S1_taxa_with_source_confirmed_post_2017_field_occurrence"]==2
    assert x["historically_lost_on_SaoJorge_taxa_with_2020_field_records"]==1
    assert x["matched_taxa_2020_recorded_on_saojorge"]==2
    assert x["evidence_of_documented_later_field_detection_not_recolonization"] is True
    assert x["no_unobserved_zero_imputation"] is True
    assert "Alpha alba" not in str(x)


def test_missing_or_unjoinable_event_never_generates_presence():
    b=make_dwca()
    raw=parse_event_occurrence(b,"São Jorge")
    raw["valid_occurrences"]=[{"scientificName":"Unobserved x","year":2020,"island":"São Jorge"}]
    x=audit_dated_matches(raw,[loss("Alpha alba","Pico")])
    assert x["matched_taxa_2020_recorded_on_saojorge"]==0


def test_html_not_a_research_dwca():
    try:parse_event_occurrence(b"404 not found","São Jorge")
    except ValueError: pass
    else: raise AssertionError("Failed source signature needs hard-stop")
