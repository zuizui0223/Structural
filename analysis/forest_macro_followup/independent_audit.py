"""Independent forest-macro response audit and exploratory paired-method model.
Uses previously extracted 2019-2022 records and saved PR469 outputs only.
"""
from __future__ import annotations
import argparse,hashlib,json,math,unicodedata
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import pandas as pd
import patsy
from scipy import stats
OUTCOMES=('total','endemic','native','introduced','endemic_minus_introduced')
GROUPS=('total','endemic','native','introduced','unknown')
ALIASES={'faial':'FAI','flores':'FLO','pico':'PIC','sao jorge':'SJG','sao miguel':'SMG','santa maria':'SMR','terceira':'TER','graciosa':'GRA'}
def normalize(x):return ' '.join(unicodedata.normalize('NFKC',str(x or '')).casefold().split())
def isl(x):return ALIASES.get(''.join(c for c in unicodedata.normalize('NFKD',normalize(x)) if not unicodedata.combining(c)),str(x).upper())
def rarefy(sets,m):
    n=len(sets)
    if m>n or m<1:return float('nan')
    incidence=Counter(t for s in sets for t in s)
    return math.fsum(1-(math.prod((n-f-j)/(n-j) for j in range(m)) if n-f>=m else 0) for f in incidence.values())
def bh(p):
    p=np.asarray(p);order=np.argsort(p);v=p[order]*len(p)/np.arange(1,len(p)+1);q=np.minimum.accumulate(v[::-1])[::-1];out=np.empty(len(p));out[order]=np.minimum(q,1);return out

def wls_cluster(X,y,w,groups):
    X=np.asarray(X,float);y=np.asarray(y,float);w=np.asarray(w,float);groups=np.asarray(groups)
    n,k=X.shape
    if len(y)!=n or len(w)!=n or not np.isfinite(X).all() or not np.isfinite(y).all() or np.any(w<=0):raise ValueError('Invalid finite positive-weight inputs')
    if np.linalg.matrix_rank(X)<k:raise ValueError('Deficient design rank')
    G=len(np.unique(groups))
    if G<3 or n<=k:raise ValueError('Insufficient clusters or residual degrees')
    bread=np.linalg.inv(X.T@(w[:,None]*X));beta=bread@(X.T@(w*y));resid=y-X@beta
    U=np.stack([(X[g==groups].T@(w[g==groups]*resid[g==groups])) for g in np.unique(groups)])
    cov=bread@(U.T@U)@bread*(G/(G-1))*((n-1)/(n-k));se=np.sqrt(np.maximum(np.diag(cov),0));crit=stats.t.ppf(.975,G-1)
    return {'beta':beta,'se':se,'ci':np.column_stack([beta-crit*se,beta+crit*se]),'p':2*stats.t.sf(np.divide(abs(beta),se,out=np.full_like(se,np.inf),where=se>0),G-1),'clusters':G,'cov':cov}

def design(d,paired=False,adjusted=False):
    f='1+C(island)+elevation200'
    if not paired and d.channel.iloc[0]=='SLAM':f+=' + C(year)+C(quarter)+log_days'
    if paired and adjusted:f+=' + C(month)+host_code_n'
    f+=' + exposure'
    X=patsy.dmatrix(f,d,return_type='dataframe');keep=[]
    for c in X:
        if np.linalg.matrix_rank(X[keep+[c]].to_numpy())>len(keep):keep.append(c)
        elif c in ('exposure','elevation200'):raise ValueError('Target not identifiable')
    return X[keep]

def pair_frame(d):
    a=d[d.channel=='BALA_foliage'].copy();b=d[d.channel=='BALA_pitfall'].copy()
    if a.plot_key.duplicated().any() or b.plot_key.duplicated().any():raise ValueError('duplicate plot-method rows')
    if set(a.plot_key)!=set(b.plot_key):raise ValueError('Unmatched physical plot keys')
    a=a.set_index('plot_key').sort_index();b=b.set_index('plot_key').loc[a.index]
    for c in ('island','cluster','source_elevation_m','tree_cover_class_fraction_500m'):
        if not a[c].equals(b[c]):raise ValueError('Paired source covariate differs: '+c)
    # Identical plot is not sufficient: dates must also match.
    same=(a.year==b.year)&(a.month==b.month)
    a=a.loc[same];b=b.loc[same]
    out=a[['island','cluster','source_elevation_m','tree_cover_class_fraction_500m','year','month','host_code_n']].copy()
    for y in OUTCOMES:out[y]=a[y+'_m10']-b[y+'_m10']
    out['elevation200']=out.source_elevation_m/200;out['exposure']=out.tree_cover_class_fraction_500m/.2
    return out.reset_index()

