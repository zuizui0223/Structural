"""Source-only field/table invariant audit of publisher-original Ecuador beetle ZIP.

No new ecological tests, p-values, hypotheses or changed source response scores.
Requires privately/local original source ZIP; only aggregated receipts are exported.
"""
import argparse, hashlib, io, json, re, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

SHA="8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d"
STAGES=("Agri","Reg1","Reg2","Old")
HOSTS=("CACAO","FERNAN SANCHEZ","GUABA","MASCAREI","SAPANILLO")

def norm(s): return "".join(re.findall("[A-Za-z0-9]",str(s))).lower()

def data(z,name):
    return pd.read_csv(io.BytesIO(z.read(name)),sep=";",dtype=str,keep_default_na=False)

def wide(z,name):
    a=data(z,name).set_index("Host")
    if set(a.index)!=set(HOSTS): raise ValueError("original Host source identity STOP")
    a=a.apply(pd.to_numeric,errors="raise")
    a.columns=[norm(c) for c in a.columns]
    if len(set(a.columns))!=a.shape[1] or "" in a.columns:
        raise ValueError("original morphospecies codebook STOP")
    return a.reindex(HOSTS)

def compare(a,b):
    cols=sorted(set(a.columns)|set(b.columns))
    return np.array_equal(
        a.reindex(index=HOSTS,columns=cols,fill_value=0).to_numpy(),
        b.reindex(index=HOSTS,columns=cols,fill_value=0).to_numpy())

def audit(path):
    raw=Path(path).read_bytes()
    if len(raw)!=11201 or hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError("source exact publisher ZIP SHA/size STOP")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=9: raise ValueError("original 9-file archive STOP")
        site=data(z,"PlotSpeciesIndiv_3.csv")
        log=data(z,"PlotLogSpeciesAbundancesDensity.csv")
        tax=data(z,"PlotKat4HostSpecIndiv_3.csv")
        byhost=wide(z,"HostBeetleIndiv_3.csv")
        bystage={s:wide(z,"a_"+s+"_3.csv") for s in STAGES}
    if len(site)!=61 or len(log)!=300 or len(tax)!=263:
        raise ValueError("source grain STOP")
    if not site.Plot.equals(site.Plot_ID) or site.Plot.duplicated().any():
        raise ValueError("source plot identity STOP")
    if log[["Plot","Host"]].duplicated().any() or not log.Plot.isin(site.Plot).all():
        raise ValueError("source log key STOP")
    if set(log.Host)!=set(HOSTS) or set(site.Category4)!=set(STAGES):
        raise ValueError("original categorical codebook STOP")
    for a,k in [(log,"Indiv"),(log,"Spec"),(site,"Individuals"),(site,"Species"),(tax,"Indiv")]:
        v=pd.to_numeric(a[k],errors="raise")
        if not np.isfinite(v).all() or (v<0).any() or (v!=np.floor(v)).any():
            raise ValueError("original numeric field STOP")
        a[k]=v.astype(int)
    if (log.Spec>log.Indiv).any() or not log.Spec.gt(0).equals(log.Indiv.gt(0)):
        raise ValueError("source observed zero/positive consistency STOP")
    opportunities=log.groupby("Plot").Host.nunique().value_counts().to_dict()
    if opportunities!={5:59,4:1,1:1}: raise ValueError("original opportunity STOP")
    site_tot=site.set_index("Plot").Individuals
    plot_tot=log.groupby("Plot").Indiv.sum()
    if not plot_tot.equals(site_tot.reindex(plot_tot.index)):
        raise ValueError("source adult totals plot-level STOP")
    joined=log.merge(site[["Plot","Category4"]],on="Plot",validate="many_to_one")
    stagecounts=joined.pivot_table(index="Category4",columns="Host",values="Indiv",aggfunc="sum")
    taxcounts=tax.pivot_table(index="Plot",columns="Host",values="Indiv",aggfunc="sum")
    if not stagecounts.sort_index().equals(taxcounts.sort_index()):
        raise ValueError("source 4 x 5 adult totals STOP")
    if tax[["Plot","Host","Morphospecies"]].duplicated().any():
        raise ValueError("source taxonomic duplicate key STOP")
    tax["canonical"]=tax.Morphospecies.map(norm)
    blank=tax[tax.canonical==""]
    if len(blank)!=1 or int(blank.Indiv.sum())!=2:
        raise ValueError("missing taxon original source identity STOP")
    named=tax[tax.canonical!=""]
    if named.canonical.nunique()!=91:raise ValueError("named morphospecies ID STOP")
    pooled=named.pivot_table(index="Host",columns="canonical",values="Indiv",aggfunc="sum",fill_value=0)
    if not compare(pooled,byhost):raise ValueError("pooled species abundance matrices STOP")
    for s in STAGES:
        g=named[named.Plot==s].pivot_table(index="Host",columns="canonical",values="Indiv",aggfunc="sum",fill_value=0)
        if not compare(g,bystage[s]):raise ValueError("stage species abundance matrices STOP")
    a=log.groupby("Plot").Spec.max()
    b=site.set_index("Plot").Species.reindex(a.index)
    bad=b<a
    classes=site.set_index("Plot").Category4.reindex(a.index)
    return {
        "schema":"structural.falconi2026_independent_source_invariant_audit.v1",
        "original_zip_sha256":SHA,"field_plots":61,"logged_host_records":300,
        "complete_5_host_plots":59,"published_recovered_logs":306,
        "adult_sum_log":int(log.Indiv.sum()),"adult_sum_stages":int(tax.Indiv.sum()),
        "adult_sum_named_taxa":int(byhost.to_numpy().sum()),
        "taxa_named":91,"blank_taxon_occurrence_rows":len(blank),
        "blank_taxon_adult_count":int(blank.Indiv.sum()),
        "blank_taxon_stage":"Old","blank_taxon_host":"FERNAN SANCHEZ",
        "all_61_original_plot_adult_totals_match":True,
        "all_20_original_stage_host_adult_totals_match":True,
        "all_4_stage_taxon_matrices_match":True,"pooled_host_taxon_matrix_matches":True,
        "source_species_richness_plot_smaller_than_single_log_count":int(bad.sum()),
        "source_species_richness_anomalies_by_stage":{s:int(((classes==s)&bad).sum()) for s in STAGES},
        "richness_semantics_reconciled":False,"original_missing_log_records_recovered":False,
        "new_ecological_effects_or_pvalues_scored":0,"raw_identifiers_or_taxa_exported":False,
        "status":"ADULT_ARITHMETIC_PASS_TAXON_AND_RICHNESS_DEFINITION_HOLD"}

def test():
    assert norm("BOLD:AGB1855")==norm("BOLDAGB1855")
    assert norm("")==""
    assert len(STAGES)==4 and len(HOSTS)==5
    print("SYNTHETIC_ORIGINAL_TAXON_NORMALIZATION_TEST_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source")
    parser.add_argument("--out")
    parser.add_argument("--test",action="store_true")
    args=parser.parse_args()
    if args.test:test()
    else:
        if not args.source or not args.out:parser.error("--source and --out required")
        result=audit(args.source)
        p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
        print("SOURCE_AUDIT_STATUS",result["status"])
