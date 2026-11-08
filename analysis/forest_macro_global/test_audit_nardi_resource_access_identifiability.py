"""Known-truth resource/connection design support without opening beetle observations."""
import importlib.util,math
from pathlib import Path
import pytest

src=Path(__file__).with_name("audit_nardi_resource_access_identifiability.py")
spec=importlib.util.spec_from_file_location("resource_access_support",src)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def rows(kind):
    data=[]
    for k in range(13):
        site=f"NEVER_EXPORT_SITE_{k}"
        n=15 if k==0 else 16
        for i in range(n):
            # Same composition every 2 cells, free angular barrier variation
            # within each cover bin in independently varying sources.
            comp=10+(i//2)*10
            if kind=="separable":
                conf=20+(i%2)*50 + 2*k
            elif kind=="collinear":
                conf=2*comp+0.01*(i%2)
            elif kind=="flat":
                conf=30
            else:
                raise AssertionError(kind)
            urban=math.sqrt((100-comp)**2+(100-conf)**2)
            data.append({"SITE":site,"CELL_ID":f"NEVER_EXPORT_CELL_{i}",
                         "composition":str(comp),"configuration":str(conf),
                         "urbanization_index":str(urban)})
    assert len(data)==207
    return data

def test_separable_resource_and_access_has_independent_same_cover_contrasts():
    out=m.analyze(rows("separable"))
    assert out["original_study_trap_cell_count"]==207
    assert out["original_landscape_context_count"]==13
    assert out["source_landscapes_with_discordant_tree_cover_and_barrier_pairs"]==13
    assert out["two_covar_separable_in_original_observed_feature_support"]
    assert out["landscape_centered_configuration_variance_retained_after_cover_regression"]>.95
    assert out["sources_sampling_effort_and_beetle_incidence_NOT_READ"]
    assert out["new_arthropod_effect_calculated"] is False
    assert "NEVER_EXPORT_SITE" not in str(out)
    assert "NEVER_EXPORT_CELL" not in str(out)

def test_resource_access_collinearity_produces_gate_not_positive_ecology():
    out=m.analyze(rows("collinear"))
    assert not out["two_covar_separable_in_original_observed_feature_support"]
    assert out["source_landscapes_with_discordant_tree_cover_and_barrier_pairs"]==0
    assert out["landscape_centered_configuration_variance_retained_after_cover_regression"]<.01

def test_flat_barriers_non_estimable_and_duplicate_stops():
    with pytest.raises(ValueError,match="source_zero_within_site_feature_variance"):
        m.analyze(rows("flat"))
    data=rows("separable")
    data[0]["CELL_ID"]=data[1]["CELL_ID"]
    with pytest.raises(ValueError,match="duplicated_original_trap_context_cell"):
        m.analyze(data)