def reconstruct_counts(inputs,modeldir):
    manifest=json.loads((inputs/'extraction_provenance.json').read_text());all_events=[];all_sets={};quality={}
    for name,digest in manifest['file_sha256'].items():
        if hashlib.sha256((inputs/name).read_bytes()).hexdigest()!=digest:raise ValueError('Input hash changed: '+name)
    for dataset in ('BALA','SLAM'):
        e=pd.read_csv(inputs/f'{dataset}_events_2019_2022.csv',keep_default_na=False);o=pd.read_csv(inputs/f'{dataset}_occurrences_2019_2022.csv',keep_default_na=False)
        ids=set(e.source_core_id);source_island=dict(zip(e.source_core_id,e.island));seen=set();records=[];states=defaultdict(set);q=Counter()
        for r in o.to_dict('records'):
            eid=r['source_core_id']
            if eid not in ids:raise ValueError('Unlinked selected occurrence')
            seen.add(eid);q['rows']+=1
            if r.get('phylum') and normalize(r['phylum'])!='arthropoda':continue
            if normalize(r.get('occurrenceStatus'))=='absent':continue
            quant=r.get('organismQuantity',r.get('individualCount',''))
            if str(quant).strip():
                try:
                    if float(quant)<=0:q['nonpositive']+=1;continue
                except ValueError:q['unparsed_quantity']+=1
            tax=normalize(r.get('scientificName'));rank=normalize(r.get('taxonRank'))
            if rank not in ('species','subspecies') or not tax:q['rank_excluded']+=1;continue
            s=normalize(r.get('establishmentMeans'));g=s if s in ('endemic','native','introduced') else 'unknown'
            records.append((eid,tax,g));q['named']+=1;q['named_'+g]+=1
            if g!='unknown':states[(source_island[eid],tax)].add(g)
        conflict={key for key,v in states.items() if len(v)>1};sets={eid:{g:set() for g in GROUPS} for eid in seen}
        for eid,tax,g in records:
            if (source_island[eid],tax) in conflict:g='unknown'
            sets[eid]['total'].add(tax);sets[eid][g].add(tax)
        e['dataset']=dataset;e['plot_key']=dataset+'|'+e.island.map(isl)+'|'+e.locationID.str.strip()
        for g in GROUPS:e[g]=e.source_core_id.map(lambda eid:len(sets[eid][g]) if eid in sets else np.nan)
        q['events']=len(e);q['events_missing_records']=len(ids-seen);q['origin_conflicts']=len(conflict);quality[dataset]=dict(q)
        all_events.append(e);all_sets[dataset]=sets
    events=pd.concat(all_events,ignore_index=True)
    ref=pd.read_csv(modeldir/'event_richness_selected.csv',keep_default_na=False)
    comp=events[['dataset','source_core_id',*GROUPS]].merge(ref[['dataset','source_core_id',*GROUPS]],on=['dataset','source_core_id'],suffixes=('_audit','_saved'),validate='one_to_one')
    max_event=max(float(np.max(abs(comp[g+'_audit']-comp[g+'_saved']))) for g in GROUPS)
    if max_event>0 or len(comp)!=1911:raise ValueError('Event-level richness mismatch')
    d=pd.read_csv(modeldir/'response_environment_all.csv');checks=[]
    bala=events[events.dataset=='BALA']
    for r in d[d.channel!='SLAM'].to_dict('records'):
        method='Pitfall solution' if r['channel']=='BALA_pitfall' else 'Open beating tray (with bag)'
        cores=bala[(bala.plot_key==r['plot_key'])&(bala.samplingProtocol==method)].source_core_id.tolist()
        for g in GROUPS:
            ss=[all_sets['BALA'][k][g] for k in cores]
            for suffix,m in [('',int(r['rarefaction_m'])),('_m10',10)]:
                value=rarefy(ss,m);checks.append({'channel':r['channel'],'plot_key':r['plot_key'],'outcome':g+suffix,'reconstructed':value,'saved':r[g+suffix],'difference':value-r[g+suffix]})
    check=pd.DataFrame(checks)
    if abs(check.difference).max()>1e-10:raise ValueError('Exact rarefaction mismatch')
    return d,events,quality,check,{'event_group_count_values_reconciled':len(comp)*len(GROUPS),'max_event_difference':max_event,'rarefaction_values_reconciled':len(check),'max_rarefaction_difference':float(abs(check.difference).max())}

