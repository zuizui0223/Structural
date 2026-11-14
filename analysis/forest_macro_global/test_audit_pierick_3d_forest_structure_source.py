"""Response-unopened known-truth for Pierick source header and site grain."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_pierick_3d_forest_structure_source as p

def test_plot_identity_requires_correct_30_physical_original_keys():
    rows=[{"PlotID":f"P{i+1}","CanopyCover":"X","PlantRichness":"PRIVATE_RESPONSE"}
          for i in range(30) for _ in range(2)]
    x=p.source_grain(list(rows[0]),rows)
    assert x["original_plot_identity_distinct_source_label_count"]==30
    assert x["original_30_plot_grain_metadata_status"]=="AUTHOR_PLOT_COLUMN_CANDIDATE_AND_30_UNIQUE_LABELS"
    assert x["max_source_rows_per_canonical_plot_key"]==2
    assert "PRIVATE_RESPONSE" not in str(x)

def test_unknown_site_grain_fails_closed():
    rows=[{"Tree":str(i),"PlotName":f"P{i%3}"} for i in range(30)]
    x=p.source_grain(list(rows[0]),rows)
    assert x["original_30_plot_grain_metadata_status"]=="CANDIDATE_PLOT_LABEL_NOT_AUTHOR_VERIFIED"
    assert x["original_plot_identity_distinct_source_label_count"] is None

def test_fewer_original_plot_keys_do_not_become_30_independent_sites():
    rows=[{"plot_id":f"P{i%5}"} for i in range(30)]
    x=p.source_grain(list(rows[0]),rows)
    assert x["original_plot_identity_distinct_source_label_count"]==5
    assert x["original_30_plot_grain_metadata_status"]=="SCIENTIFIC_STOP_PLOT_KEY_CARDINALITY_NOT_30"

def test_header_based_trait_families_do_not_depend_on_biodiversity_values():
    keys=["PlotID","CanopyCover","LiDAR_height","Temp_heterogeneity",
          "soil_moisture","Hymenoptera_richness","Treatment","Date"]
    observed={k:[f for f in keys if __import__("re").search(pat,f)]
              for k,pat in p.PATTERNS.items()}
    assert "CanopyCover" in observed["canopy_structure"]
    assert "LiDAR_height" in observed["three_dimensional_structure_or_lidar"]
    assert "Temp_heterogeneity" in observed["microclimate_heterogeneity"]
    assert "Hymenoptera_richness" in observed["biodiversity_response_schema_ONLY"]
    assert "Treatment" in observed["source_management_or_treatment"]

def test_author_long_form_factor_grid_is_not_sample_size_or_microclimate_effect():
    fields=list(p.LONG_FORMAT_META)+["climhet_val","structure_val","div"]
    rows=[]
    for region in ("forest_region_1","forest_region_2"):
        for plot in range(15):
            for micro in ("temperature_sd","vpd_sd"):
                for structure in ("canopy_cover","lidar_height"):
                    for group in ("plants","hymenoptera"):
                        rows.append(dict(zip(fields,(
                            "P"+str(plot),"SECRET_"+region,micro,structure,
                            "control",group,"PRIVATE_TEMP","PRIVATE_STRUCTURE",
                            "PRIVATE_DIVERSITY"))))
    v=p.audit_long_format_metadata(fields,rows)
    assert v["long_format_design_status"]=="LONG_FORMAT_30_REGION_PATCH_KEYS_CANDIDATE"
    assert v["source_region_patch_unique_keys_NOT_certified_independent_forests"]==30
    assert v["source_unique_region_codes_NOT_independent_forest_studies"]==2
    assert v["source_unique_patch_codes"]==15
    assert v["source_observation_rows_NOT_independent_field_plots"]==240
    assert v["source_duplicate_original_factor_combination_rows"]==0
    assert v["original_biodiversity_div_values_NOT_READ"]
    assert v["original_structure_val_measurements_NOT_READ"]
    assert "PRIVATE_TEMP" not in str(v)
    assert "PRIVATE_DIVERSITY" not in str(v)
    assert "SECRET_forest_region_1" not in str(v)

def test_long_factor_grid_same_key_repeated_without_30_unique_stop():
    f=list(p.LONG_FORMAT_META)
    rows=[dict(zip(f,("P0","R0","T","H","M","plants"))) for _ in range(10)]
    v=p.audit_long_format_metadata(f,rows)
    assert v["long_format_design_status"]=="SCIENTIFIC_STOP_SOURCE_REGION_PATCH_COUNT_NOT_30"
    assert v["source_duplicate_original_factor_combination_rows"]==9
    assert v["source_region_patch_unique_keys_NOT_certified_independent_forests"]==1
