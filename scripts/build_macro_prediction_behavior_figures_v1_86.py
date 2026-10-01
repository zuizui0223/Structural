#!/usr/bin/env python3
"""Render v1.85 prediction-behaviour diagnostics from frozen JSON only."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

class Stop(RuntimeError): pass

def val(x):
    x=float(x)
    if not math.isfinite(x): raise Stop("nonfinite value")
    return x

def save(fig,outdir,name):
    outdir.mkdir(parents=True,exist_ok=True)
    fig.tight_layout()
    for ext in ("png","svg"):
        fig.savefig(outdir/f"{name}.{ext}",dpi=300,bbox_inches="tight")
    plt.close(fig)

def asymmetry(x,outdir):
    labels=[
      "Natural-prevalence\nblock primary",
      "True absences",
      "Realized presences",
      "Class-balanced\nblock diagnostic",
    ]
    values=[
      val(x["effect_scale"]["block_weighted"]["C_minus_R3"]),
      val(x["outcome_asymmetry"]["absence"]["C_minus_R3"]),
      val(x["outcome_asymmetry"]["presence"]["C_minus_R3"]),
      val(x["outcome_asymmetry"]["class_balanced_equal_block_C_minus_R3"]),
    ]
    fig,ax=plt.subplots(figsize=(7.4,4.9))
    y=list(range(len(labels)))
    ax.barh(y,values)
    ax.axvline(0,linewidth=1)
    ax.set_yticks(y,labels)
    ax.invert_yaxis()
    ax.set_xlabel("C−R3 log-loss difference")
    ax.set_title("Prediction gain is strongly asymmetric across outcome classes")
    span=max(values)-min(values)
    for i,v in enumerate(values):
        offset=0.018*span
        ax.text(v+(offset if v>=0 else -offset),i,f"{v:+.4f}",
                ha="left" if v>=0 else "right",va="center")
    ax.margins(x=0.12)
    save(fig,outdir,"figS2a_outcome_class_asymmetry")

def graph_support(x,outdir):
    g=x["graph_empty_support"]
    labels=["Graph-source nonempty","Graph-source empty"]
    values=[
      val(g["nonempty_cell_mean_C_minus_R3"]),
      val(g["empty_cell_mean_C_minus_R3"]),
    ]
    counts=[int(g["nonempty_cells"]),int(g["empty_cells"])]
    fig,ax=plt.subplots(figsize=(7.2,3.8))
    y=list(range(2))
    ax.barh(y,values)
    ax.axvline(0,linewidth=1)
    ax.set_yticks(y,[f"{lab}\n(n={n:,})" for lab,n in zip(labels,counts)])
    ax.invert_yaxis()
    ax.set_xlabel("Mean C−R3 log-loss difference")
    ax.set_title("Graph-source support strengthens the topological increment")
    span=max(values)-min(values)
    for i,v in enumerate(values):
        off=max(0.00025,0.04*span)
        ax.text(v-off,i,f"{v:+.4f}",ha="right",va="center")
    ax.margins(x=0.18)
    save(fig,outdir,"figS2b_graph_source_support")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    x=json.loads(a.freeze.read_text())
    if x.get("schema")!="structural.global_mammals_prediction_behavior_freeze.v1_85":
        raise Stop("freeze schema drift")
    if x["interpretation_guardrails"]["primary_v1_76_unchanged"] is not True:
        raise Stop("primary boundary drift")
    asymmetry(x,a.output_dir)
    graph_support(x,a.output_dir)
    result={
      "schema":"structural.macro_prediction_behavior_figure_result.v1_86",
      "status":"FROZEN_DIAGNOSTIC_FIGURES_RENDERED",
      "figures":[
        "figS2a_outcome_class_asymmetry",
        "figS2b_graph_source_support"
      ],
      "new_response_accessed":False,
      "may_change_primary_status":False,
      "counts_as_empirical_evidence":False
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
