"""Selected contemporary responses for NEW forest-environment analysis.
Source Occurrence member is scanned, but only records linked to2019-2022
Event starts are retained. No sealed historical scorer is invoked.
"""
import argparse,csv,hashlib,io,json,urllib.request,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
SOURCES={
'BALA':('https://ipt.gbif.pt/ipt/archive.do?r=bala_arthropods&v=1.0','4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2'),
'SLAM':('https://ipt.gbif.pt/ipt/archive.do?r=arthropods_slam_azores&v=1.7','b86f7fad6468d2fb9aa9473849effe41ba2c4405c786357b6f50d66d9ef552a0')}
def local(tag):return tag.rsplit('}',1)[-1]
def year_of(row):
    s=str(row.get('eventDate',''))[:4]
    return int(s) if s.isdigit() else None

def descriptor(node):
    fields={};defaults={};member=None;key=None
    for e in node.iter():
        t=local(e.tag)
        if t=='location':member=e.text.strip()
        elif t in ('id','coreid'):key=int(e.get('index'))
        elif t=='field':
            name=e.get('term','').rstrip('/').split('/')[-1].split('#')[-1]
            if 'index' in e.attrib:fields[name]=int(e.get('index'))
            elif 'default' in e.attrib:defaults[name]=e.get('default')
    if member is None or key is None:raise ValueError('Missing member or source key')
    return member,key,fields,defaults,node.get('fieldsTerminatedBy',r'\t').replace(r'\t','\t'),int(node.get('ignoreHeaderLines','0'))

def stream(z,node):
    member,key,cols,defaults,sep,skip=descriptor(node)
    with z.open(member) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as f:
        r=csv.reader(f,delimiter=sep)
        for _ in range(skip):next(r,None)
        for x in r:
            if x and any(x):yield x[key],x,cols,defaults

def extract(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read('meta.xml'))
        core=next(x for x in root if local(x.tag)=='core' and x.get('rowType','').endswith('/Event'))
        ext=next(x for x in root if local(x.tag)=='extension' and x.get('rowType','').endswith('/Occurrence'))
        events=[];allids=set()
        for key,vals,cols,defaults in stream(z,core):
            if not key or key in allids:raise ValueError('empty/duplicate source Event key')
            allids.add(key);row={**defaults,**{k:vals[i] for k,i in cols.items() if i<len(vals)},'source_core_id':key}
            yr=year_of(row)
            if yr is not None and 2019<=yr<=2022:events.append(row)
        wanted={r['source_core_id'] for r in events};occ=[];total=0;orphans=0;seen=set()
        for key,vals,cols,defaults in stream(z,ext):
            total+=1
            if key not in allids:orphans+=1
            if key not in wanted:continue
            row={**defaults,**{k:vals[i] for k,i in cols.items() if i<len(vals)},'source_core_id':key};occ.append(row);seen.add(key)
        return {'events':events,'occurrences':occ},{'event_total':len(allids),'selected_events':len(events),'occurrence_total_scanned':total,'retained_occurrence_rows':len(occ),'orphan_occurrences':orphans,'selected_events_without_any_occurrence':sorted(wanted-seen),'selected_event_ids_sha256':hashlib.sha256('\n'.join(sorted(wanted)).encode()).hexdigest(),'source_event_fields':list(descriptor(core)[2]),'source_occurrence_fields':list(descriptor(ext)[2]),'old_frozen_scorers_executed':False}

def csvout(path,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)

def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);report={}
    for name,(url,expected) in SOURCES.items():
        req=urllib.request.Request(url,headers={'User-Agent':'ForestMacro-NewExploratoryAnalysis/1.0'})
        with urllib.request.urlopen(req,timeout=90) as f:blob=f.read(10_000_000)
        digest=hashlib.sha256(blob).hexdigest()
        if digest!=expected:raise ValueError(name+' original archive changed')
        data,audit=extract(blob)
        for kind,rows in data.items():csvout(out/f'{name}_{kind}_2019_2022.csv',rows)
        report[name]={**audit,'url':url,'archive_sha256':digest}
    report['file_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}
    (out/'extraction_provenance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(p.parse_args().out)
