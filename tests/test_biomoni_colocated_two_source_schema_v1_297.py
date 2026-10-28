"""No ecological response read: synthetic dual BioMonI original archive preflight."""
import io,json,sys,zipfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import biomoni_colocated_two_source_schema_v1_297 as gate

def archive(*,include_location=True, include_origin=True):
    evt=['eventID','island']+(['locationID'] if include_location else [])+['eventDate','samplingProtocol','decimalLatitude','decimalLongitude']
    occ=['scientificName']+(['establishmentMeans'] if include_origin else [])+['taxonRank','organismQuantity']
    def fields(x):
        return ''.join(f'<field term="http://rs.tdwg.org/dwc/terms/{v}" index="{i}"/>' for i,v in enumerate(x,1))
    xml=('<?xml version="1.0"?>'
      '<archive xmlns="http://rs.tdwg.org/dwc/text/">'
      '<core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>event.txt</location></files><id index="0"/>'
      +fields(evt)+'</core>'
      '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>occurrence.txt</location></files>'
      '<coreid index="0"/>'+fields(occ)+'</extension></archive>')
    result=io.BytesIO()
    with zipfile.ZipFile(result,'w') as z:
        z.writestr('meta.xml',xml)
        z.writestr('event.txt','PRIVATE_PLOT_ID_NOT_READ')
        z.writestr('occurrence.txt','PRIVATE_SPECIES_LABEL_NEVER_READ')
    return result.getvalue()

def test_exact_original_metadata_roles_do_not_open_any_species_or_site(monkeypatch):
    data=archive()
    monkeypatch.setitem(gate.SOURCES["woody"],"sha",None)
    r=gate.inventory({"woody":data,"beetle":data})
    assert r["status"]=="TWO_SOURCE_META_QUALIFIED_SITE_VALUES_UNOPENED"
    assert r["potential_exact_shared_Terceira_plot_count_from_papers_only"]==10
    assert not r["actual_original_site_match_scored"]
    assert r["eligible_to_freeze_event_only_exact_crosswalk"]
    assert r["original_biological_Event_rows_opened"]==0
    assert r["original_plant_Occurrence_rows_opened"]==0
    assert r["original_beetle_Occurrence_rows_opened"]==0
    assert "PRIVATE_SPECIES_LABEL_NEVER_READ" not in json.dumps(r)
    assert "PRIVATE_PLOT_ID_NOT_READ" not in json.dumps(r)
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]

def test_original_woody_source_sha_must_not_be_substituted():
    with pytest.raises(ValueError,match="woody-source SHA"):
        gate.schema_only(archive(),"woody")

def test_missing_plot_key_is_stop_before_taxon_outcome(monkeypatch):
    monkeypatch.setitem(gate.SOURCES["woody"],"sha",None)
    r=gate.inventory({"woody":archive(include_location=False),"beetle":archive()})
    assert r["status"]=="TERMINAL_MISSING_SAME_SITE_SOURCE_SCHEMA_BEFORE_RESPONSES"
    assert not r["eligible_to_freeze_event_only_exact_crosswalk"]
    assert r["sources"]["woody"]["missing_Event_terms"]==["locationID"]
    assert r["original_plant_Occurrence_rows_opened"]==0

def test_missing_colonisation_status_is_stop_before_taxon_outcome(monkeypatch):
    monkeypatch.setitem(gate.SOURCES["woody"],"sha",None)
    r=gate.inventory({"woody":archive(),"beetle":archive(include_origin=False)})
    assert r["status"]=="TERMINAL_MISSING_SAME_SITE_SOURCE_SCHEMA_BEFORE_RESPONSES"
    assert r["sources"]["beetle"]["missing_Occurrence_terms"]==["establishmentMeans"]
    assert r["original_beetle_Occurrence_rows_opened"]==0

def test_zip_traversal_detected_in_the_archive_without_opening_biology():
    x=io.BytesIO()
    with zipfile.ZipFile(x,'w') as z:z.writestr("../event.txt","SENSITIVE")
    with pytest.raises(ValueError):
        gate.schema_only(x.getvalue(),"beetle")
