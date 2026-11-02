"""Galápagos original Ant field source schema and hard biological-data firewall."""
import io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from galapagos_ant_original_meta_v1_338 import inventory

def make_source(*,site=True,habitat=True,origin=True,elevation=True):
    e=["eventID","eventDate","samplingProtocol"]
    if site:e.append("locationID")
    if habitat:e.append("habitat")
    if elevation:e.append("minimumElevationInMeters")
    o=["scientificName","taxonRank","order"]
    if origin:o.append("establishmentMeans")
    def field(items):
        return "".join(f'<field term="http://rs.tdwg.org/dwc/terms/{x}" index="{i}"/>' for i,x in enumerate(items,1))
    xml='<archive xmlns="http://rs.tdwg.org/dwc/text/">'
    xml+='<core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>events.tsv</location></files><id index="0"/>'+field(e)+'</core>'
    xml+='<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>occurrences.tsv</location></files><coreid index="0"/>'+field(o)+'</extension></archive>'
    z=io.BytesIO()
    with zipfile.ZipFile(z,'w') as f:
        f.writestr("meta.xml",xml)
        f.writestr("events.tsv","SAN_CRISTOBAL_NAMED_SITES_SECRET")
        f.writestr("occurrences.tsv","WASMANNIA_SCIENTIFIC_NAME_SECRET")
    return z.getvalue()

def contract():
    return json.loads((ROOT/"development/galapagos_ant_native_altered_source_contract_v1_338.json").read_text())

def test_valid_source_roles_without_any_original_data_row():
    r=inventory(make_source(),contract())
    assert r["status"]=="GALAPAGOS_ANT_SITE_HABITAT_ELEVATION_AND_ORIGIN_SCHEMA_PRESENT_RESPONSES_SEALED"
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert r["original_schema_candidates"]["site"]==["locationID"]
    assert r["original_schema_candidates"]["origin"]==["establishmentMeans"]
    assert r["source_plot_coordinates_status_taxa_values_unopened"]
    assert r["older_Azores_biological_sources_reopened"]==0
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"] and r["new_confirmatory_systems"]==0
    assert "SAN_CRISTOBAL_NAMED" not in json.dumps(r)
    assert "WASMANNIA" not in json.dumps(r)

def test_missing_origin_stops_instead_of_assuming_pest_names_invasive():
    r=inventory(make_source(origin=False),contract())
    assert r["status"]=="TERMINAL_SOURCE_MISSING_ANT_HABITAT_ORIGIN_FIELD"
    assert not r["source_qualification"]["source_taxonomic_origin"]
    assert r["original_Occurrence_rows_opened"]==0

def test_habitat_or_elevation_without_source_metadata_stops():
    for kwargs in ({"habitat":False},{"elevation":False},{"site":False}):
        r=inventory(make_source(**kwargs),contract())
        assert r["status"]=="TERMINAL_SOURCE_MISSING_ANT_HABITAT_ORIGIN_FIELD"
        assert r["original_Event_rows_opened"]==0
