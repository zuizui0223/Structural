"""Original SLAM II DwCA meta-only source roles, never original taxon rows."""
import io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slamii_original_meta_only_v1_334 import inspect
def contract():return json.loads((ROOT/"development/slamii_forest_elevation_original_protocol_v1_334.json").read_text())
def archive(*,elevation=True,origin=True):
    ev=["eventID","eventDate","island","locationID","habitat","samplingProtocol"]
    if elevation:ev.append("minimumElevationInMetres")
    oc=["scientificName","taxonRank","order"]
    if origin:oc.append("establishmentMeans")
    def fields(items):return "".join(
       f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{v}"/>' for i,v in enumerate(items,1))
    meta=('<archive xmlns="http://rs.tdwg.org/dwc/text/">'
          '<core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>e.tsv</location></files>'
          '<id index="0"/>'+fields(ev)+'</core>'
          '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>o.tsv</location></files>'
          '<coreid index="0"/>'+fields(oc)+'</extension></archive>')
    z=io.BytesIO()
    with zipfile.ZipFile(z,'w') as f:
        f.writestr("meta.xml",meta)
        f.writestr("e.tsv","ORIGINAL_FOREST_SITE_VALUES_MUST_NOT_READ")
        f.writestr("o.tsv","ORIGINAL_EXOTIC_SPECIES_NAMES_MUST_NOT_READ")
    return z.getvalue()
def test_frozen_original_schema_allows_elevation_event_stage_only():
    r=inspect(archive(),contract())
    assert r["status"]=="ORIGINAL_45SITE_FOREST_ELEVATION_SOURCE_SCHEMA_READY_EVENT_VALUES_SEALED"
    assert r["available_original_elevation_fields"]==["minimumElevationInMetres"]
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]
    assert "ORIGINAL_FOREST_SITE_VALUES" not in json.dumps(r)
    assert "ORIGINAL_EXOTIC_SPECIES_NAMES" not in json.dumps(r)
def test_missing_original_source_altitude_hard_stops():
    r=inspect(archive(elevation=False),contract())
    assert r["status"]=="TERMINAL_ORIGINAL_FOREST_ELEVATION_OR_TAXON_SOURCE_SCHEMA"
    assert not r["original_schema_eligibility"]["source_elevation_any"]
def test_missing_original_species_origin_prevents_causal_species_scoring():
    r=inspect(archive(origin=False),contract())
    assert r["status"]=="TERMINAL_ORIGINAL_FOREST_ELEVATION_OR_TAXON_SOURCE_SCHEMA"
    assert not r["original_schema_eligibility"]["source_taxonomic_status"]
    assert r["original_Occurrence_rows_opened"]==0
