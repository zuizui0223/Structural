"""Source-metadata only: SLAM exact forest site/habitat/origin roles and stop."""
import io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slam_original_forest_habitat_schema_v1_325 import parse_opaque

def fixture(*,habitat=True, origin=True, site=True):
    e=["eventID","eventDate","island","samplingProtocol"]
    if habitat:e.append("habitat")
    if site:e.append("locationID")
    o=["scientificName","taxonRank","order"]
    if origin:o.append("establishmentMeans")
    def fields(keys):
        return "".join(f'<field term="http://rs.tdwg.org/dwc/terms/{x}" index="{i}"/>' for i,x in enumerate(keys,1))
    meta=(
       '<archive xmlns="http://rs.tdwg.org/dwc/text/">'
       '<core rowType="http://rs.tdwg.org/dwc/terms/Event">'
       '<files><location>event.txt</location></files><id index="0"/>'
       +fields(e)+'</core>'
       '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
       '<files><location>occurrence.txt</location></files><coreid index="0"/>'
       +fields(o)+'</extension></archive>'
    )
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("event.txt","SECRET_NATIVE_EXOTIC_FOREST_SITES_NEVER_READ")
        z.writestr("occurrence.txt","SECRET_ENDANGERED_BEETLE_NAMES_NEVER_READ")
    return buf.getvalue()

def test_exact_roles_metadata_only_both_original_response_members_sealed():
    r=parse_opaque(fixture())
    assert r["status"]=="SLAM_HABITAT_AND_ORIGIN_METADATA_PRESENT_EVENT_VALUES_SEALED"
    assert r["candidate_forest_habitat_Event_terms"]==["habitat"]
    assert r["candidate_site_identity_Event_terms"]==["locationID"]
    assert r["candidate_biogeographic_origin_Occurrence_terms"]==["establishmentMeans"]
    assert r["original_Event_rows_opened"]==0 and r["original_Occurrence_rows_opened"]==0
    assert r["raw_original_plot_species_or_habitat_values_opened"]==0
    assert r["original_BALA_PRIBES_taxon_outcomes_reopened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "SECRET_NATIVE" not in json.dumps(r) and "SECRET_ENDANGERED" not in json.dumps(r)

def test_missing_explicit_habitat_term_stops_scientific_transfer_before_source():
    r=parse_opaque(fixture(habitat=False))
    assert r["status"]=="TERMINAL_MISSING_ORIGINAL_EXPLICIT_HABITAT_OR_ORIGIN_SCHEMA"
    assert not r["candidate_forest_habitat_Event_terms"]
    assert r["original_Occurrence_rows_opened"]==0

def test_missing_origin_or_plot_identity_is_terminal():
    a=parse_opaque(fixture(origin=False))
    assert a["status"]=="TERMINAL_MISSING_ORIGINAL_EXPLICIT_HABITAT_OR_ORIGIN_SCHEMA"
    assert a["candidate_biogeographic_origin_Occurrence_terms"]==[]
    b=parse_opaque(fixture(site=False))
    assert b["status"]=="TERMINAL_MISSING_ORIGINAL_EXPLICIT_HABITAT_OR_ORIGIN_SCHEMA"
    assert b["candidate_site_identity_Event_terms"]==[]
