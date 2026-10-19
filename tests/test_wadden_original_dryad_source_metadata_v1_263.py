"""Dryad original version metadata checks using fake source JSON, no plant response data."""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from wadden_original_dryad_source_metadata_v1_263 import (
  _choose_latest_version, validate_source, _original_get_json, SourceStop
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=json.loads((ROOT/"development/wadden_experimental_island_source_protocol_v1_263.json").read_text())
FILES=CONTRACT["source"]["expected_min_version_files"]

def fake_files():
    return {"_embedded":{"stash:files":[
        {"id":9000+i,"path":name,"size":12000+i,
         "digest":"md5:"+f"{i:032d}"} for i,name in enumerate(FILES)
    ]}}

def test_latest_original_version_selection_and_five_metadata_only_files():
    versions={"_embedded":{"stash:versions":[
      {"id":100,"versionNumber":1},{"id":107,"versionNumber":2}]}}
    assert _choose_latest_version(versions)==((2,107),2)
    result=validate_source({"doi":"10.5061/dryad.gxd2547z3"},versions,fake_files(),CONTRACT)
    assert result["status"]=="ORIGINAL_DRYAD_FILE_METADATA_IDENTIFIED_NO_BIOLOGY"
    assert result["original_version_id"]==107
    assert set(result["required_source_files"])==set(FILES)
    assert result["actual_seed_trap_or_plant_presence_rows_read"]==0
    assert result["one_field_landscape_not_twelve_independent_archipelagos"]
    assert "species_value" not in str(result)

def test_2026_seed_trap_file_is_required_for_current_primary_source():
    versions={"versions":[{"id":107,"versionNumber":2}]}
    files=fake_files()
    files["_embedded"]["stash:files"]=[r for r in files["_embedded"]["stash:files"]
                                      if r["path"]!="DynaCom_seed_trapping_experiment_2020_2021.csv"]
    try:
        validate_source({"doi":"10.5061/dryad.gxd2547z3"},versions,files,CONTRACT)
    except SourceStop as e:
        assert "missing expected" in str(e)
    else:
        raise AssertionError("Never accept stale dataset version lacking prior-known seed trap data")

def test_ambiguous_versions_or_biologically_relabelled_doi_fail_closed():
    versions={"versions":[{"id":107,"versionNumber":2},
                           {"id":108,"versionNumber":2}]}
    try:
        validate_source({"doi":"10.5061/dryad.gxd2547z3"},versions,fake_files(),CONTRACT)
    except SourceStop as e:
        assert "Ambiguous" in str(e)
    else: raise AssertionError("Duplicated version numbers should fail")
    try:
        validate_source({"doi":"10.5061/dryad.other"}, {"versions":[{"id":108,"versionNumber":2}]},
                        fake_files(),CONTRACT)
    except SourceStop as e:
        assert "DOI" in str(e)
    else: raise AssertionError("Mismatched DOI should fail")

def test_non_dryad_url_not_fetched():
    for url in ("https://example.com/api/v2/datasets/test",
                "http://datadryad.org/api/v2/datasets/test",
                "https://datadryad.org/auth/private"):
        try:_original_get_json(url)
        except SourceStop as e: assert "Unauthorized" in str(e)
        else:raise AssertionError("Must not follow unknown source routes")
