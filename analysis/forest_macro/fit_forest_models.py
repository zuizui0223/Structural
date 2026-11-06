"""Retrospective forest-landscape association, separated by collection channel.
Reads selected2019-2022 responses and frozen2021 environmental ledger.
No requests or old historical scorer imports. Detected richness is not occupancy.
"""
from __future__ import annotations
import argparse,json,math,re,unicodedata,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
GROUPS=('total','endemic','native','introduced','unknown')
OUTCOMES=('total','endemic','native','introduced','endemic_minus_introduced')
ALIASES={'faial':'FAI','fai':'FAI','flores':'FLO','flo':'FLO','pico':'PIC','pic':'PIC','sao jorge':'SJG','sjg':'SJG','sao miguel':'SMG','smg':'SMG','santa maria':'SMR','smr':'SMR','terceira':'TER','ter':'TER','graciosa':'GRA','gra':'GRA'}
def norm(v):return ' '.join(unicodedata.normalize('NFKC',str(v or '')).casefold().split())
def plain(v):return ''.join(c for c in unicodedata.normalize('NFKD',norm(v)) if not unicodedata.combining(c))
def origin(v):
    s=norm(v).replace('_',' ').replace('-',' ')
    if s in ('endemic','azorean endemic','native endemic'):return 'endemic'
    if s in ('native','indigenous','native non endemic','native nonendemic'):return 'native'
    if s in ('introduced','exotic','alien','non native','naturalized','naturalised','invasive'):return 'introduced'
    return 'unknown'
def rarefied(sets,m):
    n=len(sets)
    if n<m or m<1:return float('nan')
    counts=Counter(s for event in sets for s in set(event));den=math.comb(n,m)
    return float(math.fsum(1-(math.comb(n-f,m)/den if n-f>=m else 0) for f in counts.values()))

def event_sets(events,occ):
    wanted=set(events.source_core_id);seen=set(occ.source_core_id)&wanted
    eisl=dict(zip(events.source_core_id,events.island));out={k:{g:set() for g in GROUPS} for k in seen}
    audit=Counter();states=defaultdict(set);accepted=[]
    for r in occ.to_dict('records'):
        core=r['source_core_id']
        if core not in wanted:continue
        audit['source_rows']+=1
        if r.get('phylum') and norm(r['phylum'])!='arthropoda':audit['non_arthropods']+=1;continue
        if norm(r.get('occurrenceStatus'))=='absent':audit['explicit_absence_rows']+=1;continue
        quantity=r.get('organismQuantity',r.get('individualCount',''))
        try:
            if str(quantity).strip() and float(quantity)<=0:audit['nonpositive_quantity_rows']+=1;continue
        except (TypeError,ValueError):audit['unparsed_quantity_rows']+=1
        if norm(r.get('taxonRank')) not in ('species','subspecies') or not norm(r.get('scientificName')):audit['excluded_rank_or_unnamed']+=1;continue
        tax=norm(r['scientificName']);status=origin(r.get('establishmentMeans'));accepted.append((core,tax,status));audit['named_rows']+=1;audit['named_origin_'+status]+=1
        if status!='unknown':states[(eisl[core],tax)].add(status)
    conflict={k for k,v in states.items() if len(v)>1}
    for core,tax,status in accepted:
        if (eisl[core],tax) in conflict:status='unknown'
        out[core]['total'].add(tax);out[core][status].add(tax)
    audit['origin_conflicting_island_taxa']=len(conflict);audit['unlinked_events']=len(wanted-seen);audit['events_with_any_record']=len(seen)
    audit['events_without_named_species']=sum(not v['total'] for v in out.values())
    return out,dict(audit)

