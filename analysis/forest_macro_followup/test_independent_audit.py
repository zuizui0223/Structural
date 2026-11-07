import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
P=Path(__file__).with_name('independent_audit.py')
def mod():
    assert P.exists()
    s=importlib.util.spec_from_file_location('audit',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_rarefaction_exact_known_sets():
    m=mod();sets=[{'a','b'},{'a'},{'c'}]
    assert m.rarefy(sets,1)==pytest.approx(4/3)
    assert m.rarefy(sets,2)==pytest.approx(7/3)
    assert m.rarefy(sets,3)==3
    assert np.isnan(m.rarefy(sets,4))

def test_cluster_wls_matches_external_statsmodels():
    import statsmodels.api as sm
    rng=np.random.default_rng(438);X=np.column_stack([np.ones(24),rng.normal(size=24)]);y=2+X[:,1]+rng.normal(size=24);w=rng.uniform(.5,1,24);g=np.repeat(np.arange(6),4)
    r=mod().wls_cluster(X,y,w,g)
    q=sm.WLS(y,X,weights=w).fit().get_robustcov_results(cov_type='cluster',groups=g,use_correction=True,df_correction=True,use_t=True)
    np.testing.assert_allclose(r['beta'],q.params,atol=1e-12)
    np.testing.assert_allclose(r['se'],q.bse,atol=1e-12)
    np.testing.assert_allclose(r['ci'],q.conf_int(),atol=1e-12)

def test_paired_grain_preserves_foliage_minus_ground():
    m=mod();rows=[]
    for site in range(4):
      for method,offset in [('BALA_foliage',2),('BALA_pitfall',0)]:
        r={'plot_key':str(site),'channel':method,'island':'A','cluster':str(site),'source_elevation_m':site*100,'tree_cover_class_fraction_500m':.5,'year':2021,'month':8,'host_code_n':2 if method.endswith('foliage') else 0}
        for origin in m.OUTCOMES:r[origin+'_m10']=5+site+offset
        rows.append(r)
    pair=m.pair_frame(pd.DataFrame(rows));assert len(pair)==4
    assert (pair['native']==2).all()
    with pytest.raises(ValueError,match='duplicate'):
      m.pair_frame(pd.concat([pd.DataFrame(rows),pd.DataFrame(rows[:1])]))

def test_rarefaction_invariant_to_species_and_sample_order():
    m=mod();s=[{'a'},{'a','b'},set(),{'b','c'}]
    assert m.rarefy(s,2)==pytest.approx(m.rarefy(list(reversed(s)),2))

def test_rank_deficient_design_fails_explicitly():
    with pytest.raises(ValueError,match='rank'):
      mod().wls_cluster(np.ones((10,2)),np.arange(10),np.ones(10),np.repeat([1,2,3,4,5],2))

def test_paired_analysis_excludes_asynchronous_years_without_outcome_selection():
    m=mod();rows=[]
    for site in range(4):
      for method in ['BALA_foliage','BALA_pitfall']:
        r={'plot_key':str(site),'channel':method,'island':'A','cluster':str(site),'source_elevation_m':100,'tree_cover_class_fraction_500m':.5,'year':2022 if site==3 and method=='BALA_foliage' else 2021,'month':8,'host_code_n':2}
        for origin in m.OUTCOMES:r[origin+'_m10']=site+2
        rows.append(r)
    pairs=m.pair_frame(pd.DataFrame(rows))
    assert set(pairs.plot_key)=={'0','1','2'}
