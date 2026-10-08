#!/usr/bin/env python3
"""ALA mammal taxon-name manifest only. No source FID, geographic event or response pair is decoded."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,unicodedata,zipfile
from pathlib import Path

class Stop(ValueError):pass

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def git_blob_sha1(blob):
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

def taxon_key(x):
    return " ".join(unicodedata.normalize("NFC",str(x)).replace("."," ").replace("_"," ").split()).casefold()

def dbf_taxon_set(data,field):
    """Decode ONLY one DBF field by byte offset, never other fields (including island FID)."""
    if len(data)<34 or data[0] not in (3, 131, 139, 48):
        raise Stop("invalid unsupported DBF header")
    n=int.from_bytes(data[4:8],"little")
    hlen=int.from_bytes(data[8:10],"little")
    rlen=int.from_bytes(data[10:12],"little")
    if not 1<=n<=2_000_000 or not 65<=hlen<len(data) or not 2<=rlen<=65535:
        raise Stop("invalid DBF record layout")
    if hlen+n*rlen>len(data):raise Stop("truncated DBF records")
    offs=1
    choice=None
    names=[]
    for start in range(32,hlen-1,32):
        desc=data[start:start+32]
        if not desc or desc[0]==13:break
        name=desc[:11].split(b"\0",1)[0].decode("ascii")
        width=int(desc[16])
        if width<1:raise Stop("zero-width DBF field")
        if name in names:raise Stop("duplicate DBF field name")
        names.append(name)
        if name==field:choice=(offs,width,desc[11])
        offs+=width
    if choice is None:raise Stop("frozen taxon DBF field not found")
    start,width,dtype=choice
    if dtype not in (ord("C"),ord("M")):raise Stop("taxon column is not character text")
    if start+width>rlen:raise Stop("taxon column extends beyond record boundary")
    taxa=set()
    for i in range(n):
        pos=hlen+i*rlen
        if data[pos:pos+1]==b"*":continue
        if data[pos:pos+1]!=b" ":raise Stop("unexpected DBF row status")
        # The ONLY semantically opened response-archive body bytes.
        v=data[pos+start:pos+start+width].strip(b" \0").decode("latin-1")
        key=taxon_key(v)
        if key:taxa.add(key)
    return taxa,{"rows":n,"field_name":field,"field_names":names,"unique_source_taxa":len(taxa)}

def archive_taxa(blob,contract):
    src=contract["external"]
    if len(blob)!=src["response_archive_size_bytes"]:
        raise Stop("ALA mammal ZIP byte-size drift")
    if git_blob_sha1(blob)!=src["response_archive_blob_sha1"]:
        raise Stop("ALA mammal ZIP original git SHA drift")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None:raise Stop("ALA mammal ZIP CRC drift")
        matches=[n for n in z.namelist() if Path(n).name.lower()==src["exact_dbf_basename"].lower()
                 and not n.lower().startswith("__macosx/") and not Path(n).name.startswith("._")]
        if len(matches)!=1:raise Stop(f"expected single authentic ALA mammal DBF, got {len(matches)}")
        raw=z.read(matches[0])
    taxa,receipt=dbf_taxon_set(raw,src["taxon_dbf_column"])
    receipt["source_dbf_name"]=matches[0]
    return taxa,receipt

def audit(original_species,crosswalk,geometry_receipt,mammal_zip,contract):
    if contract.get("schema")!="structural.ala_mammal_taxon_manifest_gate.v1_192":
        raise Stop("taxon manifest contract schema mismatch")
    a=contract["geometry_authority"]
    if digest(crosswalk)!=a["crosswalk_sha256"]:
        raise Stop("frozen original island crosswalk SHA drift")
    gr=json.loads(geometry_receipt.read_text())
    if (gr.get("status")!=a["required_status"]
        or gr.get("exact_one_to_one_heldout_matches")!=a["frozen_exact_matches"]
        or gr.get("crosswalk_sha256")!=a["crosswalk_sha256"]
        or gr.get("biological_scoring_authorized") is not False):
        raise Stop("original island geometry qualification drift")
    if original_species.name!=contract["original"]["species_universe_csv"]:
        raise Stop("original species universe basename drift")
    if digest(original_species)!=contract["original"]["species_universe_sha256"]:
        raise Stop("original 529 species SHA drift")
    rows=list(csv.DictReader(original_species.open("r",encoding="utf-8-sig",newline="")))
    if len(rows)!=529 or any(not r.get("species_name") for r in rows):
        raise Stop("original species universe schema/size drift")
    focals={taxon_key(r["species_name"]):r["species_name"] for r in rows}
    if len(focals)!=529:raise Stop("focal name canonical collision")
    taxa,stats=archive_taxa(mammal_zip.read_bytes(),contract)
    matched=sorted(taxa.intersection(focals))
    n=len(matched)
    eligible=n>=contract["parsing_policy"]["min_distinct_matching_focal_species"]
    return {
      "schema":"structural.ala_mammal_taxon_manifest_result.v1_192",
      "status":contract["outcomes"]["success"] if eligible else contract["outcomes"]["no_support"],
      "source_repository":contract["external"]["repository"],
      "source_commit":contract["external"]["source_commit"],
      "original_heldout_islands_geometrically_matched":gr["exact_one_to_one_heldout_matches"],
      "original_focal_species_total":len(focals),
      "source_dbf_taxon_field":stats["field_name"],
      "source_dbf_field_names":stats["field_names"],
      "source_dbf_rows_metadata_only":stats["rows"],
      "source_unique_taxa":stats["unique_source_taxa"],
      "distinct_exact_focal_taxon_overlap":n,
      "minimum_distinct_exact_overlap":contract["parsing_policy"]["min_distinct_matching_focal_species"],
      "matching_focal_species":[focals[k] for k in matched],
      "original_island_crosswalk_sha256":a["crosswalk_sha256"],
      "external_zip_sha256":digest(mammal_zip),
      "external_zip_transport_performed":True,
      "ALA_island_x_species_pairs_semantically_decoded":0,
      "ALA_FID_values_from_response_archive_read":0,
      "original_heldout_response_values_read":0,
      "ecological_score_calculated":False,
      "biological_scoring_authorized":False,
      "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("original_species",type=Path)
    p.add_argument("island_crosswalk",type=Path)
    p.add_argument("island_geometry_receipt",type=Path)
    p.add_argument("ala_mammal_zip",type=Path)
    p.add_argument("--contract",type=Path,default=Path("development/global_mammals_ala_taxon_manifest_gate_v1_192.json"))
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        r=audit(a.original_species,a.island_crosswalk,a.island_geometry_receipt,a.ala_mammal_zip,c)
        code=0 if r["status"]==c["outcomes"]["success"] else 2
    except (Stop,KeyError,ValueError,OSError,json.JSONDecodeError,zipfile.BadZipFile) as exc:
        r={"schema":"structural.ala_mammal_taxon_manifest_result.v1_192",
           "status":"STOP_ALA_FOCAL_TAXON_SCHEMA_OR_TRANSPORT","reason":str(exc),
           "ALA_island_x_species_pairs_semantically_decoded":0,
           "ALA_FID_values_from_response_archive_read":0,
           "original_heldout_response_values_read":0,
           "ecological_score_calculated":False,"biological_scoring_authorized":False,"eBird_used":False}
        code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
