"""BALA 7-island source ZIP source-only schema firewall regressions."""
import sys,io,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_original_metadata_only_v1_310 import parse_source
def fake(*,with_order=True,with_origin=True):
    event=["eventID","eventDate","samplingProtocol","island","locationID","decimalLatitude"]
    occ=["scientificName"]+(["order"] if with_order else [])+(["establishmentMeans"] if with_origin else [])
    def fs(vals):return "".join(
      '<field index="'+str(i)+'" term="http://rs.tdwg.org/dwc/terms/'+x+'"/>'
      for i,x in enumerate(vals,1))
    meta=('<archive xmlns="http://rs.tdwg.org/dwc/text/">'
      '<core rowType="http://rs.tdwg.org/dwc/terms/Event">'
      '<files><location>event.tsv</location></files><id index="0"/>'+fs(event)+'</core>'
      '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
      '<files><location>occ.tsv</location></files><coreid index="0"/>'+fs(occ)+'</extension></archive>')
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("event.tsv","SECRET_BALA_ISLAND_SITE_NEVER_READ")
        z.writestr("occ.tsv","SECRET_BALA_SPECIES_AND_ORIGIN_NEVER_READ")
    return buf.getvalue()
def test_valid_role_schema_does_not_open_taxon_or_event_values():
    r=parse_source(fake())
    assert r["status"]=="META_ELIGIBLE_EVENT_VALUES_STILL_CLOSED"
    assert r["source_Event_rows_opened"]==r["source_Occurrence_rows_opened"]==0
    assert r["same_site_three_campaigns_not_yet_verified"] is True
    assert r["role_qualifiers"]["taxon_origin_field_candidate"] is True
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]
    for word in ["SECRET_BALA_ISLAND_SITE_NEVER_READ","SECRET_BALA_SPECIES_AND_ORIGIN_NEVER_READ"]:
        assert word not in json.dumps(r)
def test_no_order_field_is_metadata_only_scientific_stop():
    r=parse_source(fake(with_order=False))
    assert r["status"]=="META_HOLD_MISSING_TEMPORAL_OR_GUILD_ROLE"
    assert r["role_qualifiers"]["guild_order_field"] is False
    assert r["source_Occurrence_rows_opened"]==0
def test_no_origin_field_is_metadata_only_stop():
    r=parse_source(fake(with_origin=False))
    assert r["status"]=="META_HOLD_MISSING_TEMPORAL_OR_GUILD_ROLE"
    assert r["role_qualifiers"]["taxon_origin_field_candidate"] is False
    assert r["source_Event_rows_opened"]==0
