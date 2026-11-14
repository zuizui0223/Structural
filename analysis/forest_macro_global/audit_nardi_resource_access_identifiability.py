#!/usr/bin/env python3
"""Can forest amount and road/building accessibility be separately estimated?

Source-original Nardi et al. 2026 Zenodo v3 env_data_trapscale.txt (MD5
11113faa4c13dd775c75da7e5238d2c9), a 207-cell 13-landscape habitat
profile with composition (tree cover) and configuration (unblocked directions)
from within 250 m; both are components of urbanization_index.

This source-only design audit NEVER opens beetle species, counts, status, or
taxonomic outcomes. It requires explicit within-landscape residual
configuration variation after composition before an independent accessibility
association can be attempted. It is not a dispersal/movement experiment.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from collections import defaultdict
from pathlib import Path

MD5="11113faa4c13dd775c75da7e5238d2c9"
SOURCE="https://doi.org/10.5281/zenodo.17044394"
EXPECTED_FIELDS=["SITE","CELL_ID","composition","configuration","urbanization_index"]

def pearson(x,y):
    if len(x)!=len(y) or len(x)<3:return None
    a=statistics.mean(x);b=statistics.mean(y)
    p=sum((v-a)*(w-b) for v,w in zip(x,y))
    q=sum((v-a)**2 for v in x)*sum((w-b)**2 for w in y)
    return p/math.sqrt(q) if q>0 else None

def read(path):
    src=Path(path)
    if hashlib.md5(src.read_bytes()).hexdigest()!=MD5:
        raise ValueError("source_frozen_Zenodo_trap_environment_MD5_changed")
    with src.open(encoding="utf-8-sig",newline="") as f:
        d=csv.DictReader(f,delimiter="\t")
        if (d.fieldnames or [])!=EXPECTED_FIELDS:
            raise ValueError("source_trap_environment_field_definition_changed")
        rows=list(d)
    if len(rows)!=207:raise ValueError("original_207_trap_context_rows_changed")
    return rows

def analyze(rows):
    if len(rows)!=207:raise ValueError("not_original_207_trap_environment_rows")
    bysite=defaultdict(list)
    ids=set()
    for row in rows:
        if list(row)!=EXPECTED_FIELDS:raise ValueError("original_trap_environment_columns_changed")
        site=str(row["SITE"]).strip()
        cell=str(row["CELL_ID"]).strip()
        if not site or not cell or (site,cell) in ids:
            raise ValueError("missing_or_duplicated_original_trap_context_cell")
        ids.add((site,cell))
        try:
            triple=[float(row[x]) for x in EXPECTED_FIELDS[2:]]
        except (ValueError,TypeError):
            raise ValueError("missing_original_trap_context_number")
        if not all(math.isfinite(x) for x in triple):
            raise ValueError("invalid_original_trap_context_number")
        bysite[site].append(triple)
    if len(bysite)!=13 or sorted(len(v) for v in bysite.values())!=[15]+[16]*12:
        raise ValueError("13_landscape_207cell_field_grain_changed")
    data=[item for rr in bysite.values() for item in rr]
    c=[q[0] for q in data]
    g=[q[1] for q in data]
    u=[q[2] for q in data]
    canonical=[{"variable":v,"min":min(xs),"median":statistics.median(xs),
                "max":max(xs),"population_sd":statistics.pstdev(xs),
                "nonzero":sum(x!=0 for x in xs)}
               for v,xs in (("composition",c),("configuration",g),("urbanization_index",u))]
    within_c=[]
    within_g=[]
    per=[]
    for idx,(site,rr) in enumerate(sorted(bysite.items())):
        cc=[q[0] for q in rr]
        gg=[q[1] for q in rr]
        uc=[q[2] for q in rr]
        mx=statistics.mean(cc);my=statistics.mean(gg)
        xc=[x-mx for x in cc]
        yg=[y-my for y in gg]
        within_c.extend(xc)
        within_g.extend(yg)
        r=pearson(cc,gg)
        # Pair checks are a design SUPPORT diagnostic, never independent
        # statistical replicates. Use original percent units when confirmed.
        discordant=sum(abs(cc[i]-cc[j])<=10 and abs(gg[i]-gg[j])>=20
                       for i in range(len(rr)) for j in range(i+1,len(rr)))
        per.append({
            "anonymous_landscape":idx+1,
            "original_trap_cells":len(rr),
            "composition_pstdev":statistics.pstdev(cc),
            "configuration_pstdev":statistics.pstdev(gg),
            "within_landscape_composition_configuration_correlation":r,
            "near_equal_composition_contrasting_barrier_pairs_NONINDEPENDENT":discordant,
            "urbanization_index_pstdev":statistics.pstdev(uc)
        })
    rglobal=pearson(c,g)
    rwithin=pearson(within_c,within_g)
    if rwithin is None:raise ValueError("source_zero_within_site_feature_variance")
    residual=[yg - rwithin*(statistics.pstdev(within_g)/statistics.pstdev(within_c))*xc
              for xc,yg in zip(within_c,within_g)]
    residual_fraction=(statistics.pvariance(residual)/statistics.pvariance(within_g))
    VIF=1/(1-rwithin**2) if abs(rwithin)<1 else None
    # "Configuration" is not a barrier-distance raster; it is the source
    # measured unblocked angular percentage. The source article reports r=0.85
    # for tree cover and unblocked angle over its actual 250 m buffers.
    access_support={
        "criterion_in_scope_landscapes":len(per)==13,
        "criterion_residual_configuration_variance_at_least_20_percent":residual_fraction>=0.2,
        "criterion_at_least_6_landscapes_with_nearequal_cover_contrasting_barrier_pairs":
             sum(q["near_equal_composition_contrasting_barrier_pairs_NONINDEPENDENT"]>0 for q in per)>=6,
        "criterion_within_site_finite_correlation":rwithin is not None and abs(rwithin)<0.99,
    }
    # The gate describes an estimability question. Do not modify thresholds
    # after seeing source-only predictor support to fish for significance.
    admitted=all(access_support.values())
    return {
        "schema":"structural.forest_Nardi_2026_resource_vs_access_design_support.v1",
        "source_original_Zenodo_version":"v3",
        "source_original_DOI":SOURCE,
        "original_study_trap_cell_count":len(rows),
        "original_landscape_context_count":len(per),
        "sources_sampling_effort_and_beetle_incidence_NOT_READ":True,
        "source_covariate_names":EXPECTED_FIELDS[2:],
        "source_covariate_raw_descriptive":canonical,
        "overall_correlation_composition_configuration":rglobal,
        "forest_landscape_fixed_effect_centered_covariate_correlation":rwithin,
        "landscape_centered_configuration_variance_retained_after_cover_regression":residual_fraction,
        "within_landscape_composition_configuration_variance_inflation_factor":VIF,
        "source_landscapes_with_discordant_tree_cover_and_barrier_pairs":sum(
            q["near_equal_composition_contrasting_barrier_pairs_NONINDEPENDENT"]>0 for q in per),
        "source_comparable_cover_different_barrier_pair_count_NOT_INDEPENDENT":sum(
            q["near_equal_composition_contrasting_barrier_pairs_NONINDEPENDENT"] for q in per),
        "source_landscape_anonymized_support":per,
        "frozen_support_rules":access_support,
        "two_covar_separable_in_original_observed_feature_support":admitted,
        "original_2026_paper_already_describes_them_as_correlated":True,
        "source_composition_configuration_direct_association_not_beetle_dispersal":True,
        "new_arthropod_effect_calculated":False,
        "no_raw_site_ID_cell_ID_species_or_coords_exported":True
    }

def run(source,out):
    result=analyze(read(source))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"nardi_composition_configuration_design_support.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();run(a.source,a.out)
