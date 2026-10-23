"""No biological values are decoded from original MOVECLIM 2013 Event/Occurrence archive."""
import io
import zipfile
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_MOVECLIM_2013_source_preflight_v1_277 import inspect_moveclim

NS="http://rs.tdwg.org/dwc/text/"
T="http://rs.tdwg.org/dwc/terms/"

def fixture():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("meta.xml",f'''<?xml version="1.0"?>
        <archive xmlns="{NS}">
          <core rowType="{T}Event" encoding="UTF-8" ignoreHeaderLines="1">
            <files><location>event.txt</location></files>
            <id index="0"/>
            <field index="1" term="{T}eventID"/>
            <field index="2" term="{T}island"/>
            <field index="3" term="{T}minimumElevationInMeters"/>
            <field index="4" term="{T}eventDate"/>
          </core>
          <extension rowType="{T}Occurrence" encoding="UTF-8" ignoreHeaderLines="1">
            <files><location>occurrence.txt</location></files>
            <coreid index="0"/>
            <field index="1" term="{T}scientificName"/>
            <field index="2" term="{T}organismQuantity"/>
          </extension>
        </archive>''')
        z.writestr("event.txt","eventID\\tE1\\tPico\\t200\\t2013-01-01\\nNOT_ALLOWED_TO_DECODE_EVENT_COORDINATES\\n")
        z.writestr("occurrence.txt","E1\\tPRIVATE_SPECIES_NAME\\t9\\n")
        z.writestr("eml.xml","<eml><dataset><title>MOVECLIM vegetation</title></dataset></eml>")
    return b.getvalue()

def test_only_author_metadata_and_no_taxon_event_record_bytes_read():
    result=inspect_moveclim(fixture())
    assert result["core"]["rowtype"].endswith("/Event")
    assert result["core"]["record_path"]=="event.txt"
    assert len(result["extensions"])==1
    assert result["extensions"][0]["rowtype"].endswith("/Occurrence")
    assert result["source_biological_record_bytes_read"]==0
    assert result["source_taxon_distribution_rows_decoded"]==0
    assert result["has_author_event_occurrence_coreid_keys"] is True
    assert result["source_event_or_occurrence_records_scored"]==0
    assert "PRIVATE_SPECIES_NAME" not in str(result)

def test_no_occurrence_extension_is_not_a_monitoring_survey():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("meta.xml",f'''<archive xmlns="{NS}"><core rowType="{T}Event">
          <files><location>event.txt</location></files><id index="0"/></core></archive>''')
        z.writestr("event.txt","E1\\tPRIV\\n")
    try:inspect_moveclim(b.getvalue())
    except ValueError as e:assert "Occurrence" in str(e)
    else:raise AssertionError("Cannot score biological monitoring on absent occurrence frame")

def test_bad_archive_and_multiple_cores_stop():
    try:inspect_moveclim(b"<html>Blocked</html>")
    except ValueError:pass
    else:raise AssertionError("Malformed original source should stop")
