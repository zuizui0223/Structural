#!/usr/bin/env python3
"""Response-free published-methods eligibility; never reads observation rows."""
import json
import argparse
from pathlib import Path

def classify(x):
    c=x["frozen_design"]["castorani"]
    w=x["frozen_design"]["wanner"]
    geometry_future=c["patch_definition_uses_kelp_1984_to_2011"] and c["patch_definition_end_year"]>=c["example_forward_cutoff_year"]
    zero_proxy=c["assumes_zero_fecundity_when_no_canopy"] and not c["independent_patch_fecundity_failure_measured"]
    selected=w["published_ever_kelp_cells"]<w["predefined_physical_cells"] and not w["cutoff_specific_inclusion_proven"]
    return {
      "fresh_469_patch_forecast":"STOP_FUTURE_DEFINED_GEOMETRY" if geometry_future else "REQUIRE_OTHER_GATES",
      "fresh_117_cell_forecast":"STOP_BIOLOGICALLY_SELECTED_RISK_SET" if selected else "REQUIRE_OTHER_GATES",
      "independent_reproductive_failure":"STOP_CANOPY_DERIVED_PROXY" if zero_proxy else "REQUIRE_OTHER_GATES",
      "cross_grain_2017_2024":"STOP_NO_JOIN_CROSSWALK" if not x["evidence_boundaries"]["cross_grain_patch_cell_crosswalk_verified"] else "REQUIRE_OTHER_GATES",
      "retrospective_methods_only":"PERMITTED_AS_PUBLISHED_CONTEXT_NOT_NEW_CONFIRMATION",
      "biology_values_opened":0,
      "new_ecological_score":None
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("ledger",type=Path)
    a=p.parse_args()
    x=json.loads(a.ledger.read_text(encoding="utf-8"))
    if x["schema"]!="structural.kelp_temporal_source_ontology.v1_205":
        p.error("wrong schema")
    print(json.dumps(classify(x),sort_keys=True,indent=2))
