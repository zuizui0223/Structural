"""v1.291 archive metadata firewall: tests never access Event/Occurrence content."""
import io,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_trail_plants_opaque_source_v1_291 import parse_opaque_archive

def fixture(native=True):
    eventfields=['eventID','eventDate','island','locationID']
    occfields=['scientificName','taxonRank']+(['establishmentMeans'] if native else [])
    ev=''.join(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{name}"/>' for i,name in enumerate(eventfields,1))
    ob=''.join(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{name}"/>' for i,name in enumerate(occfields,1))
    meta=('<?xml version="1.0"?><archive xmlns="http://rs.tdwg.org/dwc/text/">'
          '<core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>event.txt</location></files>'
          '<id index="0"/>'+ev+'</core>'
          '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
          '<files><location>occurrence.txt</location></files><coreid index="0"/>'+ob+'</extension></archive>')
    f=io.BytesIO()
    with zipfile.ZipFile(f,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("event.txt","SECRET_TRAIL_ROW_NEVER_READ")
        z.writestr("occurrence.txt","SECRET_SPECIES_OCCURRENCE_NEVER_READ")
    return f.getvalue()

def test_valid_but_opaque_and_nested_sampling_unscored():
    r=parse_opaque_archive(fixture())
    assert r["status"]=="SCHEMA_POSSIBLE_EVENT_UNOPENED"
    assert r["Event_meta"]["id_index_declared"]
    assert r["Occurrence_meta"]["coreid_index_declared"]
    assert r["original_Event_rows_opened"]==0
    assert r["original_Occurrence_rows_opened"]==0
    assert r["source_site_ids_and_taxon_names_read"]==0
    assert r["source_version_discrepancy_260_vs_210_events_unresolved"]
    assert not r["eBird_used"] and r["GEB_scientific_HOLD"]
    for term in ["SECRET_TRAIL_ROW_NEVER_READ","SECRET_SPECIES_OCCURRENCE_NEVER_READ"]:
        assert term not in json.dumps(r)

def test_no_original_nativeness_column_fails_scientific_qualification():
    r=parse_opaque_archive(fixture(native=False))
    assert r["status"]=="SCHEMA_HOLD_REQUIRED_TERMS_OR_LINK_MISSING"
    assert r["missing_required_Occurrence_terms"]==["establishmentMeans"]
    assert r["original_Occurrence_rows_opened"]==0

def test_meta_only_data_payload_cannot_influence_schema():
    raw=fixture()
    assert "SOURCE_TRANSPORT_OR_SCHEMA_STOP" != parse_opaque_archive(raw)["status"]
    assert parse_opaque_archive(raw)["archive_length_bytes"]==len(raw)
