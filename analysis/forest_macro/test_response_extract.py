import importlib.util,io,zipfile
from pathlib import Path
import pytest
P=Path(__file__).with_name('response_extract.py')
def mod():
    assert P.exists(), 'response extractor not implemented'
    s=importlib.util.spec_from_file_location('extract',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def fixture():
    meta='<archive><core rowType="http://rs.tdwg.org/dwc/terms/Event"><files><location>event.txt</location></files><id index="0"/><field index="1" term="http://rs.tdwg.org/dwc/terms/eventDate"/><field index="2" term="http://rs.tdwg.org/dwc/terms/locationID"/></core><extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>occurrence.txt</location></files><coreid index="0"/><field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/><field index="2" term="http://rs.tdwg.org/dwc/terms/taxonRank"/></extension></archive>'
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        z.writestr('meta.xml',meta)
        z.writestr('event.txt','old\t1999-07-01\tx\nnew\t2021-07-01\tx\n')
        z.writestr('occurrence.txt','old\tOld species\tspecies\nnew\tNew species\tspecies\nnew\tNew species\tspecies\n')
    return b.getvalue()

def test_only_selected_period_response_retained():
    m=mod();rows,audit=m.extract(fixture());assert len(rows['events'])==1;assert len(rows['occurrences'])==2;assert audit['event_total']==2 and audit['occurrence_total_scanned']==3;assert all(r['scientificName']=='New species' for r in rows['occurrences'])

def test_dates_and_missing_stay_explicit():
    m=mod();assert m.year_of({'eventDate':'2021-12-17/2022-03-18'})==2021;assert m.year_of({'eventDate':''}) is None

def test_duplicates_of_source_event_fail():
    m=mod();b=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(fixture())) as src,zipfile.ZipFile(b,'w') as z:
        for n in src.namelist():z.writestr(n,src.read(n) if n!='event.txt' else b'x\t2021-07-01\tx\nx\t2021-08-01\tx\n')
    with pytest.raises(ValueError,match='duplicate'):m.extract(b.getvalue())
