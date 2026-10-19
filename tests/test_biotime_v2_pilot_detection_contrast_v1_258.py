"""Response-free exact recomputation of the source-count / detection contrast."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"development/biotime_v2_pilot_detection_continuity_contrast_v1_258.json"
SOURCE=ROOT/"development/biotime_v2_burned_pilot_by_study_source_group_v1_252.csv"

def audit():
    target=json.loads(FROZEN.read_text(encoding="utf-8"))
    with SOURCE.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    totals={k:{field:0 for field in ("n00","n01","n10","n11")} for k in ("1",">=5")}
    for row in rows:
        if row["source_group"] not in totals:continue
        for k in totals[row["source_group"]]:
            totals[row["source_group"]][k]+=int(row[k])
    a,b=totals["1"],totals[">=5"]
    n_or=(b["n01"]/b["n00"])/(a["n01"]/a["n00"])
    p_or=(b["n11"]/b["n10"])/(a["n11"]/a["n10"])
    return target,totals,n_or,p_or

def test_frozen_unweighted_counts_match_observed_aggregate():
    r,groups,_,_=audit()
    assert sum(int(groups[g]["n00"]+groups[g]["n01"]+groups[g]["n10"]+groups[g]["n11"]) for g in groups)>0
    for g in ("1",">=5"):
        for k,value in groups[g].items():
            assert value==r["groups"][g][k]

def test_gradients_and_numerical_direction_match_before_science_claim():
    r,groups,n_or,p_or=audit()
    assert abs(n_or-r["comparison"]["new_detection_5plus_vs_1_odds_ratio"])<1e-12
    assert abs(p_or-r["comparison"]["continued_detection_5plus_vs_1_odds_ratio"])<1e-12
    assert p_or>n_or
    assert r["comparison"]["pilot_study_ids_with_both_continuity_denominators"]==13
    assert r["comparison"]["study_persistence_positive"]==13
    assert r["comparison"]["stable_prior_detected_denominator_count"]==7
    assert r["protected_response"]["reserved_76_study_taxon_rows_opened"]==0
    assert r["interpretation"]["no_network_topology_effect_measured"]
