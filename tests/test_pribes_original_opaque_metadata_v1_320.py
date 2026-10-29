"""Only original PRIBES ZIP schema; no site/species/origin data opened."""
import io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from pribes_original_opaque_metadata_v1_320 import parse_opaque
def fixture(origin=True):
    event=["eventID","eventDate","island","locationID","samplingProtocol"]
    occ=["scientificName","taxonRank","order"]+(["establishmentMeans"] if origin else [])
    def fields(words):
        return ''.join(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{word}"/>' for i,word in enumerate(words,1))
    xml=('<archive xmlns="http://rs.tdwg.org/dwc/text/">'
         '<core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>events.txt</location></files><id index="0"/>'
          +fields(event)+'</core>'
         '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>occurrences.txt</location></files>'
         '<coreid index="0"/>'+fields(occ)+'</extension></archive>')
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        z.writestr("meta.xml",xml)
        z.writestr("events.txt","PRIVATE_SITES_NEVER_OPEN")
        z.writestr("occurrences.txt","PRIVATE_SPECIES_AND_ORIGIN_NEVER_OPEN")
    return b.getvalue()
def test_exact_event_occurrence_schema_has_zero_biology_reopened():
    v=parse_opaque(fixture())
    assert v["status"]=="PRIBES_SOURCE_SCHEMA_ELIGIBLE_EVENT_AND_TAXON_VALUES_SEALED"
    assert v["source_80_Event_vs_79_physical_sites_discrepancy_unresolved"]
    assert v["original_Event_rows_opened"]==0 and v["original_Occurrence_rows_opened"]==0
    assert "PRIVATE_SITES" not in json.dumps(v)
    assert "PRIVATE_SPECIES" not in json.dumps(v)
    assert v["GEB_scientific_HOLD"] and v["new_confirmatory_systems"]==0 and not v["eBird_used"]
def test_missing_author_origin_is_scientific_stop_not_a_guessed_status():
    v=parse_opaque(fixture(origin=False))
    assert v["status"]=="PRIBES_SOURCE_SCHEMA_HOLD_BEFORE_SOURCE_SITE_VALUES"
    assert v["missing_required_Occurrence_terms"]==["establishmentMeans"]
    assert v["original_Occurrence_rows_opened"]==0
