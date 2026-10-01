#!/usr/bin/env python3
"""Build submission-facing macro figures from already frozen outputs only."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GLOBAL_EFFECT=-0.0018141589038615496
RHO_ISOLATION=0.28743057515243015
RHO_ISOLATION_WITHIN=0.2278413095720483
RHO_BREADTH=0.27643959301238685

class Stop(RuntimeError): pass

def read_csv(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

def f(x):
    v=float(str(x))
    if not math.isfinite(v): raise Stop("nonfinite value")
    return v

def linear_fit(xs,ys):
    if len(xs)!=len(ys) or len(xs)<2: raise Stop("invalid fit input")
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    den=sum((x-mx)**2 for x in xs)
    if den<=0: raise Stop("zero x variance")
    slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den
    intercept=my-slope*mx
    return intercept,slope

def save(fig,outdir,name):
    outdir.mkdir(parents=True,exist_ok=True)
    for ext in ("png","svg"):
        fig.savefig(outdir/f"{name}.{ext}",bbox_inches="tight",dpi=300)
    plt.close(fig)

def fig1_bioregions(rows,outdir):
    rows=sorted(rows,key=lambda r:f(r["mean_delta"]))
    labels=[r["bioregion"] for r in rows]
    vals=[f(r["mean_delta"]) for r in rows]
    fig,ax=plt.subplots(figsize=(7.2,5.4))
    y=list(range(len(rows)))
    ax.scatter(vals,y)
    ax.axvline(0,linewidth=1)
    ax.axvline(GLOBAL_EFFECT,linewidth=1,linestyle="--")
    ax.set_yticks(y,labels)
    ax.set_xlabel("Equal-block mean C−R3 log loss")
    ax.set_ylabel("Bioregion")
    ax.set_title("Global mammal source-network increment across bioregions")
    ax.text(0.02,0.02,"Negative values favour graph-path source continuity\nGlobal equal-block mean = −0.001814",transform=ax.transAxes,va="bottom")
    save(fig,outdir,"fig1_bioregion_effects")

def fig2_isolation(rows,outdir):
    xs=[f(r["mean_z_Current_isolation"]) for r in rows]
    ys=[f(r["delta"]) for r in rows]
    intercept,slope=linear_fit(xs,ys)
    xlo,xhi=min(xs),max(xs)
    line_x=[xlo,xhi]; line_y=[intercept+slope*x for x in line_x]
    fig,ax=plt.subplots(figsize=(6.6,5.2))
    ax.scatter(xs,ys,s=20)
    ax.plot(line_x,line_y,linewidth=1.5)
    ax.axhline(0,linewidth=1)
    ax.set_xlabel("Block mean standardized current external isolation")
    ax.set_ylabel("Block mean C−R3 log loss")
    ax.set_title("External isolation attenuates the source-network increment")
    ax.text(0.02,0.98,f"Spearman ρ = {RHO_ISOLATION:.3f}\nWithin-bioregion centered ρ = {RHO_ISOLATION_WITHIN:.3f}",transform=ax.transAxes,va="top")
    ax.text(0.02,0.02,"Positive association = less-negative C−R3 at greater isolation",transform=ax.transAxes,va="bottom")
    save(fig,outdir,"fig2_external_isolation_attenuation")

def fig3_breadth(species,quartiles,outdir):
    xs=[f(r["pilot_prevalence"]) for r in species]
    ys=[f(r["mean_C_minus_R3"]) for r in species]
    qx=[f(r["mean_pilot_prevalence"]) for r in quartiles]
    qy=[f(r["mean_C_minus_R3"]) for r in quartiles]
    fig,ax=plt.subplots(figsize=(6.6,5.2))
    ax.scatter(xs,ys,s=24)
    ax.plot(qx,qy,marker="o",linewidth=1.5)
    ax.axhline(0,linewidth=1)
    ax.set_xlabel("Pilot occupancy prevalence")
    ax.set_ylabel("Species mean held-out C−R3 log loss")
    ax.set_title("Broad species receive weaker graph-topology gains")
    ax.text(0.02,0.98,f"Spearman ρ = {RHO_BREADTH:.3f}",transform=ax.transAxes,va="top")
    ax.text(0.02,0.02,"Connected points are the four pre-defined rank-group means",transform=ax.transAxes,va="bottom")
    save(fig,outdir,"fig3_species_breadth_attenuation")

def figS1_gift(freeze,outdir):
    a=freeze["endpoint_availability"]
    labels=[
      "Retained high-confidence\nendpoint available",
      "Available list, zero accepted\nnative rows",
      "No available list",
    ]
    vals=[
      int(a["retained_entities"]),
      int(a["excluded_entities_available_list_but_zero_accepted_high_confidence_native_rows"]),
      int(a["excluded_entities_no_available_list"]),
    ]
    fig,ax=plt.subplots(figsize=(7.0,4.8))
    ax.bar(labels,vals)
    ax.set_ylabel("Frozen confirmatory GIFT entities")
    ax.set_title("Endpoint-quality attrition in the nonconfirmatory GIFT continuation")
    for i,v in enumerate(vals):
        ax.text(i,v,str(v),ha="center",va="bottom")
    ax.text(0.02,0.98,"Frozen confirmatory entities = 404\nRetained for exploratory scoring = 118",transform=ax.transAxes,va="top")
    save(fig,outdir,"figS1_gift_endpoint_attrition")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--block-context",type=Path,required=True)
    ap.add_argument("--bioregion-summary",type=Path,required=True)
    ap.add_argument("--species-effects",type=Path,required=True)
    ap.add_argument("--breadth-quartiles",type=Path,required=True)
    ap.add_argument("--gift-freeze",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    block=read_csv(a.block_context)
    bio=read_csv(a.bioregion_summary)
    species=read_csv(a.species_effects)
    quartiles=read_csv(a.breadth_quartiles)
    gift=json.loads(a.gift_freeze.read_text())

    if len(block)!=168: raise Stop("block count drift")
    if len(bio)!=12: raise Stop("bioregion count drift")
    if len(species)!=79: raise Stop("species count drift")
    if len(quartiles)!=4: raise Stop("quartile count drift")
    if gift["endpoint_availability"]["retained_entities"]!=118: raise Stop("GIFT freeze drift")

    fig1_bioregions(bio,a.output_dir)
    fig2_isolation(block,a.output_dir)
    fig3_breadth(species,quartiles,a.output_dir)
    figS1_gift(gift,a.output_dir)

    receipt={
      "schema":"structural.macro_figure_result.v1_83",
      "status":"FROZEN_OUTPUT_ONLY_FIGURES_RENDERED",
      "figures":[
        "fig1_bioregion_effects",
        "fig2_external_isolation_attenuation",
        "fig3_species_breadth_attenuation",
        "figS1_gift_endpoint_attrition"
      ],
      "new_response_accessed":False,
      "counts_as_empirical_evidence":False
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__": main()
