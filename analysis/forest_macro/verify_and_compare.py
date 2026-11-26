"""Supplementary covariate audit from cached responses; no original downloads.
Elevation was a prespecified adjustment variable, not the primary tree-cover test.
BH30 covers all tree/elevation coefficients including the origin contrast.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,patsy
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from fit_forest_models import fit,OUTCOMES

def cv(panel,channel,outcome):
    p=panel.copy();p['response']=p[outcome];p['elevation200']=p.source_elevation_m/200;p['exposure']=p.tree_cover_class_fraction_500m/.2
    if channel=='SLAM':p['weight']=1/p.groupby('plot_key').plot_key.transform('size')
    nuisance='1 + C(island)'+(' + C(year) + C(quarter) + log_days' if channel=='SLAM' else '')
    specs={'baseline':nuisance,'elevation':nuisance+' + elevation200','full':nuisance+' + elevation200 + exposure'}
    allx={name:patsy.dmatrix(spec,p,return_type='dataframe') for name,spec in specs.items()};pred=[];skips=[]
    for group in sorted(p.cluster.unique()):
        train=p.cluster!=group;test=~train
        if not set(p.loc[test,'island']).issubset(set(p.loc[train,'island'])):skips.append(group);continue
        estimates={};usable=True
        for label,x in allx.items():
            xtr=x.loc[train].to_numpy();xte=x.loc[test].to_numpy()
            if not np.allclose(xte@np.linalg.pinv(xtr)@xtr,xte,atol=1e-7):usable=False;break
            f=sm.WLS(p.loc[train,'response'],xtr,weights=p.loc[train,'weight']).fit();estimates[label]=f.predict(xte)
        if not usable:skips.append(group);continue
        for j,(_,row) in enumerate(p.loc[test].iterrows()):
            pred.append({'channel':channel,'outcome':outcome,'cluster':group,'plot_key':row.plot_key,'response':row.response,**{lab:float(pr[j]) for lab,pr in estimates.items()}})
    df=pd.DataFrame(pred)
    result={'channel':channel,'outcome':outcome,'tested_clusters':df.cluster.nunique() if len(df) else 0,'tested_plots':df.plot_key.nunique() if len(df) else 0,'skipped_clusters':'|'.join(skips)}
    if len(df):
        for lab in specs:
            result[lab+'_mse']=float(df.assign(error=(df.response-df[lab])**2).groupby('plot_key').error.mean().mean())
        result['elevation_vs_baseline_mse_reduction_pct']=100*(1-result['elevation_mse']/result['baseline_mse'])
        result['tree_added_mse_reduction_pct']=100*(1-result['full_mse']/result['elevation_mse'])
    return result,df

def run(out):
    out=Path(out);d=pd.read_csv(out/'response_environment_all.csv');coeff=[];loo=[];sens=[];pred=[];cvresults=[]
    for c,allc in d.groupby('channel'):
        p=allc[allc.primary_eligible].copy();p['exposure']=p.tree_cover_class_fraction_500m/.2
        for y in OUTCOMES:
            _,f=fit(p,c,y);r=f['robust'];cols=list(f['design'])
            for v in ('exposure','elevation200'):
                j=cols.index(v);lo,hi=r.conf_int()[j];coeff.append({'channel':c,'outcome':y,'predictor':v,'beta':r.params[j],'ci_low':lo,'ci_high':hi,'p':r.pvalues[j],'plots':p.plot_key.nunique(),'clusters':p.cluster.nunique()})
            for grouping in ('cluster','island'):
                for key in sorted(p[grouping].unique()):
                    sub=p[p[grouping]!=key]
                    try:
                        _,ff=fit(sub,c,y);idx=list(ff['design']).index('elevation200');b=ff['robust'].params[idx];loo.append({'channel':c,'outcome':y,'delete_type':grouping,'deleted':key,'elevation_beta':b,'status':'ok'})
                    except (ValueError,IndexError) as ex:loo.append({'channel':c,'outcome':y,'delete_type':grouping,'deleted':key,'elevation_beta':np.nan,'status':str(ex)})
            for scen,extra,log in [('log1p','',True),('habitat_or_month','C(habitat)' if c=='SLAM' else ('C(month) + host_code_n' if c=='BALA_foliage' else 'C(month)'),False)]:
                if log and y=='endemic_minus_introduced':continue
                try:
                    _,ff=fit(p,c,y,extra=extra,log=log);j=list(ff['design']).index('elevation200');rr=ff['robust'];ci=rr.conf_int()[j];sens.append({'channel':c,'outcome':y,'scenario':scen,'elevation_beta':rr.params[j],'low':ci[0],'high':ci[1],'p':rr.pvalues[j]})
                except ValueError as ex:sens.append({'channel':c,'outcome':y,'scenario':scen,'error':str(ex)})
            rr,pp=cv(p,c,y);cvresults.append(rr);pred.append(pp)
    co=pd.DataFrame(coeff);co['q_BH_30']=multipletests(co.p,method='fdr_bh')[1];co.to_csv(out/'all_landscape_elevation_coefficients.csv',index=False)
    pd.DataFrame(loo).to_csv(out/'elevation_leave_group_out.csv',index=False);pd.DataFrame(sens).to_csv(out/'elevation_sensitivities.csv',index=False);pd.DataFrame(cvresults).to_csv(out/'forest_block_prediction.csv',index=False);pd.concat(pred,ignore_index=True).to_csv(out/'forest_block_predictions_by_sample.csv',index=False)
    print(co[co.predictor=='elevation200'].to_string(index=False));print(pd.DataFrame(cvresults).to_string(index=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--results',type=Path,required=True);run(parser.parse_args().results)
