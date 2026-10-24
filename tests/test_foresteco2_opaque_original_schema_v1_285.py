"""ForestEco2 new-source XML only; source biology never decoded."""
from pathlib import Path
import io
import json
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
from foresteco2_opaque_original_schema_v1_285 import check_foresteco_schema
from test_biomoni_three_island_opaque_schema_intake_v1_283 import fixture


def create(*, habitat=True, rank=True):
    upstream=fixture()
    o=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(upstream)) as zin, zipfile.ZipFile(o,"w") as zout:
        for info in zin.infolist():
            b=zin.read(info.filename)
            if info.filename=="meta.xml":
                b=b.replace(b"</core>", (b'<field index="7" term="http://rs.tdwg.org/dwc/terms/habitat"/>' if habitat else b"")+b"</core>")
                if rank:
                    b=b.replace(b"</extension>", b'<field index="8" term="http://rs.tdwg.org/dwc/terms/taxonRank"/></extension>')
            zout.writestr(info.filename,b)
    return o.getvalue()


def test_good_qualified_schema_keeps_response_fully_sealed():
    r=check_foresteco_schema(create())
    assert r["status"]=="SCHEMA_QUALIFIED_BIOLOGICAL_RESPONSE_STILL_SEALED"
    assert r["frozen_first_available_forest_type_column"]=="habitat"
    assert r["source_dataset_uuid"]=="158e0f0d-26e3-4883-bf5e-6040c1bb1ff4"
    assert r["published_event_rows_claimed_not_verified"]==90
    assert r["publisher_method_paragraph_also_says_105_events"]
    assert r["Event_rows_opened"]==0
    assert r["Occurrence_rows_opened"]==0
    assert r["data_files_opened"]==0
    assert r["predictive_effects_scored"]==0
    assert r["biological_outcome_opened"] is False
    assert "PRIVATE_SPECIES_LABEL_NEVER_READ" not in json.dumps(r)


def test_missing_forest_type_declared_field_scientific_stop():
    r=check_foresteco_schema(create(habitat=False))
    assert r["status"]=="STOP_OR_HOLD_INCOMPLETE_FOREST_OR_TAXON_SCHEMA"
    assert r["frozen_first_available_forest_type_column"] is None
    assert r["Occurrence_rows_opened"]==0


def test_missing_taxon_rank_not_assumed_species():
    r=check_foresteco_schema(create(rank=False))
    assert r["status"]=="STOP_OR_HOLD_INCOMPLETE_FOREST_OR_TAXON_SCHEMA"
    assert r["data_files_opened"]==0


def test_foresteco_source_identity_is_not_biomoni_even_if_parser_reused():
    r=check_foresteco_schema(create())
    assert r["source_dataset_uuid"]!="eab982cf-81df-4d08-b9f4-c2f5c56b8ad3"
    assert "plants-azo-foresteco2&v=1.2" in r["source_archive_url"]
