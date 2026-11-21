import importlib.util,io,zipfile
from pathlib import Path
import pytest
P=Path(__file__).with_name('forest_plot_ledger.py')
def module():
    assert P.exists(), 'implementation not yet present'
    sp=importlib.util.spec_from_file_location('ledger',P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

def event(site='x',lat='38',lon='-27',island='ter',year='2020',eid='1'):
    return dict(locationID=site,decimalLatitude=lat,decimalLongitude=lon,island=island,year=year,eventID=eid,samplingProtocol='SLAM',habitat='native forest',locality='fragment A')

def test_reader_never_opens_occurrence():
    m=module();b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        z.writestr('meta.xml','<archive><core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>event.txt</location></files><id index="0"/><field index="1" term="http://rs.tdwg.org/dwc/terms/locationID"/></core><extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>DO_NOT_READ</location></files></extension></archive>')
        z.writestr('event.txt','e1\tsite1\n')
    rows,meta=m.read_events(b.getvalue());assert len(rows)==1 and rows[0]['locationID']=='site1';assert meta['members_read']==['meta.xml','event.txt']

def test_repeats_are_not_sites_and_metadata_retained():
    m=module();p,w=m.summarize('TEST',[event(),event(eid='2',year='2021')]);assert len(p)==1 and p[0]['event_n']==2 and p[0]['years']=='2020|2021' and len(w)==2

def test_missing_coordinates_not_dropped():
    m=module();p,w=m.summarize('TEST',[event(lat='',lon='')]);assert len(p)==1 and p[0]['latitude'] is None and p[0]['coordinate_valid_event_n']==0

def test_coordinate_drift_and_same_coord_ids_preserved():
    m=module();p,w=m.summarize('TEST',[event(),event(lat='38.01',eid='2'),event(site='y',eid='3')]);assert len(p)==2 and p[0]['coordinate_spread_m']>500

def test_crosssource_candidates_not_merge_and_haversine():
    m=module();a,_=m.summarize('A',[event()]);b,_=m.summarize('B',[event(site='y',lat='38.0001')]);pairs=m.cross_pairs(a+b);assert len(pairs)==1 and 10<pairs[0]['distance_m']<12 and len(a+b)==2
