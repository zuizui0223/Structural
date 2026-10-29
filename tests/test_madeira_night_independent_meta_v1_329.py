"""Madeira LIFE Natura@night source-only original archive firewall tests.

Original public source biological and habitat rows MUST stay unseen until
the predeclared physical-site and source habitat gates qualify.
"""
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from madeira_night_independent_meta_v1_329 import inspect_meta_only


def mock(*,location=True,habitat=True,origin=True,method=True):
    event=["eventID","eventDate"]
    if method:event.append("samplingProtocol")
    if location:event.append("locationID")
    if habitat:event.append("habitat")
    occurrence=["scientificName","taxonRank","order"]
    if origin:occurrence.append("establishmentMeans")
    def columns(items):
        return "".join(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{name}"/>'
                       for i,name in enumerate(items,1))
    meta=(
        '<archive xmlns="http://rs.tdwg.org/dwc/text/">'
        '<core rowType="http://rs.tdwg.org/dwc/terms/Event">'
        '<files><location>events.tsv</location></files><id index="0"/>'
        +columns(event)+'</core>'
        '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
        '<files><location>occurrences.tsv</location></files><coreid index="0"/>'
        +columns(occurrence)+'</extension>'
        '</archive>'
    )
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w") as data:
        data.writestr("meta.xml",meta)
        data.writestr("events.tsv","MADEIRA_SECRET_NATIVE_FOREST_ALAN_LOCATIONS")
        data.writestr("occurrences.tsv","MADEIRA_SECRET_ENDEMIC_MOTH_SPECIES")
    return output.getvalue()


def test_valid_source_schema_is_not_original_data_access():
    r=inspect_meta_only(mock())
    assert r["status"]=="ORIGINAL_MADEIRA_FOREST_HABITAT_ORIGIN_SCHEMA_POSSIBLE_VALUES_SEALED"
    assert r["candidate_original_habitat_fields"]==["habitat"]
    assert r["candidate_original_biogeographic_origin_fields"]==["establishmentMeans"]
    assert r["source_schema_qualification"]["source_physical_site_identity_available"]
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert r["original_species_and_habitat_values_inspected"]==0
    assert r["Azores_original_species_sources_reopened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "MADEIRA_SECRET_NATIVE" not in json.dumps(r)
    assert "MADEIRA_SECRET_ENDEMIC" not in json.dumps(r)


def test_missing_habitat_prohibits_madeira_native_forest_ecological_score():
    r=inspect_meta_only(mock(habitat=False))
    assert r["status"]=="TERMINAL_MADEIRA_HABITAT_OR_ORIGIN_SOURCE_SCHEMA_INSUFFICIENT"
    assert not r["candidate_original_habitat_fields"]
    assert r["original_Occurrence_rows_opened"]==0


def test_missing_origin_prohibits_relabeling_identified_arthropods():
    r=inspect_meta_only(mock(origin=False))
    assert r["status"]=="TERMINAL_MADEIRA_HABITAT_OR_ORIGIN_SOURCE_SCHEMA_INSUFFICIENT"
    assert not r["candidate_original_biogeographic_origin_fields"]
    assert r["original_Event_rows_opened"]==0


def test_missing_original_site_or_trap_method_is_hard_stop():
    for variation in ({"location":False},{"method":False}):
        r=inspect_meta_only(mock(**variation))
        assert r["status"]=="TERMINAL_MADEIRA_HABITAT_OR_ORIGIN_SOURCE_SCHEMA_INSUFFICIENT"
        assert not all(r["source_schema_qualification"].values())
        assert r["original_Event_rows_opened"]==0
