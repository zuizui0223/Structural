"""Four-table original 2026 Zenodo forest beetle source cohort checks."""
import csv,hashlib,importlib.util,json
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_nardi_multiregion_beetle_sources.py")
spec=importlib.util.spec_from_file_location("nardi_beetle_source",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def table(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as fd:
        w=csv.writer(fd,delimiter="\t")
        w.writerow(header)
        w.writerows(rows)


def fixture(tmp_path):
    paths={}
    tables={
      "bio_cast":(["Site","Trap","Species","Count"],[
          [f"SECRET_SITE_{i%13}",f"PRIVATE_TRAP_{i%15}","SECRET_SPECIES","2"] for i in range(110)]),
      "bio_data_trapscale":(["Site","Trap","Species","Count"],[
          [f"SECRET_SITE_{i%13}",f"PRIVATE_TRAP_{i%15}","SECRET_SPECIES","2"] for i in range(120)]),
      "env_data_sitescale":(["Site","TreeCover","Country"],[
          [f"SECRET_SITE_{i}","20","COUNTRY_X"] for i in range(13)]),
      "env_data_trapscale":(["Site","Trap","LocalTreeCover"],[
          [f"SECRET_SITE_{i%13}",f"PRIVATE_TRAP_{i%15}","20"] for i in range(120)]),
    }
    old=dict(m.EXPECTED_MD5)
    for name,(header,rows) in tables.items():
        f=tmp_path/(name+".txt")
        table(f,header,rows)
        paths[name]=f
        m.EXPECTED_MD5[name]=hashlib.md5(f.read_bytes()).hexdigest()
    return paths,old


def test_same_source_ids_only_candidates_not_verified_independent_forests(tmp_path):
    paths,old=fixture(tmp_path)
    try:
        q=m.run(paths["bio_cast"],paths["bio_data_trapscale"],
                paths["env_data_sitescale"],paths["env_data_trapscale"],tmp_path/"out")
    finally:
        m.EXPECTED_MD5.clear()
        m.EXPECTED_MD5.update(old)
    assert q["source_dataset_DOI"]=="10.5281/zenodo.17044394"
    assert q["candidate_shared_field_names_bio_vs_trap_env"]==["site","trap"]
    assert q["candidate_shared_field_names_bio_vs_site_env"]==["site"]
    assert q["source_tables"]["env_data_sitescale"]["source_row_count"]==13
    assert q["source_tables"]["bio_data_trapscale"]["source_row_count"]==120
    assert q["independent_original_plot_count_verified"]==0
    assert not q["site_trap_year_method_keys_verified"]
    assert q["not_an_insect_canopy_v_ground_vertical_data_source"]
    assert not q["new_source_topology_or_forestation_effect_scored"]
    actual=(tmp_path/"out"/"zenodo_eight_country_beetle_source_grain.json").read_text()
    assert "PRIVATE_TRAP" not in actual and "SECRET_SITE" not in actual
    assert "SECRET_SPECIES" not in actual
    assert q["raw_species_values_site_IDs_coordinates_not_exported"]


def test_source_md5_mismatch_does_not_become_invented_result(tmp_path):
    paths,old=fixture(tmp_path)
    try:
        f=paths["env_data_sitescale"]
        f.write_bytes(f.read_bytes()+b"# altered")
        with pytest.raises(ValueError,match="md5_version_changed"):
            m.audit(paths["bio_cast"],paths["bio_data_trapscale"],
                    paths["env_data_sitescale"],paths["env_data_trapscale"])
    finally:
        m.EXPECTED_MD5.clear()
        m.EXPECTED_MD5.update(old)


def test_malformed_original_rows_stop(tmp_path):
    paths,old=fixture(tmp_path)
    try:
        p=paths["bio_cast"]
        p.write_bytes(p.read_bytes()+b"BAD TAB ROW\n")
        m.EXPECTED_MD5["bio_cast"]=hashlib.md5(p.read_bytes()).hexdigest()
        with pytest.raises(ValueError,match="original_source_rows_empty_or_malformed"):
            m.audit(paths["bio_cast"],paths["bio_data_trapscale"],
                    paths["env_data_sitescale"],paths["env_data_trapscale"])
    finally:
        m.EXPECTED_MD5.clear()
        m.EXPECTED_MD5.update(old)
