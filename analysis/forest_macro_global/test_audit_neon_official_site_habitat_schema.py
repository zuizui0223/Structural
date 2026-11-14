"""Original NEON 2026 field-site CSV schema audit tests."""
import importlib.util
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_neon_official_site_habitat_schema.py")
spec=importlib.util.spec_from_file_location("neon_site_habitat_header",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def original_fake():
    rows=["siteCode,dominantVegetation,siteType,nlcdDominantClass,other"]
    for i in range(81):
        a="Mixed Forest" if i%3==0 else "Grassland"
        rows.append(f"S{i:03d},{a},CORE,{a},other")
    return ("\n".join(rows)+"\n").encode()

def test_neon_original_field_metadata_can_identify_forest_label_before_species():
    r=m.identify(original_fake())
    assert r["original_record_rows"]==81
    assert r["original_source_sha256"]
    assert r["forest_habitat_sites_verified"]==0
    assert r["species_plot_or_temperature_effect_not_scored"]
    assert r["source_fields_relevant_to_habitat_eligibility"]["dominantVegetation"]["distinct_nonempty_values"]==2
    assert r["original_row_values_siteIDs_coordinates_not_exported"]
    assert "S001" not in str(r)

def test_html_or_short_error_page_cannot_be_original_metadata():
    with pytest.raises(ValueError):
        m.identify(b"<html>"*120)
    with pytest.raises(ValueError):
        m.identify(b"short")
