"""Synthetic metadata-only ZIP firewall regressions: every biological cell remains unread."""
from pathlib import Path
import io
import json
import sys
import zipfile
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from biomoni_three_island_opaque_schema_intake_v1_283 import schema_inventory_from_archive


def fixture(*, establishment=True, linkage=True, traversal=False):
    event_fields = ''.join(
        f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{name}"/>'
        for i,name in enumerate(["eventID","locationID","island"], start=1))
    occ = ["scientificName"] + (["establishmentMeans"] if establishment else [])
    occ_fields = ''.join(
        f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{name}"/>'
        for i,name in enumerate(occ,start=1))
    coreid = '<coreid index="0"/>' if linkage else ''
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<archive xmlns="http://rs.tdwg.org/dwc/text/" metadata="eml.xml">'
           '<core rowType="http://rs.tdwg.org/dwc/terms/Event" encoding="UTF-8">'
           '<files><location>event.txt</location></files><id index="0"/>'
           + event_fields + '</core>'
           '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence" encoding="UTF-8">'
           '<files><location>occurrence.txt</location></files>' + coreid +
           occ_fields + '</extension></archive>')
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        z.writestr("meta.xml",xml)
        # This secret MUST never appear in receipt output or extracted fields.
        z.writestr("event.txt","PRIVATE_ISLAND_NEEDED_NEVER_READ\n")
        z.writestr("occurrence.txt","PRIVATE_SPECIES_LABEL_NEVER_READ\n")
        if traversal:
            z.writestr("../unexpected.txt","broken")
    return out.getvalue()


def test_metadata_only_accepts_complete_declared_syntax_not_biology():
    result=schema_inventory_from_archive(fixture())
    assert result["status"]=="METADATA_SCHEMA_POSSIBLE_RESPONSE_SEALED_HOLD"
    assert result["data_files_opened"]==0
    assert result["Event_rows_opened"]==0
    assert result["Occurrence_rows_opened"]==0
    assert result["predictive_effects_scored"]==0
    assert result["new_confirmatory_systems"]==0
    assert result["Event_meta_only"]["id_index_declared"]
    assert result["Occurrence_meta_only"]["coreid_index_declared"]
    for marker in ("PRIVATE_ISLAND_NEEDED_NEVER_READ","PRIVATE_SPECIES_LABEL_NEVER_READ"):
        assert marker not in json.dumps(result)


def test_absent_native_alien_classification_stops_before_opening_biology():
    result=schema_inventory_from_archive(fixture(establishment=False))
    assert result["status"]=="STOP_REQUIRED_PLOT_OR_NATIVE_ALIEN_STATUS_SCHEMA_MISSING"
    assert result["missing_required_Occurrence_fields"]==["establishmentMeans"]
    assert result["data_files_opened"]==0


def test_missing_foreign_coreid_is_terminal_schema_stop():
    result=schema_inventory_from_archive(fixture(linkage=False))
    assert result["status"]=="STOP_NO_DECLARED_EVENT_OCCURRENCE_CORE_ID_JOIN"
    assert result["data_files_opened"]==0


def test_unsafe_extra_zip_member_rejected_before_any_body_read():
    with pytest.raises(ValueError,match="Unsafe archive path"):
        schema_inventory_from_archive(fixture(traversal=True))
