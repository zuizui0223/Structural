#!/usr/bin/env python3
"""Response-unopened BALA DwC-A archive and Event-core audit.

Occurrence-extension bytes may be hashed as opaque bytes, but are never decoded
or parsed. Only meta.xml, EML and the Event core are semantically opened.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,urllib.request,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_event_core_audit_contract_v1_128.json"
class Stop(RuntimeError): pass

def sha_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def local_name(tag:str)->str:
    return tag.rsplit("}",1)[-1]

def parse_xml_bytes(b:bytes):
    try:return ET.fromstring(b)
    except ET.ParseError as e:raise Stop(f"XML parse failed: {e}") from e

def read_member(z:zipfile.ZipFile,name:str)->bytes:
    try:return z.read(name)
    except KeyError as e:raise Stop(f"missing archive member: {name}") from e

def find_child_text(node,name):
    for child in node.iter():
        if local_name(child.tag)==name and child.text:
            return child.text.strip()
    return None

def parse_meta(meta_bytes:bytes):
    root=parse_xml_bytes(meta_bytes)
    core=None;extensions=[]
    for ch in list(root):
        ln=local_name(ch.tag)
        if ln=="core":core=ch
        elif ln=="extension":extensions.append(ch)
    if core is None:raise Stop("meta.xml has no core")
    def parse_table(node):
        loc=None
        for x in node.iter():
            if local_name(x.tag)=="location" and x.text:
                loc=x.text.strip();break
        if not loc:raise Stop("table location missing in meta.xml")
        fields=[]
        id_index=None;coreid_index=None
        for x in list(node):
            ln=local_name(x.tag)
            if ln=="id":id_index=int(x.attrib["index"])
            elif ln=="coreid":coreid_index=int(x.attrib["index"])
            elif ln=="field":
                idx=int(x.attrib["index"])
                term=x.attrib.get("term","")
                default=x.attrib.get("default")
                fields.append({"index":idx,"term":term,"name":term.rsplit("/",1)[-1] if term else f"field_{idx}","default":default})
        return {
          "location":loc,
          "rowType":node.attrib.get("rowType",""),
          "encoding":node.attrib.get("encoding","UTF-8"),
          "fieldsTerminatedBy":node.attrib.get("fieldsTerminatedBy","\\t"),
          "linesTerminatedBy":node.attrib.get("linesTerminatedBy","\\n"),
          "fieldsEnclosedBy":node.attrib.get("fieldsEnclosedBy",""),
          "ignoreHeaderLines":int(node.attrib.get("ignoreHeaderLines","0")),
          "id_index":id_index,
          "coreid_index":coreid_index,
          "fields":sorted(fields,key=lambda x:x["index"])
        }
    return parse_table(core),[parse_table(x) for x in extensions]

ESC={"\\t":"\t","\\n":"\n","\\r":"\r","\\r\\n":"\r\n","":""}
def unesc(s):
    return ESC.get(s,s)

def parse_event_core(data:bytes,meta:dict):
    enc=meta["encoding"] or "UTF-8"
    try:text=data.decode(enc)
    except UnicodeDecodeError as e:raise Stop("Event core UTF decode failed") from e
    delim=unesc(meta["fieldsTerminatedBy"])
    quote=unesc(meta["fieldsEnclosedBy"])
    if len(delim)!=1:raise Stop(f"unsupported Event delimiter {delim!r}")
    reader=csv.reader(io.StringIO(text),delimiter=delim,quotechar=quote if quote else None,quoting=csv.QUOTE_MINIMAL if quote else csv.QUOTE_NONE)
    rows=list(reader)
    skip=meta["ignoreHeaderLines"]
    rows=rows[skip:]
    index_to_name={}
    for f in meta["fields"]:index_to_name[f["index"]]=f["name"]
    if meta["id_index"] is not None:index_to_name.setdefault(meta["id_index"],"__core_id__")
    maxidx=max(index_to_name) if index_to_name else -1
    out=[]
    for i,row in enumerate(rows,1):
        if len(row)<=maxidx:raise Stop(f"Event row {i} field-count short")
        rec={name:row[idx].strip() for idx,name in index_to_name.items()}
        out.append(rec)
    return out,index_to_name

def year_from(rec):
    for key in ("eventDate","verbatimEventDate"):
        s=rec.get(key,"")
        m=re.search(r"(?<!\d)(19\d{2}|20\d{2}|2100)(?!\d)",s)
        if m:return int(m.group(1))
    return None

PHASE_PAT=re.compile(r"\bBALA\s*([123])\b",re.I)
def explicit_phase(rec):
    vals=[]
    for k,v in rec.items():
        if not v:continue
        if k in {"samplingProtocol","eventRemarks","fieldNotes","locationRemarks","locality","datasetName","eventID","parentEventID","locationID"}:
            vals.extend(PHASE_PAT.findall(v))
    labs={f"BALA{x}" for x in vals}
    return next(iter(labs)) if len(labs)==1 else None

def derive_year_clusters(years):
    ys=sorted(set(y for y in years if y is not None))
    if len(ys)<3:raise Stop("fewer than three distinct Event years")
    gaps=[(ys[i+1]-ys[i],i,ys[i],ys[i+1]) for i in range(len(ys)-1)]
    ordered=sorted(gaps,reverse=True)
    if len(ordered)<2 or ordered[1][0]<3:raise Stop("Event years lack two >=3-year phase gaps")
    if len(ordered)>2 and ordered[1][0]==ordered[2][0]:
        raise Stop("second-largest year gap not unique; temporal clustering ambiguous")
    cuts=sorted([ordered[0][1],ordered[1][1]])
    groups=[ys[:cuts[0]+1],ys[cuts[0]+1:cuts[1]+1],ys[cuts[1]+1:]]
    if any(not g for g in groups):raise Stop("empty temporal phase cluster")
    mapping={}
    for label,grp in zip(("BALA1","BALA2","BALA3"),groups):
        for y in grp:mapping[y]=label
    return mapping,groups,sorted([(g[0],g[-1]) for g in groups])

def norm(s):
    return re.sub(r"\s+"," ",str(s or "").strip())

def coord_key(rec,decimals):
    lat=norm(rec.get("decimalLatitude",""));lon=norm(rec.get("decimalLongitude",""));island=norm(rec.get("island",""))
    try:
        a=round(float(lat),decimals);b=round(float(lon),decimals)
    except Exception:return ""
    if not island:return ""
    return f"{island}|{a:.{decimals}f}|{b:.{decimals}f}"

def candidate_key(rec,key,decimals):
    if key=="locationID":return norm(rec.get("locationID",""))
    if key=="parentEventID":return norm(rec.get("parentEventID",""))
    if key=="island_plus_locality":
        a=norm(rec.get("island",""));b=norm(rec.get("locality",""))
        return f"{a}|{b}" if a and b else ""
    if key=="rounded_latitude_longitude_plus_island":return coord_key(rec,decimals)
    raise Stop(f"unknown candidate key {key}")

def audit_site_key(rows,key,decimals):
    phase_sets=defaultdict(set);allkeys=[];key_coords=defaultdict(set);key_islands=defaultdict(set)
    nonblank=0
    for r in rows:
        k=candidate_key(r,key,decimals)
        if not k:continue
        nonblank+=1;allkeys.append(k)
        ph=r["_phase"]
        if ph:phase_sets[ph].add(k)
        lat=norm(r.get("decimalLatitude",""));lon=norm(r.get("decimalLongitude",""))
        if lat and lon:key_coords[k].add((lat,lon))
        isl=norm(r.get("island",""))
        if isl:key_islands[k].add(isl)
    inter=set.intersection(*(phase_sets.get(p,set()) for p in ("BALA1","BALA2","BALA3"))) if all(phase_sets.get(p) for p in ("BALA1","BALA2","BALA3")) else set()
    islands=set()
    for k in inter:islands.update(key_islands.get(k,set()))
    return {
      "candidate_key":key,
      "nonblank_fraction":nonblank/len(rows) if rows else 0.0,
      "unique_keys_total":len(set(allkeys)),
      "unique_BALA1":len(phase_sets.get("BALA1",set())),
      "unique_BALA2":len(phase_sets.get("BALA2",set())),
      "unique_BALA3":len(phase_sets.get("BALA3",set())),
      "three_phase_intersection_count":len(inter),
      "islands_in_three_phase_intersection":len(islands),
      "three_phase_island_names":";".join(sorted(islands)),
      "coordinate_inconsistency_count":sum(len(v)>1 for v in key_coords.values())
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.bala_event_core_audit_contract.v1_128":raise Stop("contract schema drift")
    url=c["source"]["dwca_url"]
    req=urllib.request.Request(url,headers={"User-Agent":"Structural-BALA-event-audit/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:raw=resp.read()
    except Exception as e:raise Stop(f"DwC-A download failed: {e}") from e
    if not raw.startswith(b"PK"):raise Stop("download is not ZIP")
    archive_sha=sha_bytes(raw)
    z=zipfile.ZipFile(io.BytesIO(raw))
    infos=z.infolist()
    if not infos:raise Stop("empty archive")

    inventory=[]
    for info in infos:
        b=read_member(z,info.filename)
        inventory.append({
          "path":info.filename,"compressed_bytes":info.compress_size,"uncompressed_bytes":info.file_size,
          "crc32":f"{info.CRC:08x}","sha256":sha_bytes(b)
        })

    meta_names=[x.filename for x in infos if Path(x.filename).name.lower()=="meta.xml"]
    if len(meta_names)!=1:raise Stop(f"expected one meta.xml, found {len(meta_names)}")
    meta_bytes=read_member(z,meta_names[0])
    core,exts=parse_meta(meta_bytes)
    if not core["rowType"].endswith(c["source"]["expected_core_row_type_suffix"]):
        raise Stop(f"core rowType is not Event: {core['rowType']}")
    occ_ext=[e for e in exts if e["rowType"].endswith("/Occurrence")]
    if len(occ_ext)!=1:raise Stop(f"expected one Occurrence extension, found {len(occ_ext)}")
    occurrence_location=occ_ext[0]["location"]

    eml_candidates=[x.filename for x in infos if x.filename.lower().endswith(".xml") and Path(x.filename).name.lower()!="meta.xml"]
    # Prefer archive metadata attribute if it resolves.
    meta_root=parse_xml_bytes(meta_bytes)
    metadata_attr=meta_root.attrib.get("metadata")
    if metadata_attr and metadata_attr in {x.filename for x in infos}:eml_name=metadata_attr
    elif len(eml_candidates)==1:eml_name=eml_candidates[0]
    else:
        preferred=[x for x in eml_candidates if "eml" in Path(x).name.lower()]
        if len(preferred)!=1:raise Stop("cannot resolve unique EML metadata file")
        eml_name=preferred[0]
    eml_bytes=read_member(z,eml_name)
    eml_root=parse_xml_bytes(eml_bytes)

    event_bytes=read_member(z,core["location"])
    rows,index_to_name=parse_event_core(event_bytes,core)
    if len(rows)!=c["source"]["expected_event_records_reported"]:
        raise Stop(f"Event record count drift: {len(rows)}")

    # Ensure occurrence bytes were never decoded: only inventory hashing above touched them as opaque bytes.
    occ_info=next((x for x in inventory if x["path"]==occurrence_location),None)
    if occ_info is None:raise Stop("Occurrence extension location absent from archive inventory")

    years=[year_from(r) for r in rows]
    explicit=[explicit_phase(r) for r in rows]
    explicit_count=sum(x is not None for x in explicit)
    year_map,groups,year_ranges=derive_year_clusters(years)
    for r,ep,y in zip(rows,explicit,years):
        phase=ep if ep is not None else year_map.get(y)
        r["_phase"]=phase
    unresolved=sum(r["_phase"] not in {"BALA1","BALA2","BALA3"} for r in rows)
    conflicts=sum(1 for ep,y in zip(explicit,years) if ep and y in year_map and ep!=year_map[y])

    fields=sorted({k for r in rows for k in r.keys() if k!="_phase"})
    field_manifest=[{"field":k,"nonblank_rows":sum(bool(norm(r.get(k,""))) for r in rows),"unique_nonblank":len({norm(r.get(k,"")) for r in rows if norm(r.get(k,""))})} for k in fields]

    site_rows=[]
    dec=c["site_key_audit"]["coordinate_rounding_decimals"]
    for key in c["site_key_audit"]["candidate_keys_in_priority_order"]:
        site_rows.append(audit_site_key(rows,key,dec))

    phase_counts=Counter(r["_phase"] for r in rows)
    islands_by_phase={}
    for ph in ("BALA1","BALA2","BALA3"):
        islands_by_phase[ph]=sorted({norm(r.get("island","")) for r in rows if r["_phase"]==ph and norm(r.get("island",""))})

    result={
      "schema":"structural.bala_event_core_audit_result.v1_128",
      "status":"BALA_EVENT_CORE_RESPONSE_UNOPENED_AUDIT_COMPLETE",
      "archive_bytes":len(raw),"archive_sha256":archive_sha,"archive_member_count":len(inventory),
      "meta_xml_path":meta_names[0],"meta_xml_sha256":sha_bytes(meta_bytes),
      "eml_path":eml_name,"eml_sha256":sha_bytes(eml_bytes),
      "event_core_path":core["location"],"event_core_sha256":sha_bytes(event_bytes),
      "event_records":len(rows),
      "occurrence_extension_path":occurrence_location,
      "occurrence_extension_uncompressed_bytes":occ_info["uncompressed_bytes"],
      "occurrence_extension_sha256_opaque_bytes":occ_info["sha256"],
      "occurrence_extension_semantically_opened":False,
      "event_by_taxon_rows_parsed":0,"taxon_occurrence_values_opened":0,
      "event_year_min":min(y for y in years if y is not None),
      "event_year_max":max(y for y in years if y is not None),
      "explicit_phase_labelled_event_rows":explicit_count,
      "date_cluster_year_ranges":[{"phase":p,"year_min":min(g),"year_max":max(g),"years":g} for p,g in zip(("BALA1","BALA2","BALA3"),groups)],
      "phase_assignment_unresolved_rows":unresolved,
      "explicit_vs_date_cluster_conflict_rows":conflicts,
      "event_rows_by_phase":dict(phase_counts),
      "islands_by_phase":islands_by_phase,
      "eml_title":find_child_text(eml_root,"title"),
      "eml_pub_date":find_child_text(eml_root,"pubDate"),
      "next_gate":"inspect site_key_candidates and freeze one deterministic three-phase core panel; occurrence extension remains sealed",
      "confirmatory_eligible":False
    }

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    with (out/"archive_inventory.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["path","compressed_bytes","uncompressed_bytes","crc32","sha256"],lineterminator="\n");w.writeheader();w.writerows(inventory)
    meta_manifest={"core":core,"extensions":exts,"metadata_file":eml_name,"occurrence_extension_location":occurrence_location}
    (out/"meta_manifest.json").write_text(json.dumps(meta_manifest,indent=2,sort_keys=True)+"\n")
    with (out/"event_field_manifest.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["field","nonblank_rows","unique_nonblank"],lineterminator="\n");w.writeheader();w.writerows(field_manifest)
    with (out/"site_key_candidates.csv").open("w",encoding="utf-8",newline="") as h:
        fields2=list(site_rows[0].keys());w=csv.DictWriter(h,fieldnames=fields2,lineterminator="\n");w.writeheader();w.writerows(site_rows)
    (out/"event_core_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
