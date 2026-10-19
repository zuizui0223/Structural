"""Pure probability algebra and frozen-summary eligibility tests; no heldout cells."""
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from occupancy_role_calibration_witness_v1_250 import (
    constant_probabilities, analyze,
)


def test_no_site_information_matches_each_signed_contrast_exactly():
    for dp,dn in [(.11643800501898788,-.005801435444703651),
                  (-.2774434469982346,.0004297992584762837),
                  (-.5962586684916777,.0002359552379291134)]:
        d=constant_probabilities(dp,dn)
        assert math.isclose(d["reconstructed_presence_C_minus_R3"],dp,abs_tol=1e-12)
        assert math.isclose(d["reconstructed_absence_C_minus_R3"],dn,abs_tol=1e-12)
        assert d["site_specific_source_discrimination"] is False
        assert 0<d["R3_constant_probability"]<1
        assert 0<d["C_constant_probability"]<1


def test_wrong_sign_pair_fails():
    try:
        constant_probabilities(.1,.001)
    except ValueError:
        pass
    else:
        raise AssertionError("Cannot construct opposed shift without opposed signs")


def test_pooled_summary_only_cannot_overturn_all_full_model_evidence():
    src=Path(__file__).resolve().parents[1]
    import json
    paths=[
      "development/global_mammals_prediction_behavior_freeze_v1_85.json",
      "development/global_mammals_sealed_species_result_freeze_v1_97.json",
      "development/global_mammals_ultrarare_result_freeze_v1_119.json"
    ]
    a,b,c=[json.loads((src/p).read_text(encoding="utf-8")) for p in paths]
    r=analyze(a,b,c)
    assert len(r["strata"])==3
    assert r["original_mammal_heldout_rows_opened"]==0
    assert r["new_confirmatory_systems"]==0
    assert r["GEB_scientific_HOLD"] is True
    actual=r["strata"]["higher_occupancy_exploratory_79"]["actual_full_model_ranking_metadata"]
    assert actual["ROC_AUC_C"] > actual["ROC_AUC_R3"]
    assert actual["average_precision_C"] < actual["average_precision_R3"]
