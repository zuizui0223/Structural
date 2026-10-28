"""No original biological source rows: fixed ridge + plot-unit stress-test fixture."""
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))

from azores_MOVECLIM_richness_adjusted_v1_282 import fixed_ridge_residual, audit_adjusted
from test_azores_MOVECLIM_introduced_pressure_v1_281 import fixture


def test_fixed_ridge_constant_covariate_becomes_intercept_residual():
    residual,fit=fixed_ridge_residual([0,1,2,3],[1,1,1,1],[4,4,4,4])
    assert residual == [-1.5,-0.5,0.5,1.5]
    assert fit["slope_standardized_elevation"] == 0
    assert fit["slope_standardized_native_richness"] == 0
    assert fit["lambda"] == 1.0


def test_fixed_ridge_two_continuous_predictors_center_and_finite():
    resid,fit=fixed_ridge_residual([0,1,1,2],[0,1,2,3],[2,5,2,5])
    assert len(resid)==4
    assert abs(sum(resid))<1e-9
    assert all(math.isfinite(v) for v in resid)
    assert math.isfinite(fit["slope_standardized_elevation"])
    assert math.isfinite(fit["slope_standardized_native_richness"])


def test_synthetic_original_v281_reconciled_without_species_export():
    result=audit_adjusted(*fixture(),expected_plots=8,expected_events=32)
    assert result["status"]=="RETROSPECTIVE_RICHNESS_ELEVATION_STRESS_TEST_COMPLETED"
    assert result["independent_plots"]==4
    assert result["focal_native_taxa"]==2
    assert result["reference_native_taxa"]==5
    assert result["focal_species_plot_positives"]==4
    assert result["other_native_species_plot_positives"]==10
    assert result["introduced_species_plot_positives"]==4
    assert result["original_v281_primary_focal_minus_reference"]==-1
    assert math.isfinite(result["focal_minus_reference_richness_elevation_adjusted"])
    assert result["not_independent_fresh_confirmatory"]
    assert result["not_a_causal_effect_or_true_refuge"]
    assert result["not_observed_dispersal_colonization_rescue"]
    assert not result["eBird_used"]
    assert "Alpha alba" not in json.dumps(result)
    assert "Pico.plot" not in json.dumps(result)


def test_design_change_to_ridge_lambda_rejected():
    try:
        fixed_ridge_residual([0,1,2,3],[0,1,2,3],[4,3,2,1],lam=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Slope penalty cannot be tuned after seeing outcome")
