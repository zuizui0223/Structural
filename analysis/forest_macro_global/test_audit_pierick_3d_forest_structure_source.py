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
