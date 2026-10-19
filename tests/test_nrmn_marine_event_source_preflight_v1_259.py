"""Source-only AODN Parquet metadata regression tests, no ecological rows."""
import io
import json
import sys
from pathlib import Path
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow.fs import FileInfo, FileType

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from nrmn_marine_event_source_preflight_v1_259 import audit, check_schema, SourceStop

CONTRACT=json.loads((ROOT/"development/nrmn_marine_event_source_protocol_v1_259.json").read_text())

def make_metadata(field_map):
    schema=pa.schema([(name,kind) for name,kind in field_map.items()])
    output=io.BytesIO()
    pq.write_metadata(schema,output)
    return output.getvalue()

def types_for(kind):
    expected=CONTRACT[f"expected_{kind}_fields"]
    return {name:(pa.int32() if name=="survey_id" else
                  pa.float32() if name in ("latitude","longitude") else
                  pa.string()) for name in expected}

class FakePublicS3:
    def __init__(self,fish_type=None):
        self.fish_type=fish_type
    def _blob(self,path):
        kind="survey" if "survey_metadata" in path else "fish"
        fields=types_for(kind)
        if kind=="fish" and self.fish_type is not None:
            fields["survey_id"]=self.fish_type
        return make_metadata(fields)
    def get_file_info(self,path):
        return FileInfo(path, type=FileType.File,size=len(self._blob(path)))
    def open_input_file(self,path):
        return io.BytesIO(self._blob(path))

def test_expected_source_survey_and_fish_schema_headers_only():
    result=audit(CONTRACT,inspector=FakePublicS3())
    assert result["status"]=="PASS_PUBLISHER_PUBLIC_METADATA_ONLY"
    assert result["strict_shared_survey_id_type"]=="int32"
    assert result["fish_species_abundance_rows_opened"]==0
    assert result["survey_event_rows_opened"]==0
    assert result["actual_multi_island_repeat_networks"]=="UNESTIMATED"

def test_unmatched_join_identifier_dtype_fails_before_response():
    with pytest.raises(SourceStop,match="discordant"):
        audit(CONTRACT,inspector=FakePublicS3(fish_type=pa.int64()))

def test_missing_required_original_metadata_field_fails_closed():
    fields=types_for("survey")
    del fields["site_code"]
    blob=make_metadata(fields)
    with pytest.raises(SourceStop,match="site_code"):
        check_schema(blob,CONTRACT["expected_survey_fields"])

def test_parquet_sidecar_source_does_not_contain_observation_rows():
    blob=make_metadata(types_for("fish"))
    summary=check_schema(blob,CONTRACT["expected_fish_fields"])
    assert summary["metadata_sidecar_bytes"]>0
    assert "species_name" in summary["field_names"]
    assert "total" in summary["field_names"]

def test_source_contract_rejects_noncanonical_dataset():
    altered=json.loads(json.dumps(CONTRACT))
    altered["authority"]["fish_dataset"]="custom_study_species_scores.parquet"
    with pytest.raises(SourceStop,match="identity"):
        audit(altered,inspector=FakePublicS3())