def prepare(inputs,environment,out):
    env=pd.read_csv(environment);env['plot_key']=env.plot_key.str.strip();assert env.plot_key.is_unique
    if 'source_elevation_m' not in env:
        env['source_elevation_m']=pd.to_numeric(env.minimum_elevation_source_values,errors='coerce')
    if 'source_fragment_or_locality_label' not in env:
        labels={}
        for name in ('BALA','SLAM'):
            meta=pd.read_csv(inputs/f'{name}_events_2019_2022.csv',keep_default_na=False)
            meta['plot_key']=name+'|'+meta.island.map(lambda v:ALIASES.get(plain(v),str(v).upper()))+'|'+meta.locationID.str.strip()
            for key,x in meta.groupby('plot_key'):
                vv=set(x.locationRemarks.str.strip())-{''}
                if len(vv)!=1:raise ValueError('Ambiguous forest-cluster label: '+key)
                labels[key]=next(iter(vv))
        env['source_fragment_or_locality_label']=env.plot_key.map(labels)
    allrows=[];all_event=[];audits={}
    for dataset in ('BALA','SLAM'):
        e=pd.read_csv(inputs/f'{dataset}_events_2019_2022.csv',keep_default_na=False)
        o=pd.read_csv(inputs/f'{dataset}_occurrences_2019_2022.csv',keep_default_na=False)
        assert e.source_core_id.is_unique
        e['island']=e.island.map(lambda v:ALIASES.get(plain(v),str(v).upper()))
        e['plot_key']=dataset+'|'+e.island+'|'+e.locationID.str.strip()
        e['start']=pd.to_datetime(e.eventDate.str.split('/').str[0]);e['end']=pd.to_datetime(e.eventDate.str.split('/').str[-1]);e['year']=e.start.dt.year;e['month']=e.start.dt.month;e['quarter']=(e.start+(e.end-e.start)/2).dt.quarter
        assert e.year.between(2019,2022).all()
        sets,audit=event_sets(e,o);audits[dataset]=audit;e['record_linked']=e.source_core_id.isin(sets)
        audit['origin_vocab']=o.establishmentMeans.value_counts().to_dict();audit['rank_vocab']=o.taxonRank.value_counts().to_dict()
        for g in GROUPS:e[g]=e.source_core_id.map(lambda k:len(sets[k][g]) if k in sets else np.nan)
        e['dataset']=dataset;e['endemic_minus_introduced']=e.endemic-e.introduced
        all_event.append(e)
        if dataset=='BALA':
            for (plot,method),x in e.groupby(['plot_key','samplingProtocol']):
                channel='BALA_pitfall' if method=='Pitfall solution' else 'BALA_foliage';m=23 if channel=='BALA_pitfall' else 10
                x=x[x.record_linked];rec={'plot_key':plot,'dataset':dataset,'channel':channel,'year':int(x.year.iloc[0]),'month':int(x.month.iloc[0]),'quarter':int(x.quarter.iloc[0]),'sampling_events':len(x),'rarefaction_m':m,'host_code_n':x.fieldNumber.str.split('-').str[0].nunique() if channel=='BALA_foliage' else 0,'duration_days':np.nan,'weight':1}
                for g in GROUPS:
                    ss=[sets[k][g] for k in x.source_core_id];rec[g]=rarefied(ss,m);rec[g+'_raw']=len(set().union(*ss));rec[g+'_m10']=rarefied(ss,10)
                rec['endemic_minus_introduced']=rec['endemic']-rec['introduced'];rec['endemic_minus_introduced_m10']=rec['endemic_m10']-rec['introduced_m10'];allrows.append(rec)
        else:
            e['duration_days']=pd.to_numeric(e.sampleSizeValue,errors='coerce');audit['duration_vs_dates_mismatch_events']=int(((e.end-e.start).dt.days!=e.duration_days).sum())
            e['channel']='SLAM';e['host_code_n']=np.nan;e['sampling_events']=1;e['rarefaction_m']=np.nan
            allrows+=e[e.record_linked].to_dict('records')
    d=pd.DataFrame(allrows);d=d.drop(columns=[c for c in ['island','latitude','longitude','habitat_values','source_elevation_m','dataset'] if c in d])
    d=d.merge(env,on='plot_key',how='left',validate='many_to_one',indicator=True)
    if not (d._merge=='both').all():raise ValueError('environment join failed')
    d=d.drop(columns='_merge');d['elevation200']=d.source_elevation_m/200;d['log_days']=np.log(d.duration_days/90)
    d['cluster']=d.dataset+'|'+d.island+'|'+d.source_fragment_or_locality_label.map(lambda v:re.sub(r'^nff\s+','',plain(v)))
    d['habitat']=d.habitat_values.map(norm)
    d['primary_eligible']=(d.channel!='SLAM')|d.duration_days.between(60,120)
    d['weight']=1.
    ix=d.channel=='SLAM';d.loc[ix,'weight']=1/d[ix].groupby('plot_key').plot_key.transform('size')
    d.to_csv(out/'response_environment_all.csv',index=False)
    pd.concat(all_event,ignore_index=True).to_csv(out/'event_richness_selected.csv',index=False)
    audits['panels']={k:{'rows_all':len(v),'plots_all':v.plot_key.nunique(),'primary_rows':int(v.primary_eligible.sum()),'primary_plots':v[v.primary_eligible].plot_key.nunique(),'clusters':v.cluster.nunique(),'islands':v.island.nunique()} for k,v in d.groupby('channel')}
    (out/'response_quality.json').write_text(json.dumps(audits,indent=2,ensure_ascii=False)+'\n')
    return d

def design(d,channel,extra=''):
    f='1 + C(island) + elevation200'
    if channel=='SLAM':f+=' + C(year) + C(quarter) + log_days'
    if extra:f+=' + '+extra
    f+=' + exposure'
    x=patsy.dmatrix(f,d,return_type='dataframe')
    kept=[];rank=0
    for c in x:
        trial=x[kept+[c]].to_numpy();newrank=np.linalg.matrix_rank(trial)
        if newrank>rank:kept.append(c);rank=newrank
        elif c=='exposure':raise ValueError('exposure not estimable conditional on covariates')
    return x[kept]

