"""Synthetic DwC-A archive tests: never decode island × taxon values."""
import io
import zipfile
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_2016_dwca_structure_v1_267 import summarize_archive

NS="http://rs.tdwg.org/dwc/text/"


def fake_dwca(with_distribution=True):
    b=io.BytesIO()
    ext=(
        '<extension rowType="http://rs.gbif.org/terms/1.0/Distribution">'
        '<files><location>distribution.txt</location></files>'
        '<coreid index="0"/>'
        '<field index="1" term="http://rs.tdwg.org/dwc/terms/locality"/>'
        '<field index="2" term="http://rs.tdwg.org/dwc/terms/occurrenceStatus"/>'
        '</extension>' if with_distribution else ""
    )
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("meta.xml",f'''<?xml version="1.0"?>
            <archive xmlns="{NS}" metadata="eml.xml">
                <core rowType="http://rs.tdwg.org/dwc/terms/Taxon">
                    <files><location>taxon.txt</location></files>
                    <id index="0"/>
                    <field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
                    <field index="2" term="http://rs.tdwg.org/dwc/terms/taxonRank"/>
                </core>
                {ext}
            </archive>''')
        z.writestr("eml.xml","<eml><dataset><title>Azorean terrestrial checklist</title></dataset></eml>")
        z.writestr("taxon.txt","a\\tDO_NOT_DECODE_THIS_SPECIES\\tspecies\\n")
        if with_distribution:
            z.writestr("distribution.txt","a\\tDO_NOT_DECODE_ISLAND\\tpresent\\n")
    return b.getvalue()


def test_archive_inventory_reports_original_schema_not_species_rows():
    report=summarize_archive(fake_dwca(),expected_gbif_uuid="ec1a0bfb-7d8e-4c6b-bc4d-dfd68a1e844f")
    assert report["core"]["rowtype"].endswith("/Taxon")
    assert report["core"]["record_path"]=="taxon.txt"
    assert len(report["extensions"])==1
    assert report["extensions"][0]["record_path"]=="distribution.txt"
    assert report["potential_island_distribution_extension"] is True
    assert report["source_taxon_distribution_rows_decoded"]==0
    assert report["source_biological_record_bytes_read"]==0
    assert "DO_NOT_DECODE" not in str(report)


def test_archive_without_island_distribution_flags_incomplete():
    report=summarize_archive(fake_dwca(False),expected_gbif_uuid="ec1a0bfb-7d8e-4c6b-bc4d-dfd68a1e844f")
    assert report["potential_island_distribution_extension"] is False
    assert report["source_taxon_distribution_rows_decoded"]==0


def test_invalid_zip_and_missing_meta_fail():
    for raw in (b"<html>Blocked</html>",b"PK\\x03\\x04short"):
        try:
            summarize_archive(raw,"dummy")
        except ValueError:
            pass
        else:
            assert False,"Unverified source ZIP accepted"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("taxon.txt","bad")
    try:
        summarize_archive(b.getvalue(),"dummy")
    except ValueError:
        pass
    else:
        assert False,"Source archive without meta.xml must fail"


def test_species_tsv_must_not_be_used_to_fake_island_metadata():
    with zipfile.ZipFile(io.BytesIO(fake_dwca(False))) as z:
        names=z.namelist()
        assert "taxon.txt" in names
    report=summarize_archive(fake_dwca(False),"dummy")
    assert report["potential_island_distribution_extension"] is False
