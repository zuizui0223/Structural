"""Original Madeira/Porto Santo COBRA spider source version1.8 meta-only tests."""
import io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from madeira_spider_original_meta_v1_341 import metadata_only

def mock(origin=True,habitat=True):
    event=["eventID","eventDate","island","locationID","samplingProtocol"]
    if habitat:event.append("habitat")
    occurrence=["scientificName","taxonRank"]
    if origin:occurrence.append("establishmentMeans")
    def fields(keys):
        return "".join(f'<field term="http://rs.tdwg.org/dwc/terms/{word}" index="{idx}"/>'
                       for idx,word in enumerate(keys,1))
    xml=(
      '<archive xmlns="http://rs.tdwg.org/dwc/text/">'
      '<core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>event.tsv</location></files>'
      '<id index="0"/>'+fields(event)+'</core>'
      '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
      '<files><location>occ.tsv</location></files><coreid index="0"/>'
      +fields(occurrence)+'</extension></archive>'
    )
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("meta.xml",xml)
        z.writestr("event.tsv","PRIVATE_22_PLOT_MADEIRA_NATIVE_DRY_SOURCE_SITE_VALUES")
        z.writestr("occ.tsv","PRIVATE_ENDANGERED_MADEIRA_DRY_SPIDER_SPECIES")
    return b.getvalue()

def test_valid_original_role_has_no_plot_taxon_or_origin_values_read():
    r=metadata_only(mock())
    assert r["status"]=="MADEIRA_SPIDER_NATURAL_HABITAT_ORIGIN_META_ELIGIBLE_RESPONSES_CLOSED"
    assert r["source_candidate_fields"]["author_plot_field"]==["locationID"]
    assert r["source_candidate_fields"]["author_method_field"]==["samplingProtocol"]
    assert r["source_candidate_fields"]["author_taxon_origin_field"]==["establishmentMeans"]
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "PRIVATE_ENDANGERED" not in json.dumps(r)
    assert "PRIVATE_22_PLOT" not in json.dumps(r)

def test_missing_author_origin_fails_without_name_inference():
    r=metadata_only(mock(origin=False))
    assert r["status"]=="TERMINAL_MADEIRA_SPIDER_SOURCE_PLOT_OR_ORIGIN_META_MISSING"
    assert r["source_candidate_fields"]["author_taxon_origin_field"]==[]
    assert r["original_Occurrence_rows_opened"]==0

def test_absent_explicit_habitat_can_use_predefined_paper_plot_code_only_later():
    r=metadata_only(mock(habitat=False))
    assert r["status"]=="TERMINAL_MADEIRA_SPIDER_SOURCE_PLOT_OR_ORIGIN_META_MISSING"
    assert r["original_Event_rows_opened"]==0
