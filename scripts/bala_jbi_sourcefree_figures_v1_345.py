#!/usr/bin/env python3
"""v1.345 manuscript figures and source ledger from ONLY frozen BALA aggregates.

Original 10,379 Event / 63,904 Occurrence source records are NEVER opened.
The v1.344 scientific audit enforces original SHA/29 physical site identity,
and three main figures distinguish temporal (within-site) turnover, spatial
among-site beta and changes in site richness. Island labels are descriptive;
the 49/56 dependent site pairs and 18 half-Event partitions are NOT n.
"""
from __future__ import annotations
import argparse,csv,json,math,statistics
from pathlib import Path

from bala_temporal_spatial_paper_sourcefree_v1_344 import (
    analyze, V316, V318, CONTRACT, ISLANDS, SOURCE_SHA, SHA316, SHA318
)

NAMES={
    "fai":"Faial","flo":"Flores","pic":"Pico","sjg":"São Jorge",
    "smg":"São Miguel","smr":"Santa Maria","ter":"Terceira",
}
GUILDS={"araneae":"Spiders","coleoptera":"Beetles"}

def make_ledger(v316,v318,contract):
    audit=analyze(v316,v318,contract)
    if audit["status"]!="BALA_SEVEN_ISLAND_BEETLE_HOMOGENIZATION_LOO_SOURCEFREE_VALIDATED":
        raise ValueError("Prior original source-identity scientific paper audit STOP")
    out=[]
    for island in ISLANDS:
        for guild in GUILDS:
            temporal=v316["pitfall"][guild]["per_island"][island]
            spatial=v318["main_pitfall"][guild]["per_island"][island]
            out.append({
              "island_code":island,
              "island_name":NAMES[island],
              "guild":guild,
              "guild_label":GUILDS[guild],
              "physical_plots_spatial":spatial["matched_physical_sites"],
              "dependent_plot_pairs":spatial["dependent_pairs"],
              "physical_plots_half_sample":temporal["n"],
              "source_sites_positive_temporal_excess":temporal["positive"],
              "temporal_sorensen_across_minus_within":temporal["excess_sorensen"],
              "temporal_simpson_across_minus_within":temporal["excess_simpson"],
              "B1_spatial_simpson":spatial["B1_spatial_simpson"],
              "B3_spatial_simpson":spatial["B3_spatial_simpson"],
              "spatial_simpson_delta_B3_minus_B1":spatial["delta_spatial_simpson"],
              "spatial_sorensen_delta_B3_minus_B1":spatial["delta_spatial_sorensen"],
              "mean_local_richness_B1":spatial["mean_B1_site_richness"],
              "mean_local_richness_B3":spatial["mean_B3_site_richness"],
              "mean_local_richness_delta_B3_minus_B1":
                    spatial["mean_B3_site_richness"]-spatial["mean_B1_site_richness"],
              "original_observed_gamma_B1":spatial["source_B1_island_taxa"],
              "original_observed_gamma_B3":spatial["source_B3_island_taxa"],
            })
    if len(out)!=14 or len({r["island_code"] for r in out})!=7:
        raise ValueError("Source seven-island two-guild set is not complete")
    for guild in GUILDS:
        rows=[r for r in out if r["guild"]==guild]
        origin= v318["main_pitfall"][guild]
        if sum(r["physical_plots_spatial"] for r in rows)!=origin["source_physical_sites"]:
            raise ValueError("Original physical site count changed")
        if sum(r["dependent_plot_pairs"] for r in rows)!=origin["dependent_site_pairs"]:
            raise ValueError("Source within-island dependent pairs changed")
        if not math.isclose(statistics.fmean(r["spatial_simpson_delta_B3_minus_B1"] for r in rows),
                            origin["island_equal_delta_spatial_simpson"],abs_tol=1e-12):
            raise ValueError("Source seven island spatial direction mean mismatch")
        if not math.isclose(statistics.fmean(r["temporal_sorensen_across_minus_within"] for r in rows),
                            v316["pitfall"][guild]["island_equal_excess_sorensen"],abs_tol=1e-12):
            raise ValueError("Source within-phase sampling excess mean mismatch")
    return audit,out

