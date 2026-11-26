#!/usr/bin/env python3
"""One source-frozen exploratory matched host association (NOT a new data collection).

Source: Falconi-Lopez et al. 2026, original publisher ZIP supplied locally.
No raw field plot/taxon IDs are exported. Run --test without the original ZIP.
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SHA = "8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d"
HOSTS = ("CACAO", "FERNAN SANCHEZ", "GUABA", "MASCAREI", "SAPANILLO")
STAGES = ("Agri", "Reg1", "Reg2", "Old")
SEED = 20261122
N_PERM = 19999
FILES = {
    "R skript for Saproxylic beetle analyses_2024_12_22.R",
    "PlotLogSpeciesAbundancesDensity.csv",
    "PlotKat4HostSpecIndiv_3.csv",
    "a_Agri_3.csv", "a_Old_3.csv", "a_Reg1_3.csv", "a_Reg2_3.csv",
    "HostBeetleIndiv_3.csv", "PlotSpeciesIndiv_3.csv",
}


def q_stat(a):
    a = np.asarray(a)
    if a.ndim != 2 or a.shape[1] != 5 or not np.isin(a, [0, 1]).all():
        raise ValueError("five matched binary observations per physical plot required")
    c = a.sum(axis=0, dtype=np.int64)
    r = a.sum(axis=1, dtype=np.int64)
    t = int(c.sum())
    den = 5*t - int(r @ r)
    if den <= 0:
        raise ValueError("source matched variation gate: STOP")
    return float(4*(5*int(c @ c)-t*t)/den)


def source_matrix(src):
    raw = Path(src).read_bytes()
    if len(raw) != 11201 or hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError("source original ZIP SHA/size STOP")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if set(z.namelist()) != FILES or len(z.namelist()) != len(FILES):
            raise ValueError("ZIP author file manifest STOP")
        meta = pd.read_csv(io.BytesIO(z.read("PlotSpeciesIndiv_3.csv")),
                           sep=";", dtype=str, keep_default_na=False)
        logs = pd.read_csv(io.BytesIO(z.read("PlotLogSpeciesAbundancesDensity.csv")),
                           sep=";", dtype=str, keep_default_na=False)
    if (len(meta) != 61 or meta.Plot.nunique() != 61
            or meta.Plot.duplicated().any() or not meta.Plot.equals(meta.Plot_ID)):
        raise ValueError("source physical plot keys STOP")
    if (len(logs) != 300 or logs[["Plot","Host"]].duplicated().any()
            or not logs.Plot.isin(meta.Plot).all()
            or set(logs.Host.unique()) != set(HOSTS)):
        raise ValueError("source physical plot x five offered hosts STOP")
    n = logs.groupby("Plot").Host.nunique()
    if n.value_counts().to_dict() != {5:59, 4:1, 1:1}:
        raise ValueError("source missing-log opportunity frame STOP")
    plots = n[n == 5].index
    if any(set(logs.loc[logs.Plot == p, "Host"]) != set(HOSTS) for p in plots):
        raise ValueError("source full five-host site incomplete STOP")
    counts = pd.to_numeric(logs.Indiv, errors="coerce")
    if (counts.isna().any() or (counts < 0).any()
            or not np.isfinite(counts).all() or (counts != np.floor(counts)).any()):
        raise ValueError("invalid source adult count STOP")
    logs["Y"] = (counts > 0).astype(int)
    x = logs[logs.Plot.isin(plots)].pivot(index="Plot", columns="Host", values="Y")
    x = x.loc[:, list(HOSTS)].sort_index()
    if x.shape != (59,5) or x.isna().any().any() or int(x.to_numpy().sum()) != 169:
        raise ValueError("matched 59 site binary frame STOP")
    stages = meta.set_index("Plot").loc[x.index,"Category4"]
    if set(stages) != set(STAGES) or stages.value_counts().to_dict() != {
            "Agri":11,"Reg1":21,"Reg2":12,"Old":15}:
        raise ValueError("source stage mapping STOP")
    return x, stages


def run(src):
    x, stages = source_matrix(src)
    a = x.to_numpy(dtype=np.int8)
    observed = q_stat(a)
    rng = np.random.default_rng(SEED)
    row_sums = a.sum(axis=1)
    ge = 0
    for _ in range(N_PERM):
        shuffled = np.stack([row[rng.permutation(5)] for row in a])
        assert np.array_equal(shuffled.sum(axis=1), row_sums)
        if q_stat(shuffled) >= observed - 1e-12:
            ge += 1
    counts = x.sum(axis=0)
    stage_counts = {s:{"plots":int((stages==s).sum()),
                       "positive_by_host":{h:int(x.loc[stages==s,h].sum()) for h in HOSTS}}
                    for s in STAGES}
    return {
        "schema":"structural.falconi2026_within_plot_host_omnibus_exploratory.v1",
        "source_original_zip_sha256":SHA,
        "evidence_class":"retrospective, outcome-exposed source-matched association only",
        "original_independent_study_count":1, "physical_plot_count":59,
        "host_log_records":295, "observed_positive_log_records":int(a.sum()),
        "offered_host_labels":list(HOSTS),
        "positive_by_host":{h:int(counts[h]) for h in HOSTS},
        "positive_rate_by_host":{h:float(counts[h]/59) for h in HOSTS},
        "descriptive_max_min_host_rate_gap":float((counts.max()-counts.min())/59),
        "within_plot_success_distribution":{
            str(k):int(v) for k,v in x.sum(axis=1).value_counts().items()},
        "stage_specific_counts_descriptive_not_inferential":stage_counts,
        "cochran_Q":observed,"MC_permutations":N_PERM,
        "MC_null_exceedances":ge,"MC_p_one_sided":(ge+1)/(N_PERM+1),
        "original_plot_ids_or_species_ids_exported":False,
        "new_species_composition_test_scored":False,
        "causal_or_multiregion_host_selection_claim":False,
        "prior_LOPO_predictive_gain_uncertainty_unchanged":
            "E0-E1 +0.030624, bootstrap [-0.005204,+0.064390], p=.0906: non-support",
    }


def smoke_test():
    x=np.eye(5,dtype=np.int8)
    assert q_stat(x)==0
    y=np.array([[1,0,0,0,0],[1,0,0,0,0],
                [1,0,0,0,0],[0,1,0,0,0]],dtype=np.int8)
    assert q_stat(y)==8.5
    try:
        q_stat(np.ones((5,5),dtype=np.int8))
        raise AssertionError("zero variation must STOP")
    except ValueError:
        pass
    print("SYNTHETIC_COHCHRAN_Q_PASS")


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source")
    p.add_argument("--out")
    p.add_argument("--test",action="store_true")
    a=p.parse_args()
    if a.test:
        smoke_test()
    else:
        if not a.source or not a.out:
            p.error("--source and --out required")
        obj=run(a.source)
        path=Path(a.out)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
        print("MATCHED_HOST_Q",obj["cochran_Q"],"CONDITIONAL_MC_P",obj["MC_p_one_sided"])
