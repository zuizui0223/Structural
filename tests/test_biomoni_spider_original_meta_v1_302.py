"""Never open original spider Event/Occurrence body at source intake."""
import io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from biomoni_spider_original_meta_v1_302 import inventory
def fake(has_location=True):
    ef=["island","decimalLatitude","decimalLongitude","eventDate","samplingProtocol"]+(["locationID"] if has_location else [])
    of=["scientificName","taxonRank"]
    def fs(x):return ''.join(f'<field term="http://rs.tdwg.org/dwc/terms/{name}" index="{i}"/>' for i,name in enumerate(x,1))
    meta='<archive xmlns="http://rs.tdwg.org/dwc/text/"><core rowType="http://rs.tdwg.org/dwc/terms/Event"><id index="0"/><files><location>event.txt</location></files>'+fs(ef)+'</core><extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><coreid index="0"/><files><location>occurrence.txt</location></files>'+fs(of)+'</extension></archive>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("event.txt","PRIVATE_SITE_MUST_NEVER_OPEN")
        z.writestr("occurrence.txt","PRIVATE_SPIDER_TAXON_MUST_NEVER_OPEN")
    return out.getvalue()
def test_source_roles_and_original_data_firewall():
    r=inventory(fake())
    assert r["status"]=="SPIDER_ORIGINAL_SCHEMA_ELIGIBLE_EVENT_AND_OCCURRENCE_STILL_SEALED"
    assert r["original_Event_rows_opened"]==r["original_Occurrence_rows_opened"]==0
    assert "PRIVATE_SITE" not in json.dumps(r)
    assert "PRIVATE_SPIDER" not in json.dumps(r)
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
def test_missing_physical_plot_column_scientific_stop():
    r=inventory(fake(has_location=False))
    assert r["status"]=="SPIDER_SOURCE_SCHEMA_TERMINAL"
    assert r["missing_required_Event"]==["locationID"]
    assert r["bio_values_or_site_names_read"]==0
