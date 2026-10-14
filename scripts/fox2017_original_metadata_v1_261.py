#!/usr/bin/env python3
"""Fox 2017 original Dryad metadata only; never download biological rows."""
import argparse,json,re,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse
BASE="https://datadryad.org/api/v2"
DOI="10.5061/dryad.2rs23"
ENC="doi%3A10.5061%2Fdryad.2rs23"
NAMES={"data_for_Fox_et_el_2017_nature_ee.csv",
       "README_for_data_for_Fox_et_el_2017_nature_ee.txt"}
def get_json(url):
    if not url.startswith(BASE+"/"):
        raise ValueError("Original Dryad publisher host only")
    req=urllib.request.Request(url,headers={"User-Agent":"StructuralEcology/1.261","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as r:
        return json.loads(r.read(300000).decode("utf-8"))
def walk(x):
    if isinstance(x,dict):
        yield x
        for z in x.values():yield from walk(z)
    if isinstance(x,list):
        for z in x:yield from walk(z)
def source_id(entry,prefix):
    value=entry.get("id")
    if isinstance(value,int):return value
    href=((entry.get("_links") or {}).get("self") or {}).get("href","")
    u=urlparse(href)
    if u.netloc and u.netloc!="datadryad.org":raise ValueError("Foreign source authority")
    m=re.fullmatch("/api/v2/"+prefix+r"/(\d+)",u.path)
    if not m:raise ValueError("Source ID not independently verifiable")
    return int(m.group(1))
def versions(data):
    return sorted(set((int(o["versionNumber"]),source_id(o,"versions"))
       for o in walk(data)
       if isinstance(o,dict) and "versionNumber" in o
       and o.get("curationStatus") in (None,"Published")))
def validate(dataset,version_data,file_data):
    if str(dataset.get("identifier","")).lower() not in (DOI,"doi:"+DOI):
        raise ValueError("Original Fox DOI mismatch")
    vers=versions(version_data)
    if not vers:raise ValueError("No published Fox source version")
    entries=(file_data.get("_embedded") or {}).get("stash:files",[])
    if not isinstance(entries,list) or file_data.get("total")!=len(entries):
        raise ValueError("Missing/paginated publisher file list")
    files={}
    for f in entries:
        name=f.get("path") or f.get("filename") or f.get("name")
        if name in files:raise ValueError("Duplicate file entry")
        files[name]=f
    if set(files)!=NAMES:raise ValueError("Different Fox published source file set")
    out={}
    for name,obj in sorted(files.items()):
        digest=obj.get("digest","")
        size=obj.get("size")
        if (not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest)
            or not isinstance(size,int) or size<=0):
            raise ValueError("Publisher source hash or size missing")
        out[name]={"id":source_id(obj,"files"),"bytes":size,"sha256":digest}
    return {"schema":"structural.fox2017_spatial_hydra_source_only.v1_261",
            "status":"PASS_ORIGINAL_DRYAD_EXPERIMENT_FILE_IDENTITIES_ONLY",
            "dataset_DOI":DOI,
            "2017_study_DOI":"10.1038/s41559-017-0271-y",
            "source_archived_published_data":True,
            "all_published_versions":vers,
            "latest_version_number":vers[-1][0],
            "latest_version_id":vers[-1][1],
            "source_file_metadata":out,
            "biological_rows_decoded":0,
            "recorded_number_of_metapopulations_confirmed":False,
            "individual_source_to_target_migration_confirmed":False,
            "already_published_hydra_result_NOT_new":True,
            "one_lab_experiment_not_independent_GEB_confirmation":True,
            "GEB_scientific_HOLD":True,"eBird_used":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result={"schema":"structural.fox2017_spatial_hydra_source_only.v1_261",
        "status":"STOP_ORIGINAL_DRYAD_METADATA_TRANSPORT",
        "dataset_DOI":DOI,"biological_rows_decoded":0,
        "GEB_scientific_HOLD":True,"eBird_used":False}
    try:
        data=get_json(BASE+"/datasets/"+ENC)
        v=get_json(BASE+"/datasets/"+ENC+"/versions")
        version_rows=versions(v)
        if not version_rows:raise ValueError("No published version")
        file_data=get_json(BASE+"/versions/"+str(version_rows[-1][1])+"/files?per_page=100")
        result=validate(data,v,file_data)
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
        result["network_error"]={"kind":type(e).__name__,
                                 "http_status":getattr(e,"code",None)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
