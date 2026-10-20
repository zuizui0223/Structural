"""Verify the two new 2020+ Azores PRIBES original source schemas WITHOUT reading taxa."""
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_pribes_modern_source_preflight_v1_270 import inspect_publisher_archive

NS="http://rs.tdwg.org/dwc/text/"
DWC="http://rs.tdwg.org/dwc/terms/"
GBIF="http://rs.gbif.org/terms/1.0/"

def sample_archive(occurrence=True):
    x=io.BytesIO()
    ext=f'''<extension rowType="{DWC}Occurrence" encoding="UTF-8">
        <files><location>occurrence.txt</location></files><coreid index="0"/>
        <field index="1" term="{DWC}scientificName"/>
        <field index="2" term="{DWC}occurrenceStatus"/>
      </extension>''' if occurrence else ""
    with zipfile.ZipFile(x,"w") as z:
        z.writestr("meta.xml",f'''<archive xmlns="{NS}">
        <core rowType="{DWC}Event" encoding="UTF-8">
          <files><location>event.txt</location></files><id index="0"/>
          <field index="1" term="{DWC}eventDate"/>
          <field index="2" term="{DWC}island"/>
        </core>{ext}
        </archive>''')
        z.writestr("event.txt","X1\\t2020-08-04\\tPico\\nSECRET_OBSERVATION\\n")
        if occurrence:
            z.writestr("occurrence.txt","X1\\tSECRET_SPECIES\\tpresent\\n")
    return x.getvalue()

def test_source_archive_verifies_event_occurrence_schema_no_record_bytes():
    r=inspect_publisher_archive(sample_archive(),"fixture")
    assert r["event_core"] is True
    assert r["occurrence_extension"] is True
    assert r["author_has_island_field"] is True
    assert r["author_has_eventDate_field"] is True
    assert r["author_has_scientificName_field"] is True
    assert r["event_and_occurrence_fields_eligible"] is True
    assert r["biological_event_occurrence_rows_decoded"]==0
    assert "SECRET" not in str(r)

def test_missing_source_occurrence_extension_does_not_pass():
    r=inspect_publisher_archive(sample_archive(False),"fixture")
    assert not r["event_and_occurrence_fields_eligible"]

def test_malformed_source_zip_rejected():
    try:
        inspect_publisher_archive(b"<html>error</html>","bad")
    except ValueError:
        pass
    else:
        raise AssertionError("Do not accept HTML as a published source archive")
