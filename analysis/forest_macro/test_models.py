import importlib.util,itertools,statistics
from pathlib import Path
import numpy as np,pandas as pd
import pytest
P=Path(__file__).with_name('fit_forest_models.py')
def mod():
 assert P.exists(),'forest response model not implemented'
 s=importlib.util.spec_from_file_location('models',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_rarefaction_matches_all_combinations():
 m=mod();sets=[{'a','b'},{'b'},{'b','c'},set()]
 expected=statistics.mean(len(set().union(*x)) for x in itertools.combinations(sets,2))
 assert m.rarefied(sets,2)==pytest.approx(expected)
 assert m.rarefied(sets,4)==3
 assert np.isnan(m.rarefied(sets,5))

def test_origin_does_not_promote_unknown():
 m=mod();assert m.origin('Endemic')=='endemic';assert m.origin('Native')=='native';assert m.origin('introduced')=='introduced';assert m.origin('uncertain')=='unknown'

def test_clustered_slope_and_weights():
 m=mod();rng=np.random.default_rng(12);x=rng.uniform(.1,.9,40);z=rng.uniform(1,4,40)
 d=pd.DataFrame({'plot_key':[f'p{i}' for i in range(40)],'cluster':[f'f{i//2}' for i in range(40)],'island':['A']*20+['B']*20,'exposure':x/.2,'elevation200':z,'response':2+3*x/.2+.5*z,'weight':1})
 r,f=m.fit(d,'BALA_pitfall','response');assert r['beta_per20pp']==pytest.approx(3);assert r['clusters']==20;assert r['plots']==40

def test_source_zero_and_duplicate_taxa():
 m=mod();o=pd.DataFrame({'source_core_id':['e1','e1','e2'],'scientificName':['A','A','B'],'taxonRank':['species']*3,'establishmentMeans':['endemic','endemic','unknown'],'phylum':['Arthropoda']*3,'occurrenceStatus':['present']*3})
 events=pd.DataFrame({'source_core_id':['e1','e2','e3'],'island':['A']*3})
 sets,a=m.event_sets(events,o);assert sets['e1']['endemic']=={'a'} and sets['e2']['total']=={'b'} and sets['e2']['native']==set();assert 'e3' not in sets;assert a['unlinked_events']==1