def run(inputs,models,out):
    inputs=Path(inputs);models=Path(models);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    d,events,quality,rare,counts=reconstruct_counts(inputs,models);rare.to_csv(out/'independent_rarefaction_check.csv',index=False)
    ref=pd.read_csv(models/'all_landscape_elevation_coefficients.csv');rep=[]
    for channel,dd in d.groupby('channel'):
        dd=dd[dd.primary_eligible].copy();dd['exposure']=dd.tree_cover_class_fraction_500m/.2
        w=(1/dd.groupby('plot_key').plot_key.transform('size')).to_numpy() if channel=='SLAM' else np.ones(len(dd))
        X=design(dd)
        for y in OUTCOMES:
            fit=wls_cluster(X,dd[y],w,dd.cluster)
            for target in ('exposure','elevation200'):
                j=X.columns.get_loc(target);r=ref[(ref.channel==channel)&(ref.outcome==y)&(ref.predictor==target)].iloc[0]
                rep.append({'channel':channel,'outcome':y,'predictor':target,'beta':fit['beta'][j],'ci_low':fit['ci'][j,0],'ci_high':fit['ci'][j,1],'p':fit['p'][j],'beta_difference':fit['beta'][j]-r.beta,'ci_low_difference':fit['ci'][j,0]-r.ci_low,'ci_high_difference':fit['ci'][j,1]-r.ci_high,'p_difference':fit['p'][j]-r.p})
    rep=pd.DataFrame(rep);rep['q_BH_30_recomputed']=bh(rep.p)
    err=float(rep[['beta_difference','ci_low_difference','ci_high_difference','p_difference']].abs().max().max())
    if err>1e-8:raise ValueError('Manual weighted/sandwich coefficient mismatch')
    rep.to_csv(out/'independent_coefficient_check.csv',index=False)
    pair=pair_frame(d)
    bplot=d[d.channel=='BALA_pitfall'].set_index('plot_key');fplot=d[d.channel=='BALA_foliage'].set_index('plot_key')
    excluded=[]
    for key in sorted(set(bplot.index)-set(pair.plot_key)):
        excluded.append({'plot_key':key,'ground_year':int(bplot.loc[key,'year']),'foliage_year':int(fplot.loc[key,'year']),'ground_month':int(bplot.loc[key,'month']),'foliage_month':int(fplot.loc[key,'month']),'reason':'different_source_sampling_year_or_month'})
    pd.DataFrame(excluded).to_csv(out/'paired_temporal_exclusions.csv',index=False)
    pair.to_csv(out/'paired_method_difference_data.csv',index=False);coeff=[];loo=[]
    for adjusted in (False,True):
        X=design(pair,paired=True,adjusted=adjusted)
        for y in OUTCOMES:
            fit=wls_cluster(X,pair[y],np.ones(len(pair)),pair.cluster)
            for target in ('elevation200','exposure'):
                j=X.columns.get_loc(target);coeff.append({'outcome':y,'predictor':target,'scenario':'month_host_adjusted' if adjusted else 'primary_pair','n_pairs':len(pair),'n_clusters':fit['clusters'],'beta':fit['beta'][j],'ci_low':fit['ci'][j,0],'ci_high':fit['ci'][j,1],'p':fit['p'][j],'contrast':'foliage_minus_pitfall_both_m10'})
            if not adjusted:
                for groupcol in ('cluster','island'):
                    for k in sorted(pair[groupcol].unique()):
                        sub=pair[pair[groupcol]!=k];xx=design(sub,paired=True)
                        ff=wls_cluster(xx,sub[y],np.ones(len(sub)),sub.cluster)
                        for target in ('elevation200','exposure'):
                            j=xx.columns.get_loc(target);loo.append({'outcome':y,'predictor':target,'deleted_type':groupcol,'deleted':k,'beta':ff['beta'][j]})
    co=pd.DataFrame(coeff);co['q_BH_within10']=np.nan
    for label in co.scenario.unique():
        loc=co.scenario==label;co.loc[loc,'q_BH_within10']=bh(co.loc[loc,'p'])
    co.to_csv(out/'paired_ground_foliage_models.csv',index=False);pd.DataFrame(loo).to_csv(out/'paired_leave_group_out.csv',index=False)
    pred=pd.read_csv(models/'forest_block_predictions_by_sample.csv');cv=[];cvref=pd.read_csv(models/'forest_block_prediction.csv')
    for (channel,y),pp in pred.groupby(['channel','outcome']):
        r={'channel':channel,'outcome':y,'plots':pp.plot_key.nunique(),'clusters':pp.cluster.nunique()}
        for name in ('baseline','elevation','full'):
            losses=pp.assign(sq=(pp.response-pp[name])**2).groupby('plot_key').sq.mean();r[name+'_mse']=float(losses.mean())
        r['elevation_reduction_pct']=100*(1-r['elevation_mse']/r['baseline_mse']);r['tree_reduction_pct']=100*(1-r['full_mse']/r['elevation_mse'])
        old=cvref[(cvref.channel==channel)&(cvref.outcome==y)].iloc[0]
        for name in ('baseline_mse','elevation_mse','full_mse'):
            if abs(old[name]-r[name])>1e-10:raise ValueError('CV plot-weighted error mismatch')
        cv.append(r)
    pd.DataFrame(cv).to_csv(out/'independent_forest_block_prediction_check.csv',index=False)
    summary={'status':'INDEPENDENT_NUMERICAL_RECONSTRUCTION_AND_EXPLORATORY_PAIRED_ANALYSIS_COMPLETE','source_model_run':42210266917,'source_response_run':42207600533,'counts':counts,'quality':quality,'coefficient_rows_recomputed':len(rep),'max_coefficient_or_interval_difference':err,'prediction_rows_reconciled':len(pred),'paired_method_plots':len(pair),'paired_clusters':pair.cluster.nunique(),'paired_islands':pair.island.nunique(),'new_original_archives_downloaded':0,'new_historical_biological_scorer_executions':0,'scope':'Exploratory forest-environment associations, not causal elevation effects or direct canopy-height gradients. Shared BALA/SLAM sites not independent replication.'}
    summary['outputs_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}
    (out/'audit_receipt.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));print(co.to_string(index=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--models',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.inputs,a.models,a.out)
