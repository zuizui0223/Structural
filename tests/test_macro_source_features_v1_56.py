import math
from structural.macro_source_features import source_features,jeffreys_logit,EARTH_RADIUS_KM

def fixture():
 coords={"a":(0.,0.),"b":(0.,1.),"c":(0.,2.),"d":(1.,0.)}
 pool={"a":"p","b":"p","c":"p","d":"q"}
 adj={"p":{"a":[("b",1.)],"b":[("a",1.),("c",1.)],"c":[("b",1.)]},"q":{"d":[]}}
 return coords,pool,adj

def test_global_no_source_has_strict_beyond_earth_sentinel():
 coords,pool,adj=fixture()
 # use a valid 3-node target pool
 x=source_features(target="a",occupied_sources=[],coordinates=coords,pool_by_id=pool,
  adjacency_by_pool={"p":adj["p"],"q":{"d":[("d",1.)]}},
  scale_by_pool={"p":2.,"q":2.},max_edge_by_pool={"p":1.,"q":1.},node_count_by_pool={"p":3,"q":2})
 assert x.nearest_euclidean_km > math.pi*EARTH_RADIUS_KM
 assert x.euclidean_pressure==0
 assert x.nearest_graph_km==4.0
 assert x.graph_pressure==0

def test_graph_no_source_can_coexist_with_global_euclidean_source():
 coords,pool,adj=fixture()
 x=source_features(target="a",occupied_sources=["d"],coordinates=coords,pool_by_id=pool,
  adjacency_by_pool={"p":adj["p"],"q":{"d":[("d",1.)]}},
  scale_by_pool={"p":2.,"q":2.},max_edge_by_pool={"p":1.,"q":1.},node_count_by_pool={"p":3,"q":2})
 assert x.nearest_euclidean_km < math.pi*EARTH_RADIUS_KM
 assert x.euclidean_pressure>0
 assert x.nearest_graph_km==4.0
 assert x.graph_pressure==0

def test_zero_regional_trials_jeffreys_is_zero_logit():
 assert jeffreys_logit(0,0)==0.0