def fit(d,channel,outcome,extra='',log=False):
    d=d.copy();d['response']=np.log1p(d[outcome]) if log else d[outcome];d=d.dropna(subset=['response','exposure','elevation200','cluster'])
    if channel=='SLAM':d['weight']=1/d.groupby('plot_key').plot_key.transform('size')
    x=design(d,channel,extra);w=d.weight.to_numpy(float)
    if len(d)<=x.shape[1]+1 or d.cluster.nunique()<3:raise ValueError('insufficient independent model support')
    model=sm.WLS(d.response,x,weights=w).fit();robust=model.get_robustcov_results(cov_type='cluster',groups=d.cluster,use_correction=True,df_correction=True,use_t=True)
    j=list(x).index('exposure');ci=robust.conf_int()[j];nuis=x.drop(columns='exposure');xres=sm.WLS(x.exposure,nuis,weights=w).fit().resid
    info={'channel':channel,'outcome':outcome,'beta_per20pp':float(robust.params[j]),'se_cluster':float(robust.bse[j]),'ci_low':float(ci[0]),'ci_high':float(ci[1]),'p':float(robust.pvalues[j]),'rows':len(d),'plots':d.plot_key.nunique(),'clusters':d.cluster.nunique(),'islands':d.island.nunique(),'model_rank':x.shape[1],'cluster_df':float(robust.df_resid_inference),'r2':float(model.rsquared),'exposure_residual_sd_pp':float(np.sqrt(np.average(xres**2,weights=w))*.2*100),'model_columns':'|'.join(x.columns),'outcome_scale':'log1p' if log else 'richness'}
    return info,{'model':model,'robust':robust,'data':d,'design':x,'x_resid':xres}

def main_models(d,out):
    primary=[];sensitivity=[];deleted=[]
    exposures={'primary_tree500':'tree_cover_class_fraction_500m','tree100':'tree_cover_class_fraction_100m','tree1000':'tree_cover_class_fraction_1000m','woody500':'tree_plus_shrub_class_fraction_500m','position_min':'tree_cover_500m_45m_offset_min','position_max':'tree_cover_500m_45m_offset_max'}
    for channel,allc in d.groupby('channel'):
        panel=allc[allc.primary_eligible].copy()
        for scenario,col in exposures.items():
            p=panel.copy();p['exposure']=p[col]/.2
            for outcome in OUTCOMES:
                r,f=fit(p,channel,outcome);r['scenario']=scenario
                (primary if scenario=='primary_tree500' else sensitivity).append(r)
                if scenario=='primary_tree500':
                    for grouping in ('cluster','island'):
                        for key in sorted(p[grouping].unique()):
                            sub=p[p[grouping]!=key]
                            try:rr,_=fit(sub,channel,outcome);deleted.append({'channel':channel,'outcome':outcome,'deleted_type':grouping,'deleted':key,'beta':rr['beta_per20pp'],'status':'ok'})
                            except ValueError as exc:deleted.append({'channel':channel,'outcome':outcome,'deleted_type':grouping,'deleted':key,'status':str(exc)})
        p=panel.copy();p['exposure']=p.tree_cover_class_fraction_500m/.2
        for outcome in OUTCOMES:
            if outcome!='endemic_minus_introduced':
                r,_=fit(p,channel,outcome,log=True);r['scenario']='log1p';sensitivity.append(r)
            if channel=='SLAM':
                r,_=fit(p,channel,outcome,extra='C(habitat)');r['scenario']='condition_habitat';sensitivity.append(r)
                a=allc[allc.duration_days>0].copy();a['exposure']=a.tree_cover_class_fraction_500m/.2;r,_=fit(a,channel,outcome);r['scenario']='all_positive_durations';sensitivity.append(r)
            else:
                r,_=fit(p,channel,outcome,extra='C(month)'+(' + host_code_n' if channel=='BALA_foliage' else ''));r['scenario']='month_host_adjusted';sensitivity.append(r)
                if channel=='BALA_pitfall':
                    a=p.copy();a[outcome]=a[outcome+'_m10'];r,_=fit(a,channel,outcome);r['scenario']='rarefaction10';sensitivity.append(r)
    pr=pd.DataFrame(primary);pr['q_BH_15']=multipletests(pr.p,method='fdr_bh')[1];pr.to_csv(out/'primary_models.csv',index=False);pd.DataFrame(sensitivity).to_csv(out/'sensitivity_models.csv',index=False);pd.DataFrame(deleted).to_csv(out/'leave_group_out.csv',index=False)
    print(pr[['channel','outcome','beta_per20pp','ci_low','ci_high','p','q_BH_15','plots','clusters']].to_string(index=False))
    return pr

def run(inputs,environment,out):
    inputs=Path(inputs);out=Path(out);out.mkdir(exist_ok=True,parents=True)
    p=json.loads((inputs/'extraction_provenance.json').read_text())
    for n,s in p['file_sha256'].items():assert hashlib.sha256((inputs/n).read_bytes()).hexdigest()==s
    d=prepare(inputs,environment,out);main_models(d,out)
    manifest={'environment_sha256':hashlib.sha256(Path(environment).read_bytes()).hexdigest(),'source_extraction':p,'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')},'design':'retrospective exploratory, primary15 tests, no causal identification, no source pooling','software':{'statsmodels':__import__('statsmodels').__version__,'pandas':pd.__version__,'numpy':np.__version__}}
    (out/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--environment',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.inputs,a.environment,a.out)