def _pretty_axes(ax,title,ylabel):
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.axhline(0,linewidth=.8,alpha=.7)
    ax.grid(axis="y",alpha=.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

def render(v316,v318,contract,destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    audit,rows=make_ledger(v316,v318,contract)
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    # Figure 1. Plot source original ISLAND temporal vs within period excess
    fig,ax=plt.subplots(figsize=(11,5.7))
    x=list(range(len(ISLANDS)))
    offsets={"araneae":-.19,"coleoptera":.19}
    markers={"araneae":"o","coleoptera":"s"}
    for guild in GUILDS:
        y=[next(r for r in rows if r["guild"]==guild and r["island_code"]==i)["temporal_sorensen_across_minus_within"] for i in ISLANDS]
        ax.scatter([z+offsets[guild] for z in x],y,marker=markers[guild],
                   s=70,label=GUILDS[guild])
    ax.set_xticks(x,[NAMES[i] for i in ISLANDS],rotation=18,ha="right")
    _pretty_axes(ax,"Temporal species-identity dissimilarity beyond within-campaign half-sample differences",
                 "Sørensen dissimilarity: between − within")
    ax.legend(frameon=False,ncol=2)
    ax.text(.99,.015,"Island means; site n = 29 spiders / 26 beetles; split salts are not independent",
            transform=ax.transAxes,ha="right",va="bottom",fontsize=8,alpha=.7)
    fig.tight_layout()
    fig.savefig(destination/"figure1_temporal_excess.png",dpi=260)
    fig.savefig(destination/"figure1_temporal_excess.svg")
    plt.close(fig)

    # Figure 2. Spatial changes with negative = homogenization.
    fig,ax=plt.subplots(figsize=(10.7,5.6))
    for guild in GUILDS:
        y=[next(r for r in rows if r["guild"]==guild and r["island_code"]==i)["spatial_simpson_delta_B3_minus_B1"] for i in ISLANDS]
        ax.scatter([z+offsets[guild] for z in x],y,marker=markers[guild],s=70,label=GUILDS[guild])
    ax.set_xticks(x,[NAMES[i] for i in ISLANDS],rotation=18,ha="right")
    _pretty_axes(ax,"Spatial forest-community change differs by guild",
                 "Within-island spatial Simpson β, B3 − B1")
    ax.text(.01,.03,"Below zero: spatial homogenization   •   Above zero: differentiation",
            transform=ax.transAxes,ha="left",va="bottom",fontsize=9)
    ax.legend(frameon=False,ncol=2)
    fig.tight_layout()
    fig.savefig(destination/"figure2_spatial_beta_by_island.png",dpi=260)
    fig.savefig(destination/"figure2_spatial_beta_by_island.svg")
    plt.close(fig)

    # Figure 3. Alpha richness vs spatial beta; original 7 island physical n.
    b=[next(r for r in rows if r["guild"]=="coleoptera" and r["island_code"]==i)
       for i in ISLANDS]
    fig,ax=plt.subplots(figsize=(8.6,6.3))
    alpha=[r["mean_local_richness_delta_B3_minus_B1"] for r in b]
    beta=[r["spatial_simpson_delta_B3_minus_B1"] for r in b]
    ax.scatter(alpha,beta,s=82)
    for r in b:
        ax.annotate(f'{r["island_name"]} (n={r["physical_plots_spatial"]})',
          xy=(r["mean_local_richness_delta_B3_minus_B1"],
              r["spatial_simpson_delta_B3_minus_B1"]),
          xytext=(5,7),textcoords="offset points",fontsize=9)
    ax.axvline(0,linewidth=.8,alpha=.7)
    _pretty_axes(ax,"Rising local beetle richness does not preclude forest convergence",
                 "Within-island spatial Simpson β, B3 − B1")
    ax.set_xlabel("Mean local beetle richness, B3 − B1 (taxa/site)")
    fig.tight_layout()
    fig.savefig(destination/"figure3_alpha_spatial_decoupling.png",dpi=260)
    fig.savefig(destination/"figure3_alpha_spatial_decoupling.svg")
    plt.close(fig)

    # Text data for all graphical points: no source species names/coordinates.
    fields=list(rows[0])
    with (destination/"sourcefree_island_figure_data.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest={
        "schema":"structural.bala_jbi_sourcefree_figure_bundle.v1_345",
        "status":"ORIGINAL_BALA_NUMERICAL_FIGURES_GENERATED_WITHOUT_BIOLOGICAL_SOURCE",
        "original_archive_SHA256":SOURCE_SHA,
        "original_v316_inner_result_SHA256":SHA316,
        "original_v318_inner_result_SHA256":SHA318,
        "physical_islands":7,
        "physical_sites":29,
        "matched_source_events_original":4620,
        "original_Event_or_Occurrence_rows_opened":0,
        "figures":["figure1_temporal_excess","figure2_spatial_beta_by_island",
                   "figure3_alpha_spatial_decoupling"],
        "island_guild_row_n":len(rows),
        "source_island_equal_spatial_simpson_delta":{
            guild:audit["source_pitfall_guilds"][guild]["island_equal_spatial_simpson_B3_minus_B1"]
            for guild in GUILDS
        },
        "beetle_one_island_delete_negative_n":
            audit["source_pitfall_guilds"]["coleoptera"]["source_one_island_delete_negative_count"],
        "negative_beetle_spatial_mean_is_not_seven_of_seven_negative_islands":True,
        "no_new_significance_or_causal_model":True,
        "source_BALA_v314_v316_v318_workflows_SEALED":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }
    (destination/"figure_bundle_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--316",dest="source316",type=Path,default=V316)
    p.add_argument("--318",dest="source318",type=Path,default=V318)
    p.add_argument("--contract",type=Path,default=CONTRACT)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    manifest=render(json.loads(args.source316.read_text(encoding="utf-8")),
                    json.loads(args.source318.read_text(encoding="utf-8")),
                    json.loads(args.contract.read_text(encoding="utf-8")),
                    args.out)
    print(json.dumps(manifest,sort_keys=True))
if __name__=="__main__":main()
