"""Known-truth, original 207 sampling cell × 13 landscape source identity gate."""
import csv,hashlib,importlib.util,json
from collections import Counter
from pathlib import Path
import pytest

p=Path(__file__).with_name("qualify_eight_country_beetle_joins.py")
spec=importlib.util.spec_from_file_location("beetle_zenodo_site_joins",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def build_fake(tmp,unmatched_site_env=False):
    siteids=[f"PRIVATE_SITE_{i:02d}" for i in range(13)]
    cells=[(sid,f"PRIVATE_CELL_{j:03d}") for i,sid in enumerate(siteids)
           for j in range(15 if i==12 else 16)]
    assert len(cells)==207
    individuals=Counter()
    long=[]
    for z in range(3215):
        sid,cell=cells[z%207]
        species="SECRET_SPECIES_ALPHA" if z%2 else "SECRET_SPECIES_BETA"
        n=1
        long.append({"SITE":sid,"CELL_ID":cell,"SPECIES":species,
                     "STATUS":"known","N":str(n)})
        individuals[sid,cell,species]+=n
    w=[{"SITE":sid,"CELL_ID":cell,
        "SECRET_SPECIES_ALPHA":str(int(individuals[sid,cell,"SECRET_SPECIES_ALPHA"]>0)),
        "SECRET_SPECIES_BETA":str(int(individuals[sid,cell,"SECRET_SPECIES_BETA"]>0))}
       for sid,cell in cells]
    site=[{"plot_id":("UNMATCHED_"+sid if unmatched_site_env else sid),
            "forest_2000":str((i+1)*4),"forest_3000":str((i+1)*3),
            "forest_4000":str((i+1)*2)}
          for i,sid in enumerate(siteids)]
    trap=[{"SITE":sid,"CELL_ID":cell,"composition":"1.0",
           "configuration":"2.0","urbanization_index":"3.0"} for sid,cell in cells]
    arrays={"bio_cast":w,"bio_data_trapscale":long,
            "env_data_sitescale":site,"env_data_trapscale":trap}
    paths={}
    expected=dict(m.EXPECTED_MD5)
    for role,rows in arrays.items():
        path=tmp/(role+".txt")
        with path.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t")
            writer.writeheader();writer.writerows(rows)
        m.EXPECTED_MD5[role]=hashlib.md5(path.read_bytes()).hexdigest()
        paths[role]=path
    return paths,expected


def restore(original):
    m.EXPECTED_MD5.clear();m.EXPECTED_MD5.update(original)


def test_all_207_bio_cells_match_environment_and_site_rows_by_values(tmp_path):
    path,original=build_fake(tmp_path)
    try:
        r=m.run(path["bio_cast"],path["bio_data_trapscale"],
                path["env_data_sitescale"],path["env_data_trapscale"],tmp_path/"out")
    finally:restore(original)
    assert r["original_sampled_landscapes_n"]==13
    assert r["sampling_CELL_ID_SITE_pairs_unique"]==207
    assert r["original_bio_long_rows"]==3215
    assert r["landscape_env_plot_id_and_biological_SITE_values_exact_match"] is True
    assert r["site_environment_join_status"]=="DIRECT_13_LANDSCAPE_ID_EQUIVALENCE"
    assert r["source_beetle_long_unique_species_LABELS_not_verified_species_richness"]==2
    assert r["source_long_species_field_matches_wide_headers_all"]
    assert r["source_bio_wide_0_1_incidence_matrix_semantics_confirmed"] is True
    assert r["source_0_1_and_long_positive_species_incidence_disagreements"]==0
    assert r["source_wide_nonzero_cell_species_incidence_count"]==414
    assert r["original_long_N_sum_NOT_VERIFIED_SAMPLING_EFFORT"]==3215
    assert r["original_wide_raw_numeric_sum_NOT_ASSUMED_INDIVIDUALS"]==414
    assert r["original_independent_forest_patches_count_verified"]==0
    assert r["species_source_occupancy_or_connectivity_model_fit"] is False
    report=(tmp_path/"out"/"zenodo_beetle_original_site_and_trap_join.json").read_text()
    for secret in ("PRIVATE_SITE","PRIVATE_CELL","SECRET_SPECIES"):
        assert secret not in report


def test_nonmatching_plot_id_is_safe_stop_not_join_by_row_order(tmp_path):
    p,original=build_fake(tmp_path,unmatched_site_env=True)
    try:
        r=m.run(p["bio_cast"],p["bio_data_trapscale"],
                p["env_data_sitescale"],p["env_data_trapscale"],tmp_path/"out")
    finally:restore(original)
    assert not r["landscape_env_plot_id_and_biological_SITE_values_exact_match"]
    assert r["landscape_env_SITE_join_unmatched_source_code_count"]==13
    assert r["site_environment_join_status"]=="STOP_REQUIRES_SOURCE_IDENTITY_CROSSWALK"


def test_duplicate_sample_cell_and_invalid_taxon_counts_stop(tmp_path):
    p,original=build_fake(tmp_path)
    try:
        b,fields=m.parse(p["bio_cast"],"bio_cast")
        b[1]["SITE"]=b[0]["SITE"];b[1]["CELL_ID"]=b[0]["CELL_ID"]
        a=m.parse(p["bio_data_trapscale"],"bio_data_trapscale")
        site=m.parse(p["env_data_sitescale"],"env_data_sitescale")
        trap=m.parse(p["env_data_trapscale"],"env_data_trapscale")
        with pytest.raises(ValueError,match="duplicate_source_cell_identity"):
            m.build((b,fields),a,site,trap)
        assert m.count_n("10")==10
        assert m.count_n("0")==0
        with pytest.raises(ValueError,match="nonnegative_integer"):
            m.count_n("-1")
    finally:restore(original)
