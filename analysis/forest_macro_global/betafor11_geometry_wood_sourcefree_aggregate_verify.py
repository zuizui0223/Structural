#!/usr/bin/env python3
"""Independent post-onepass arithmetic from six ANONYMOUS archived region means.

NO original OTU data or archived source numerical observations are opened.
The six aggregate means are copied from SHA-verified one-shot artifact only.
This does not independently reproduce R's 4000 bootstrap or 999 shuffles.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
import math
from pathlib import Path

ORIGINAL_RUN = 44735016332
ARTIFACT_ZIP_SHA256 = "9fbab085cf77b2051992056e13f5bf682e1d7c31001638443c56e0a01306b09b"
REGION_MEANS_SORTED = (
    -0.002129694250273442,
     0.002249868571373881,
     0.00649962758015532,
     0.01099966875261971,
     0.02838233786656228,
     0.02947185150129056,
)
SOURCE_G = 0.4067550823144644
SOURCE_W = 0.3941761389775097
SOURCE_D = 0.01257894333695472
SOURCE_REGION_EXACT_P = 0.0625
SOURCE_CI_95 = (0.003664900663959557,0.02238286478386816)
SOURCE_WITHIN_FOREST_LABEL_PERM_P = 0.006


def audit_aggregate_only():
    assert len(REGION_MEANS_SORTED) == 6
    assert sorted(REGION_MEANS_SORTED) == list(REGION_MEANS_SORTED)
    region_equal = sum(REGION_MEANS_SORTED)/6
    assert math.isclose(region_equal,SOURCE_D,abs_tol=1e-14,rel_tol=0.0)
    assert math.isclose(SOURCE_G-SOURCE_W,SOURCE_D,abs_tol=1e-14,rel_tol=0.0)
    all_64 = [
        sum(d*s for d,s in zip(REGION_MEANS_SORTED,sign))/6
        for sign in product((-1,1),repeat=6)
    ]
    count = sum(abs(v)>=abs(region_equal)-1e-12 for v in all_64)
    p_exact = count/len(all_64)
    assert count == 4 and len(all_64)==64
    assert math.isclose(p_exact,SOURCE_REGION_EXACT_P,rel_tol=0.0,abs_tol=1e-15)
    assert sum(v>0 for v in REGION_MEANS_SORTED)==5
    assert sum(v<0 for v in REGION_MEANS_SORTED)==1
    assert SOURCE_CI_95[0]>0 and SOURCE_CI_95[1]>SOURCE_CI_95[0]
    assert SOURCE_WITHIN_FOREST_LABEL_PERM_P != p_exact
    # This does NOT count 999 forest shuffles as 999 independent regions.
    # Their original permutation null draws are not in this anonymous
    # aggregate; p=.006 is original-score-derived and NOT re-estimated.
    support_gate = (
        SOURCE_D>0 and SOURCE_CI_95[0]>0 and p_exact<0.05
    )
    assert not support_gate
    return {
        "schema":"structural.BETAFOR11_sourcefree_original_aggregate_inference_audit.v1",
        "status":"PASS_SIX_REGION_MEAN_AND_EXACT_P_BUT_PRIMARY_GATE_NOT_SUPPORTED",
        "original_onepass_run":ORIGINAL_RUN,
        "original_zip_sha256":ARTIFACT_ZIP_SHA256,
        "original_biological_rows_reopened":0,
        "new_ecological_models_fitted":0,
        "previous_original_onepass_result_frozen":True,
        "regions_original_independent_conditional_units":6,
        "forests_nested_in_regions":11,
        "original_detected_OTUs_corrected":21114,
        "forest_source_g":SOURCE_G,
        "forest_source_w":SOURCE_W,
        "region_equal_g_minus_w_from_two_independent_paths":region_equal,
        "source_region_equal_g_minus_w":SOURCE_D,
        "six_region_exact_signflip_permutations":len(all_64),
        "exact_two_sided_as_extreme_count":count,
        "exact_two_sided_p_recomputed":p_exact,
        "region_signs_positive":5,
        "region_signs_negative":1,
        "original_R_4000_bootstrap_ci_reported_not_recomputed":SOURCE_CI_95,
        "original_within_forest_label_null_p_reported_not_recomputed":SOURCE_WITHIN_FOREST_LABEL_PERM_P,
        "fixed_exploratory_primary_support_criterion_met":support_gate,
        "not_meta_analysis":True,
        "not_global_forest_mechanism":True,
        "original_source_project_eBird_used":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    audit=audit_aggregate_only()
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(audit["status"])
    print("SOURCE_FREE_G_W_D",audit["region_equal_g_minus_w_from_two_independent_paths"])
    print("SOURCE_FREE_EXACT_P",audit["exact_two_sided_p_recomputed"])
    print("NEITHER_SIGNIFICANT_FOREST_LAW_NOR_NEW_BIOLOGY")


if __name__=="__main__":main()
