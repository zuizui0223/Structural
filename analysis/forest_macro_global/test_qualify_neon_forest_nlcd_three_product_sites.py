"""Known truth NEON official NLCD source site context and 3-product overlap."""
import csv,hashlib,importlib.util,io
from pathlib import Path
import pytest

p=Path(__file__).with_name("qualify_neon_forest_nlcd_three_product_sites.py")
spec=importlib.util.spec_from_file_location("neon_source_nlcd_forest",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fake():
    fields=["site_id","dominant_nlcd_classes","mean_canopy_height_m",
            "tower_height_m","number_tower_levels","domain_id","site_subtype"]
    rows=[]
    for i in range(81):
        status="Deciduous Forest|Evergreen Forest" if i<20 else (
            "Deciduous Forest|Grassland/Herbaceous" if i<30 else "Shrub/Scrub")
        rows.append(dict(site_id=f"S{i:03d}",dominant_nlcd_classes=status,
            mean_canopy_height_m="22.5",tower_height_m="30",number_tower_levels="5",
            domain_id=f"D{(i%10)+1:02d}",site_subtype="TERRESTRIAL"))
    buffer=io.StringIO()
    w=csv.DictWriter(buffer,fieldnames=fields)
    w.writeheader();w.writerows(rows)
    raw=buffer.getvalue().encode()
    month={
      "schema":"structural.NEON_forest_beetle_canopy_temperature_2026_product_metadata_support.v1",
      "original_NEON_release":"RELEASE-2026",
      "three_product_candidate_site_by_year_support":[
        dict(siteCode=f"S{i:03d}",three_product_same_calendar_months_count=(
            0 if i>=39 else 3),
             three_product_common_sample_year_count=(2 if i<15 else 1))
        for i in range(42)]}
    return raw,rows,month


def test_strict_forest_is_not_any_site_with_one_forest_class():
    assert m.nlcd_class("Evergreen Forest")=="STRICT_FOREST_ONLY_SOURCE_SITE"
    assert m.nlcd_class("Deciduous Forest|Evergreen Forest")=="STRICT_FOREST_ONLY_SOURCE_SITE"
    assert m.nlcd_class("Deciduous Forest|Grassland/Herbaceous")=="FOREST_MIXED_NONFOREST_NLCD_CONTEXT"
    assert m.nlcd_class("Woody Wetlands")=="WOODY_WETLAND_ONLY_SEPARATE"
    assert m.nlcd_class("Evergreen Forest|Woody Wetlands")=="FOREST_PLUS_WOODY_WETLANDS_SEPARATE"
    assert m.nlcd_class("Shrub/Scrub")=="NONFOREST_SOURCE_NLCD"


def test_landcover_site_scope_not_plot_level_forest_claim():
    raw,rows,manifest=fake()
    actual=m.table_rows(raw,expected_sha=hashlib.sha256(raw).hexdigest())
    assert len(actual)==81
    r=m.classify(actual,manifest)
    assert r["original_three_product_site_N"]==42
    assert r["strict_forest_only_dominant_NLCD_sites"]==20
    assert r["strict_forest_only_with_same_calendar_month_three_products"]==20
    assert r["strict_forest_only_with_2plus_sample_years"]==15
    assert r["strict_forest_only_with_positive_mean_canopy_height"]==20
    assert r["original_plot_scale_habitat_identity_qualified"]==0
    assert not r["actual_original_air_temperature_level_data_observed"]
    assert not r["original_NEON_biological_thermal_effect_scored"]
    assert r["NEON_ground_beetle_pitfall_not_an_insect_canopy_trap"]
    assert r["no_original_species_or_trap_ID_values_exported"]


def test_source_mapping_and_version_discrepancy_stops():
    raw,rows,manifest=fake()
    rows[0]["site_id"]="DIFFERENT"
    with pytest.raises(ValueError,match="missing_in_official_landcover"):
        m.classify(rows,manifest)
    with pytest.raises(ValueError,match="source_version_changed"):
        m.table_rows(raw,expected_sha="0"*64)
