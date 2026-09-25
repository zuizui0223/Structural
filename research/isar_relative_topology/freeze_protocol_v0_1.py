#!/usr/bin/env python3
"""Freeze the fresh ISAR relative-isolation x topology response protocol.

No abundance matrix is opened here. This consumes only the exact response-blind
metadata census and fixes response parsing, rarefaction, model and inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_CENSUS="7def865c885385629c517f22a7a2fe27ab447a6fec7a99a1150c7ba307f2b84b"
TARGET="topology_x_relative_isolation"

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise RuntimeError(f"{path} must contain object")
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",type=Path,required=True)
    ap.add_argument("--contamination",type=Path,required=True)
    a=ap.parse_args()
    census=load(a.census); contamination=load(a.contamination)

    if census.get("census_fingerprint")!=EXPECTED_CENSUS:
        raise RuntimeError("census fingerprint drift")
    if census.get("status")!="QUALIFIED_RESPONSE_SEALED":
        raise RuntimeError("metadata census not qualified")
    if census.get("response_values_accessed") is not False or census.get("abundance_files_opened") is not False:
        raise RuntimeError("fresh abundance response already opened")
    if contamination.get("status")!="FROZEN_BEFORE_FRESH_RESPONSE":
        raise RuntimeError("contamination boundary drift")
    if contamination.get("response_values_used_for_hypothesis_design") is not False:
        raise RuntimeError("response contamination influenced H1 design")
    if not all(census["pre_response_gates"].values()):
        raise RuntimeError("pre-response geometry gates not all passed")

    response_surfaces=census["response_surfaces"]
    if len(response_surfaces)!=10 or len({r["geography_cluster"] for r in response_surfaces})!=10:
        raise RuntimeError("fresh response surface not 10 independent geographic clusters")
    if any(r.get("opened") is not False for r in response_surfaces):
        raise RuntimeError("fresh response surface already marked opened")

    protocol={
        "schema":"structural.isar_relative_topology_protocol.v0_1",
        "status":"FROZEN_BEFORE_FRESH_RESPONSE",
        "study_family":"fresh public-data test of within-archipelago relative isolation x stepping-stone topology",
        "source":census["source"],
        "census_fingerprint":EXPECTED_CENSUS,
        "contamination_boundary_sha256":sha(contamination),
        "response_values_accessed":False,
        "response_surfaces":response_surfaces,
        "geographic_archipelagos":census["selection"]["final_geographic_archipelagos"],
        "islands":census["selection"]["final_islands"],
        "response_contract":{
            "matrix_orientation":"rows are islands; first column is island_name; all remaining columns are species abundances",
            "source_identity":"exact source repository commit + path frozen in census; no fallback version or alternate processed N10/N20 matrix",
            "island_row_match":"after stripping surrounding whitespace, island_name values must be unique and exactly equal the frozen metadata island_code set for that study; no fuzzy matching",
            "species_columns":"all columns after island_name must be nonempty and unique after exact string comparison",
            "missing_abundance":"blank or case-insensitive NA is converted to zero, matching the published synthesis preprocessing",
            "abundance_cells":"all other cells must parse as finite nonnegative integer individual counts; fractional or negative values fail closed",
            "study_quality_gate":[
                "all ten frozen files must parse under this exact contract",
                "every frozen island must have total abundance N >= 2",
                "study-specific minimum abundance m_g=min_i(N_i) must be >=2",
                "primary rarefied-richness response must be finite on every island",
                "z(log1p rarefied richness) must have population SD > 1e-12 within every study"
            ],
            "failure_rule":"if any one of the ten studies fails any response-quality gate, record terminal STOP and compute no H1 coefficient or bootstrap interval",
        },
        "primary_response":{
            "name":"individual-based rarefied species richness at the study minimum abundance",
            "study_reference_effort":"m_g = minimum total individual abundance N_i across all frozen islands in study g",
            "formula":"S_m(i)=sum_s [1 - C(N_i-n_is,m_g)/C(N_i,m_g)], with absent probability set to 0 when N_i-n_is < m_g",
            "computation":"deterministic analytic hypergeometric expectation using log-gamma arithmetic; no Monte Carlo rarefaction and no extrapolation",
            "analysis_transform":"within each study, z-standardize log1p(S_m) using population SD ddof=0 before study fixed-effect demeaning",
            "reason":"controls individual count within study without extrapolating beyond observed abundance; uses the same individual-based rarefaction principle as the source synthesis",
        },
        "predictor_model":{
            "columns":census["design"]["columns"],
            "target":TARGET,
            "area_control":"z_log_area",
            "core_distance_control":"z_core_distance",
            "relative_isolation_main_effect":"z_relative_isolation",
            "topology_main_effect":"z_step_gain",
            "interaction":"topology_x_relative_isolation = z_step_gain * z_relative_isolation",
            "study_fixed_effects":"demean transformed response and all final predictor columns within source study",
            "weights":census["design"]["geography_weighting"],
            "estimator":"geographic-archipelago-equal weighted least squares",
            "no_hyperparameter_tuning":True,
        },
        "H1_primary":{
            "question":"Within an archipelago, is stepping-stone topology more beneficial for islands that are relatively isolated from their nearest neighbours?",
            "estimand":"weighted pooled coefficient on topology_x_relative_isolation after frozen area/core-distance/main-effect controls and study fixed effects",
            "prediction":"positive",
            "success_rule":"frozen whole-geographic-archipelago bootstrap 95% interval excludes zero on the positive side",
            "claim_ceiling":"association of standardized rarefied richness with response-independent local geometry; not a direct colonization, extinction, or dispersal-rate estimate",
        },
        "bootstrap":{
            **census["design"]["bootstrap"],
            "interval_quantiles":[0.025,0.975],
            "quantile_method":"numpy.quantile method=linear",
            "point_and_bootstrap_model_identical":True,
        },
        "secondary_nonrescuing":{
            "inverse_simpson_effective_diversity":"may be reported after the primary one-shot using the same frozen panel/model; cannot rescue H1",
            "sampling_design_sensitivity":"may descriptively stratify fixed versus non-standardized sampling using metadata frozen before response; cannot rescue H1",
            "taxon_or_island_type_moderators":"exploratory only and cannot become confirmatory after response",
        },
        "forbidden_after_response":[
            "reintroduce any directly or geographically contaminated study",
            "add or replace response studies or islands",
            "change geographic-cluster definition or weighting",
            "change nearest-neighbour relative-isolation definition",
            "change geometry medoid, minimax bottleneck, or step-gain definition",
            "change area/core-distance controls or interaction target",
            "change rarefaction reference effort or allow extrapolation",
            "drop a study after seeing H1 unless its predeclared response-quality gate fails, in which case the entire v0.1 test terminates without scoring",
            "change bootstrap seed, cluster unit, draw set or quantile method",
            "select a taxon/island-type subgroup based on effect direction",
        ],
        "response_open_authorized":False,
        "H1_scoring_authorized":False,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
