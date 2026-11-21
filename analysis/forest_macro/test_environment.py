import importlib.util
from pathlib import Path
import numpy as np
P=Path(__file__).with_name('extract_environment.py')
def module():
 assert P.exists(),'environment extractor not implemented';s=importlib.util.spec_from_file_location('e',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_tile_is_lowerleft_and_handles_western_longitude():
 m=module();assert m.tile_name(38.7,-27.2)=='N36W030';assert m.tile_name(39.5,-31.2)=='N39W033'

def test_tree_shrub_missing_and_water_are_explicit():
 m=module();a=np.array([[10,20],[0,80]],dtype='uint8');mask=np.ones((2,2),bool);w=np.ones((2,2));r=m.cover_stats(a,mask,w);assert r['valid_fraction']==.75;assert r['tree_cover_class_fraction']==1/3;assert r['tree_plus_shrub_class_fraction']==2/3;assert r['water_class_fraction']==1/3

def test_no_data_is_not_zero_cover():
 m=module();r=m.cover_stats(np.zeros((2,2),dtype='uint8'),np.ones((2,2),bool),np.ones((2,2)));assert r['tree_cover_class_fraction'] is None and r['valid_fraction']==0
