"""Original 2024 balanced native/exotic forest source ZIP metadata firewall."""
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from terceira_2024_forest_original_meta_v1_332 import opaque_inventory

def build(*,site=True,habitat=True,height=True,origin=True):
    event=["eventID","eventDate","samplingProtocol"]
    if site:event.append("locationID")
    if habitat:event.append("habitat")
    if height:event.append("samplingEffort")
    occur=["scientificName","taxonRank","order"]
    if origin:occur.append("establishmentMeans")
    def fs(fields):
        return "".join(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{field}"/>'
                       for i,field in enumerate(fields,1))
    meta=(
        '<archive xmlns="http://rs.tdwg.org/dwc/text/">'
        '<core rowType="http://rs.tdwg.org/dwc/terms/Event">'
        '<files><location>Event.txt</location></files><id index="0"/>'
        +fs(event)+'</core>'
        '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
        '<files><location>Occurrence.txt</location></files><coreid index="0"/>'
        +fs(occur)+'</extension>'
        '</archive>'
    )
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("Event.txt","2024_TAXON_OPAQUE_NATIVE_FOREST_SOURCE_PLOT")
        z.writestr("Occurrence.txt","2024_SOURCE_ENDEMIC_BEETLE_NAMES_OPAQUE")
    return out.getvalue()

def test_original_event_species_roles_are_source_opaque():
    r=opaque_inventory(build())
    assert r["status"]=="TERCEIRA_2024_NATIVE_EXOTIC_SOURCE_META_ELIGIBLE_ALL_VALUES_CLOSED"
    assert r["author_site_meta_field_candidates"]==["locationID"]
    assert r["author_forest_habitat_meta_field_candidates"]==["habitat"]
    assert r["author_vertical_stratum_meta_field_candidates"]==["samplingEffort"]
    assert r["author_origin_meta_field_candidates"]==["establishmentMeans"]
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert r["older_source_biological_rows_reopened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]
    assert "2024_TAXON_OPAQUE" not in json.dumps(r)
    assert "ENDEMIC_BEETLE" not in json.dumps(r)

def test_missing_forest_habitat_hard_stops_before_original_species():
    result=opaque_inventory(build(habitat=False))
    assert result["status"]=="TERMINAL_2024_ORIGINAL_VERTICAL_HABITAT_OR_ORIGIN_SCHEMA"
    assert not result["author_forest_habitat_meta_field_candidates"]
    assert result["original_Occurrence_rows_opened"]==0

def test_unreported_origin_or_height_precludes_vertical_habitat_transfer():
    for variant in ({"origin":False},{"height":False},{"site":False}):
        r=opaque_inventory(build(**variant))
        assert r["status"]=="TERMINAL_2024_ORIGINAL_VERTICAL_HABITAT_OR_ORIGIN_SCHEMA"
        assert r["original_Event_rows_opened"]==0
        assert r["original_Occurrence_rows_opened"]==0
