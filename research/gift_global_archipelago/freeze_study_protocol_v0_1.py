#!/usr/bin/env python3
"""Freeze the GIFT global-archipelago macro-study before any pilot response opens."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "structural.gift_global_archipelago_study_protocol.v0_1"
SCALES_KM = [25.0, 50.0, 125.0, 250.0]
CLIMATE = [
    "wc2.0_bio_30s_01",
    "wc2.0_bio_30s_05",
    "wc2.0_bio_30s_06",
    "wc2.0_bio_30s_12",
    "wc2.0_bio_30s_15",
]

def sha(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()

def load(path: Path) -> dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"{path} must contain an object")
    return value

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--universe",type=Path,required=True)
    p.add_argument("--intake-receipt",type=Path,required=True)
    p.add_argument("--environment-audit",type=Path,required=True)
    p.add_argument("--geology-crosswalk",type=Path,required=True)
    a=p.parse_args()

    u=load(a.universe)
    intake=load(a.intake_receipt)
    env=load(a.environment_audit)
    geology=load(a.geology_crosswalk)

    if u.get("response_values_accessed") is not False:
        raise RuntimeError("analysis universe is not response sealed")
    if u.get("species_composition_endpoint_called") is not False:
        raise RuntimeError("species composition was already opened")
    if intake.get("status") != "eligible_to_construct_v0_31_partition_protocol":
        raise RuntimeError("v0.10 intake did not pass")
    if intake.get("pilot_response_authorized") is not False:
        raise RuntimeError("intake unexpectedly authorized pilot response")
    if env.get("species_composition_accessed") is not False:
        raise RuntimeError("environment audit opened response")
    if geology.get("status") != "FROZEN_BEFORE_PILOT_RESPONSE":
        raise RuntimeError("geology crosswalk is not frozen pre-response")
    if geology.get("response_values_accessed") is not False:
        raise RuntimeError("geology crosswalk opened response")

    pilot=set(u["pilot_archipelagos"])
    confirm=set(u["confirmatory_archipelagos"])
    if not pilot or not confirm or pilot & confirm:
        raise RuntimeError("pilot/confirmatory archipelago partitions are invalid")

    pilot_lists=set()
    confirm_lists=set()
    for g in u["groups"]:
        target=pilot_lists if g["archipelago_id"] in pilot else confirm_lists
        for island in g["islands"]:
            target.update(str(x) for x in island["list_IDs"])
    if pilot_lists & confirm_lists:
        raise RuntimeError("pilot and confirmatory list surfaces overlap")

    protocol={
        "schema":SCHEMA,
        "status":"FROZEN_BEFORE_PILOT_RESPONSE",
        "system_id":"gift_global_archipelago_panel_v1",
        "gift_version":"3.2",
        "response_values_accessed":False,
        "pilot_response_opened":False,
        "confirmatory_response_opened":False,
        "parent_intake_fingerprint":intake["intake_fingerprint"],
        "analysis_universe_fingerprint":u["universe_fingerprint"],
        "geology_crosswalk_fingerprint":geology["crosswalk_fingerprint"],
        "evidence_partition":{
            "axis":"archipelago/list_ID response surface",
            "pilot_archipelagos":sorted(pilot),
            "confirmatory_archipelagos":sorted(confirm),
            "pilot_list_id_set_sha256":sha(sorted(pilot_lists,key=int)),
            "confirmatory_list_id_set_sha256":sha(sorted(confirm_lists,key=int)),
            "pilot_confirmatory_list_overlap":0,
            "reason":"GIFT checklist API returns complete list contents and cannot server-filter response rows by work_ID",
            "pilot_predictive_denominator_contribution":0,
        },
        "response_semantics":{
            "target":"native Angiosperm incidence within each eligible island checklist union",
            "presence":"1 when any eligible native-filtered checklist for the island returns the work_ID with questionable=0 and quest_native=0",
            "uncertain":"NA when occurrence/native status is only questionable; uncertain rows never become absences",
            "absence":"0 when the work_ID has no returned native occurrence in the eligible complete native-checklist union for that island and no questionable native record is present",
            "species_analysis_rule":"within each archipelago, analyze work_IDs with at least one unambiguous native presence; no selection may use candidate-minus-reference direction",
            "completeness_boundary":"complete_taxon + complete_floristic + native_indicated + suit_geo are required, but are treated as quality filters rather than a claim of perfect checklist completeness",
        },
        "heldout_design":{
            "unit":"island",
            "replication_unit_for_inference":"archipelago",
            "blocks_per_archipelago":4,
            "block_rule":u["spatial_holdout"]["algorithm"],
            "fitting_scope":"one independent species model per archipelago; species pools are never pooled across archipelagos",
            "fold_rule":"for each species and archipelago, hold out one frozen MST block and train on the other three",
        },
        "isolation_hypothesis":{
            "source":"development/prospective_extreme_isolation_topology_hypothesis_v0_3.json",
            "metric":"GIFT dist: coast-to-coast distance to nearest mainland excluding Antarctica",
            "primary_rule":u["extreme_rules"]["primary_q75"],
            "sensitivity_rules":[u["extreme_rules"]["sensitivity_q70"],u["extreme_rules"]["sensitivity_q80"]],
            "threshold_retuning_after_pilot_or_confirmatory_response":False,
        },
        "graph_operator":{
            "scope":"within archipelago only",
            "distance":"great-circle centroid distance",
            "primary_radii_km":SCALES_KM,
            "radii_inherited_from_frozen_A_Islands_R3":True,
            "post_response_scale_change_forbidden":True,
        },
        "reference_ladder":{
            "R0":CLIMATE,
            "R1":CLIMATE+[
                "log_area_km2","log1p_mainland_dist_km","nearest_training_presence_km"
            ],
            "R2":CLIMATE+[
                "log_area_km2","log1p_mainland_dist_km","nearest_training_presence_km",
                "multi_source_pressure","area_weighted_source_pressure"
            ],
            "R3":CLIMATE+[
                "log_area_km2","log1p_mainland_dist_km","nearest_training_presence_km",
                "multi_source_pressure","area_weighted_source_pressure",
                "SLMP","GMMC","nearest_other_island_km",
                "surrounding_island_pressure","surrounding_landmass_pressure",
                "unanchored_component_exposure","mainland_stepping_stone_frequency"
            ],
            "C_addition":"geography_only_eog_connected_frequency",
            "primary_contrast":"C minus R3 matched held-out Bernoulli log loss",
            "favourable_direction":"negative",
        },
        "feature_rules":{
            "multi_source_pressure":"mean_s log(1 + sum over permitted training-presence anchors a != focal of exp(-d(focal,a)/s))",
            "area_weighted_source_pressure":"mean_s log(1 + sum over permitted training-presence anchors a != focal of area_km2(a)*exp(-d(focal,a)/s))",
            "surrounding_island_pressure":"mean_s log(1 + sum over all other islands j in same archipelago of exp(-d(focal,j)/s))",
            "surrounding_landmass_pressure":"mean_s log(1 + sum over all other islands j in same archipelago of area_km2(j)*exp(-d(focal,j)/s))",
            "unanchored_component_exposure":"mean_s ((component_size(focal,s)-1)/(N_archipelago-1))",
            "mainland_stepping_stone_frequency":"fraction of primary-radius graphs where focal component contains an island with GIFT dist <= radius",
            "geography_only_eog_connected_frequency":"fraction of primary-radius graphs where focal component contains at least one permitted training-presence anchor other than focal",
            "training_row_self_anchor_exclusion":True,
            "heldout_labels_used_for_feature_construction":False,
        },
        "comparison_model":{
            "family":"deterministic L2-penalized logistic regression",
            "lambda":1.0,
            "intercept_penalized":False,
            "training_only_z_standardization":True,
            "class_weighting":"none",
            "hyperparameter_tuning":"none",
            "minimum_training_presences":5,
            "minimum_training_absences":5,
            "minimum_test_rows":3,
            "constant_predictor_policy":"drop only training-constant columns with sd<=1e-12; use identical retained columns on heldout rows",
            "constant_predictor_tolerance":1e-12,
        },
        "burned_pilot_gate":{
            "response_surface":"pilot archipelago list_IDs only",
            "model_fits_allowed":False,
            "effect_sizes_allowed":False,
            "prediction_scores_allowed":False,
            "audit_unit":"species x archipelago x frozen spatial block",
            "fold_estimable_rule":"training presence>=5 AND training absence>=5 AND heldout rows>=3",
            "species_archipelago_estimable_rule":"at least 3 of 4 folds estimable",
            "archipelago_estimable_rule":"at least 50 species satisfy species_archipelago_estimable_rule",
            "pass_rule":"all 3 pilot archipelagos estimable AND at least one passing extreme contributor AND at least one passing non-extreme contributor",
            "failure_rule":"STOP this study protocol version; do not retune thresholds/scales/reference and do not open confirmatory lists",
        },
        "H1_primary":{
            "question":"Is the topology increment more favourable on globally extreme-isolation islands?",
            "row_loss_increment":"heldout logloss(C)-heldout logloss(R3)",
            "within_species_archipelago_regime":"equal mean across matched heldout islands/folds",
            "within_archipelago_regime":"equal mean across contributing species",
            "archipelago_regime_minimum":"at least 3 frozen islands in that regime and at least 30 contributing species",
            "estimand":"equal-weight mean archipelago extreme-regime increment minus equal-weight mean archipelago non-extreme-regime increment",
            "favourable_direction":"negative",
            "inference":"10,000 whole-archipelago cluster bootstrap replicates; resample archipelagos as intact units and recompute both regime means",
            "bootstrap_seed":20260924,
            "paired_archipelago_sensitivity":"within-archipelago extreme minus non-extreme for archipelagos with both regimes; non-rescuing",
        },
        "H2_primary":{
            "question":"Does recent mainland-connection history modify the extreme-isolation topology increment?",
            "history_metric":"archipelago fraction of islands with GIFT GMMC=1",
            "analysis_population":"confirmatory archipelagos contributing an extreme-regime H1 summary",
            "estimand":"slope of archipelago extreme-regime C-R3 loss increment on GMMC-connected fraction",
            "prediction":"positive slope: topology becomes less favourable as the fraction historically connected to mainland increases",
            "inference":"archipelago bootstrap using the same whole-archipelago resamples as H1",
            "minimum_archipelagos":6,
            "nonestimable_is_neutral":True,
            "external_geological_type_secondary":{
                "source":"Roeble et al. 2024 Nature Communications Supplementary Data 3",
                "source_sha256":geology["source"]["xlsx_sha256"],
                "crosswalk_fingerprint":geology["crosswalk_fingerprint"],
                "classes":["continental","oceanic","mixed"],
                "confirmatory_quantitative_geology_eligible":geology["confirmatory_quantitative_geology_eligible"],
                "class_contrast_estimable_pre_response":geology["geology_h2_class_contrast_estimable"],
                "fraction_slope_estimable_pre_response":geology["geology_h2_fraction_slope_estimable"],
                "status":(
                    "confirmatory_secondary_authorized_pre_response"
                    if geology["geology_h2_fraction_slope_estimable"]
                    else "pre_response_nonestimable_secondary"
                ),
                "estimand":"slope of archipelago extreme-regime C-R3 increment on external oceanic fraction; class contrast continental vs oceanic only if >=3 pure confirmatory archipelagos per class",
                "inference":"whole-archipelago bootstrap; two-sided geological-history heterogeneity test",
                "role":"tests geological origin beyond the GIFT GMMC history gradient; cannot rescue H2 primary",
            },
        },
        "H3_secondary_confirmatory":{
            "trait":"GIFT Dispersal_syndrome_1",
            "exact_levels":["anemochorous","zoochorous","autochorous","hydrochorous","unspecialized"],
            "primary_grouping":{
                "limited_or_unspecialized":["autochorous","unspecialized"],
                "vector_assisted":["anemochorous","zoochorous","hydrochorous"],
            },
            "estimand":"H1 contrast in limited_or_unspecialized species minus H1 contrast in vector_assisted species",
            "prediction":"negative: topology dependence strengthens when direct/vector-assisted long-distance dispersal is less available",
            "five_level_heterogeneity":"secondary descriptive/omnibus; cannot rescue grouped H3",
            "missing_trait_policy":"exclude from H3 only, never from H1/H2",
            "inference":"two-way species x archipelago bootstrap of species-archipelago regime summaries",
            "nonestimable_is_neutral":True,
        },
        "M4_environmental_proxy":{
            "status":"embedded_in_primary_strong_reference",
            "current_climate_source":"GIFT 3.2 WorldClim 2.0 polygon means",
            "climate_layers":CLIMATE,
            "other_response_blind_reference":["area","dist","SLMP","GMMC","generic within-archipelago network context"],
            "claim_ceiling":"a residual topology increment is information beyond this declared environmental/isolation reference, not proof that every environmental proxy has been excluded",
        },
        "forbidden_after_pilot_open":[
            "change q75 primary threshold",
            "change graph radii",
            "weaken R3",
            "change lambda or class gates",
            "change archipelago minimum size",
            "replace archipelago/list evidence partition",
            "select taxa or archipelagos using C-R3 direction",
            "use pilot effects or scores",
            "reinterpret EOG as colonisation, persistence, or dispersal probability",
        ],
        "pilot_response_authorized":False,
        "confirmatory_response_authorized":False,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
