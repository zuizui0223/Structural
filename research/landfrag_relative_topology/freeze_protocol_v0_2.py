#!/usr/bin/env python3
"""Freeze LandFrag response parsing and H1 inference before abundance access."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BOOTSTRAP_REPS=10000
BOOTSTRAP_SEED=20260925
MIN_RESPONSE_CLUSTERS=30
EXPECTED_ABUNDANCE_COLUMNS=[
    "id","refshort","fragment_id","plot_id","scientific_name","abundance","tsn","taxon"
]

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain object")
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",type=Path,required=True)
    ap.add_argument("--precision",type=Path,required=True)
    a=ap.parse_args()
    census=load(a.census); precision=load(a.precision)
    if census.get("schema")!="structural.landfrag_relative_topology_metadata.v0_2":
        raise RuntimeError("unexpected census schema")
    if census.get("status")!="QUALIFIED_RESPONSE_SEALED_V0_2":
        raise RuntimeError("metadata census not qualified")
    if census.get("response_values_accessed") is not False:
        raise RuntimeError("response values already accessed")
    if census.get("abundance_file_opened") is not False:
        raise RuntimeError("abundance file already opened")
    if census["response_surface"].get("opened") is not False:
        raise RuntimeError("monolithic response surface already marked opened")
    if census["selection"]["independent_geography_clusters"]<30:
        raise RuntimeError("fewer than 30 response-blind geography clusters")
    if precision.get("schema")!="structural.landfrag_relative_topology_precision.v0_2":
        raise RuntimeError("unexpected precision audit schema")
    if precision.get("response_values_accessed") is not False:
        raise RuntimeError("precision audit is not response blind")
    if precision.get("census_fingerprint")!=census["census_fingerprint"]:
        raise RuntimeError("precision/census fingerprint drift")

    protocol={
        "schema":"structural.landfrag_relative_topology_protocol.v0_2",
        "status":"FROZEN_BEFORE_MONOLITHIC_ABUNDANCE_ACCESS_V0_2",
        "v0_2_revision":{
            "v0_1_stop":"response-blind >=50 geography replication gate unmet",
            "v0_1_response_opened":False,
            "per_study_geometry_rules_changed":False,
            "v0_2_minimum_geographies":30,
            "precision_audit_fingerprint":precision["precision_fingerprint"],
            "precision_audit":precision,
        },
        "study_role":"fresh global habitat-fragmentation test of within-landscape relative source isolation x stepping-stone topology",
        "source":census["source"],
        "census_fingerprint":census["census_fingerprint"],
        "response_values_accessed":False,
        "abundance_file_opened":False,
        "response_firewall":{
            "surface":"single monolithic LandFrag abundance CSV; opening it consumes the entire LandFrag response family for this program",
            "path":census["response_surface"]["path"],
            "git_blob_sha":census["response_surface"]["git_blob_sha"],
            "expected_columns":EXPECTED_ABUNDANCE_COLUMNS,
            "one_shot_access_only":True,
            "no_pilot_confirmatory_split":True,
            "post_access_new_LandFrag_hypothesis_authorized":False,
        },
        "response_contract":{
            "row_semantics":"one species abundance record within a refshort x fragment_id x plot_id sampling unit",
            "selected_studies":"exact response-blind geometry-qualified refshort set frozen in census",
            "selected_fragments":"only frozen focal fragment_id rows enter the primary study model",
            "plot_aggregation":"within each selected refshort and fragment_id, sum abundance across all plot_id rows separately for each scientific_name",
            "species_name":"scientific_name must be nonempty after stripping whitespace",
            "abundance":"must parse as a finite nonnegative integer; no negative/fractional values",
            "duplicate_rows":"rows with identical refshort, fragment_id, plot_id and scientific_name are summed rather than silently dropped",
            "extra_response_fragments":"allowed in source file but never enter the frozen model unless their fragment_id is a frozen focal for that refshort",
            "missing_frozen_focal":"study fails response-quality gate if any frozen focal fragment has no response rows",
            "study_failure":"predeclared quality failure removes that study without inspecting coefficient direction; the geography remains only if another qualified study in the same frozen cluster survives",
        },
        "primary_response":{
            "name":"individual-based rarefied species richness at the study-specific minimum focal-fragment abundance",
            "fragment_total_abundance":"N_i = sum of aggregated species abundances in frozen focal fragment i",
            "study_reference_effort":"m_g = min_i N_i across all frozen focal fragments in study g",
            "minimum_reference_effort":2,
            "formula":"S_m(i)=sum_s [1 - C(N_i-n_is,m_g)/C(N_i,m_g)], absent probability=0 when N_i-n_is < m_g",
            "calculation":"deterministic analytic hypergeometric expectation using log-gamma arithmetic; no Monte Carlo and no extrapolation",
            "transform":"within each response-qualified study, z-standardize log1p(S_m) using population SD ddof=0",
        },
        "study_response_gate":{
            "all_frozen_focals_present":True,
            "all_focal_total_abundance_at_least":2,
            "study_reference_effort_at_least":2,
            "transformed_response_sd_gt":1e-12,
            "minimum_model_rows":10,
            "frozen_predictor_design_must_remain_full_rank":True,
            "maximum_frozen_predictor_condition_number":100.0,
            "coefficient_direction_never_enters_gate":True,
        },
        "study_model":{
            "family":"ordinary least squares on within-study z(log1p rarefied richness)",
            "columns":census["geometry_rules"]["model_columns"],
            "target":"direct_x_gain",
            "controls":["z_log_area","z_log1p_direct_source_isolation","z_topology_gain"],
            "hyperparameter_tuning":"none",
            "predictors":"exact frozen design rows from metadata census; no response-dependent predictor recomputation",
            "fit_scope":"one independent fit per response-qualified refshort study",
        },
        "geography_aggregation":{
            "cluster_definition":census["geography_clustering"],
            "within_cluster":"equal-weight mean of target coefficients from all response-qualified studies in the frozen geography cluster",
            "across_clusters":"equal-weight mean of geography-cluster target coefficients",
            "minimum_response_qualified_geography_clusters":MIN_RESPONSE_CLUSTERS,
            "failure_rule":"if fewer than 30 frozen geography clusters retain at least one response-qualified study, terminal STOP with no H1 score",
        },
        "H1_primary":{
            "question":"Within fragmented forest landscapes, is the richness association with stepping-stone topology more positive for fragments that are relatively isolated from larger source fragments?",
            "estimand":"equal-geography mean of per-study direct_x_gain coefficients",
            "prediction":"positive",
            "success_rule":"whole-geography-cluster bootstrap 95% interval excludes 0 on positive side",
            "claim_ceiling":"association after fragment area, direct larger-source isolation, and topology-gain main effects; not a direct colonization/dispersal probability and not proof against all unmeasured landscape structure",
        },
        "bootstrap":{
            "unit":"frozen geographic landscape cluster",
            "replicates":BOOTSTRAP_REPS,
            "seed":BOOTSTRAP_SEED,
            "rng":"numpy.default_rng(PCG64)",
            "draw_rule":"sample the response-qualified frozen cluster IDs with replacement, same number of draws as qualified clusters; average sampled cluster coefficients",
            "interval_quantiles":[0.025,0.975],
            "quantile_method":"numpy.quantile method=linear",
        },
        "secondary_nonrescuing":{
            "study_target_sign_fraction":"report fraction of response-qualified study coefficients >0",
            "cluster_target_sign_fraction":"report fraction of geography-cluster coefficients >0",
            "taxon_summaries":"descriptive cluster-balanced summaries by frozen LandFrag taxon; cannot rescue H1",
            "leave_one_geography_out":"exploratory influence diagnostic; cannot rescue H1",
            "landscape_metric_extension":"requires a separately frozen protocol before abundance access; not authorized post-response",
        },
        "forbidden_after_response":[
            "change larger-source definition or allow equal-area sources",
            "change topology/minimax metric",
            "change minimum geometry gates or response-quality gates",
            "change geography clustering threshold",
            "add/drop response studies using coefficient direction",
            "change rarefaction reference effort or allow extrapolation",
            "change model columns, target, sign, geography weighting, bootstrap seed or quantile method",
            "introduce LandFrag landscape metrics as post-hoc controls to rescue H1",
            "use taxon subgroup direction to rescue H1",
            "treat multiple studies in one geography as independent geography replicates",
        ],
        "response_open_authorized":False,
        "H1_scoring_authorized":False,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
