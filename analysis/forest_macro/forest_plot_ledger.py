"""Forest macroecology: published Event metadata only, no Occurrence reads.
Source IDs and uncertainty are retained. Co-location is flagged, never merged.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,statistics,unicodedata,urllib.request,zipfile
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import xml.etree.ElementTree as ET
SOURCES={
 'BALA':('https://ipt.gbif.pt/ipt/archive.do?r=bala_arthropods&v=1.0','4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2'),
 'SLAM':('https://ipt.gbif.pt/ipt/archive.do?r=arthropods_slam_azores&v=1.7','b86f7fad6468d2fb9aa9473849effe41ba2c4405c786357b6f50d66d9ef552a0')}
ALLOW=set('eventID parentEventID eventDate year month day fieldNumber samplingProtocol samplingEffort sampleSizeValue sampleSizeUnit locationID locality island islandGroup habitat decimalLatitude decimalLongitude coordinateUncertaintyInMeters coordinatePrecision geodeticDatum minimumElevationInMeters maximumElevationInMeters verbatimElevation eventRemarks locationRemarks dynamicProperties footprintWKT georeferenceRemarks associatedTaxa'.split())
ALIASES={'faial':'FAI','fai':'FAI','flores':'FLO','flo':'FLO','pico':'PIC','pic':'PIC','sao jorge':'SJG','sjg':'SJG','sao miguel':'SMG','smg':'SMG','santa maria':'SMR','smr':'SMR','terceira':'TER','ter':'TER','graciosa':'GRA','gra':'GRA','corvo':'COR','cor':'COR'}
def text(v):return ' '.join(str(v or '').split())
def island(v):
 s=''.join(c for c in unicodedata.normalize('NFKD',text(v)) if not unicodedata.combining(c)).casefold()
 return ALIASES.get(s,s.upper())
def number(v):
 try:
  x=float(str(v).strip());return x if math.isfinite(x) else None
 except (ValueError,TypeError):return None
def hav(a,b):
 p1,p2=map(math.radians,(a[0],b[0]));dp=p2-p1;dl=math.radians(b[1]-a[1])
 return 6371008.8*2*math.asin(min(1,math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2)))
def read_events(blob):
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  root=ET.fromstring(z.read('meta.xml'));cores=[x for x in root if x.tag.rsplit('}',1)[-1]=='core']
  if len(cores)!=1 or not cores[0].get('rowType','').endswith('/Event'):raise ValueError('Not an Event core')
  c=cores[0];fields={};defaults={};member=None;idx=None
  for e in c.iter():
   tag=e.tag.rsplit('}',1)[-1]
   if tag=='location':member=e.text.strip()
   if tag=='id':idx=int(e.get('index'))
   if tag=='field':
    name=e.get('term','').rstrip('/').split('/')[-1].split('#')[-1]
    if 'index' in e.attrib:fields[name]=int(e.get('index'))
    elif 'default' in e.attrib:defaults[name]=e.get('default')
  if not member or idx is None:raise ValueError('No source Event primary key')
  sep=c.get('fieldsTerminatedBy',r'\t').replace(r'\t','\t');skip=int(c.get('ignoreHeaderLines','0'));out=[]
  with z.open(member) as stream:
   rows=csv.reader(io.TextIOWrapper(stream,encoding='utf-8-sig',newline=''),delimiter=sep)
   for _ in range(skip):next(rows,None)
   for r in rows:
    if not r or not any(r):continue
    d={k:r[i] for k,i in fields.items() if k in ALLOW and i<len(r)}
    d.update({k:v for k,v in defaults.items() if k in ALLOW});d['source_core_id']=r[idx];out.append(d)
  return out,{'members_read':['meta.xml',member],'available_event_fields':fields,'constant_event_fields':defaults,'occurrence_rows_read':0}
def values(rows,key):return '|'.join(sorted({text(r.get(key)) for r in rows if text(r.get(key))}))
def summarize(dataset,events):
 groups=defaultdict(list);windows=defaultdict(list)
 for r in events:
  loc=text(r.get('locationID'));isl=island(r.get('island'));sid=f'{dataset}|{isl}|{loc}' if loc else f'{dataset}|MISSING_LOCATION|{r.get("source_core_id",r.get("eventID"))}'
  groups[sid].append(r);year=text(r.get('year')) or text(r.get('eventDate'))[:4];method=text(r.get('samplingProtocol'))
  windows[(sid,year,method)].append(r)
 plots=[]
 for sid,rows in sorted(groups.items()):
  coords=[]
  for r in rows:
   lat=number(r.get('decimalLatitude'));lon=number(r.get('decimalLongitude'))
   if lat is not None and lon is not None and -90<=lat<=90 and -180<=lon<=180:coords.append((lat,lon))
  unique=sorted(set(coords));center=(statistics.median(x[0] for x in unique),statistics.median(x[1] for x in unique)) if unique else (None,None)
  spread=max((hav(a,b) for a,b in combinations(unique,2)),default=0) if unique else None
  years=sorted({text(r.get('year')) or text(r.get('eventDate'))[:4] for r in rows}-{''})
  r0=rows[0]
  rec={'plot_key':sid,'dataset':dataset,'island':island(r0.get('island')),'source_location_id':text(r0.get('locationID')),'source_locality_values':values(rows,'locality'),'habitat_values':values(rows,'habitat'),'latitude':center[0],'longitude':center[1],'coordinate_valid_event_n':len(coords),'coordinate_unique_n':len(unique),'coordinate_spread_m':spread,'coordinate_uncertainty_source_values':values(rows,'coordinateUncertaintyInMeters'),'geodetic_datum_values':values(rows,'geodeticDatum'),'year_min':years[0] if years else '', 'year_max':years[-1] if years else '', 'years':'|'.join(years),'year_n':len(years),'event_n':len(rows),'sampling_protocols':values(rows,'samplingProtocol'),'minimum_elevation_source_values':values(rows,'minimumElevationInMeters'),'maximum_elevation_source_values':values(rows,'maximumElevationInMeters'),'coordinate_status':'missing' if not coords else ('variable_check' if spread>50 else 'available'),'native_forest_inferred':False}
  plots.append(rec)
 periods=[]
 for (sid,year,method),rows in sorted(windows.items()):
  periods.append({'plot_key':sid,'dataset':dataset,'island':island(rows[0].get('island')),'year':year,'sampling_protocol':method,'event_n':len(rows),'date_values':values(rows,'eventDate'),'sample_size_values':values(rows,'sampleSizeValue'),'sample_size_units':values(rows,'sampleSizeUnit'),'sampling_effort_values':values(rows,'samplingEffort'),'habitat_values':values(rows,'habitat')})
 return plots,periods
def cross_pairs(plots,radius=500):
 out=[]
 for a,b in combinations(plots,2):
  if a['dataset']==b['dataset'] or a['island']!=b['island'] or a['latitude'] is None or b['latitude'] is None:continue
  d=hav((a['latitude'],a['longitude']),(b['latitude'],b['longitude']))
  if d<=radius:out.append({'plot_a':a['plot_key'],'plot_b':b['plot_key'],'island':a['island'],'distance_m':d,'same_physical_site_confirmed':False,'spatial_relation':'within_50m' if d<=50 else ('within_150m' if d<=150 else 'within_500m'),'shared_years':'|'.join(sorted(set(a['years'].split('|'))&set(b['years'].split('|'))))})
 return sorted(out,key=lambda r:r['distance_m'])
def write_csv(path,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);plots=[];periods=[];report={'sources':{},'occurrence_rows_read':0,'goal':'forest plot-environment linkage, not outcome rescoring'}
 for name,(url,expected) in SOURCES.items():
  req=urllib.request.Request(url,headers={'User-Agent':'ForestMacroecology-Metadata/1.0'})
  with urllib.request.urlopen(req,timeout=90) as response:blob=response.read(10000000)
  digest=hashlib.sha256(blob).hexdigest()
  if digest!=expected:raise ValueError(f'{name} source version hash changed: {digest}')
  rows,meta=read_events(blob);p,w=summarize(name,rows);plots+=p;periods+=w
  write_csv(out/f'{name}_event_metadata.csv',rows)
  profile={k:{'nonempty_n':sum(bool(text(r.get(k))) for r in rows),'distinct_n':len({text(r.get(k)) for r in rows if text(r.get(k))}),'examples':sorted({text(r.get(k)) for r in rows if text(r.get(k))})[:12]} for k in sorted(ALLOW)}
  report['sources'][name]={'url':url,'sha256':digest,'event_rows':len(rows),'plots':len(p),'island_plot_counts':dict(Counter(r['island'] for r in p)),'plot_year_method_rows':len(w),'metadata':meta,'field_profile':profile}
 write_csv(out/'forest_plot_ledger.csv',plots);write_csv(out/'plot_year_method_ledger.csv',periods);pairs=cross_pairs(plots);write_csv(out/'cross_source_nearby_candidates.csv',pairs)
 report['cross_source_candidates_n']=len(pairs);report['cross_source_candidates_within_50m_n']=sum(p['distance_m']<=50 for p in pairs)
 report['combined_plot_records']=len(plots);report['plots_missing_coordinates']=sum(p['latitude'] is None for p in plots);report['plots_coordinate_spread_over_50m']=sum((p['coordinate_spread_m'] or 0)>50 for p in plots)
 report['output_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}
 (out/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('sources','output_sha256')}));print(json.dumps({k:{x:v[x] for x in ('event_rows','plots','island_plot_counts','plot_year_method_rows')} for k,v in report['sources'].items()}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);run(ap.parse_args().out)
