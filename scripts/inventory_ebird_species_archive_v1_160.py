#!/usr/bin/env python3
"""Content-blind inventory of the Dryad eBird species archive.

The code inspects only the ZIP central directory. It never opens or decompresses
an archive member and never deserializes an RData object.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/ebird_species_archive_firewall_contract_v1_160.json"

class Stop(RuntimeError):
    pass

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def load_json(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))

def require_parent(prebiology:dict, contract:dict):
    req=contract["prerequisites"]
    if prebiology.get("status") != req["required_prebiology_status"]:
        raise Stop("v1.159 prebiology handoff did not pass")
    if prebiology.get("species_response_opened") is not req["required_species_response_opened"]:
        raise Stop("species response boundary already violated")
    if prebiology.get("source_loss_events_constructed") is not req["required_source_loss_events_constructed"]:
        raise Stop("source-loss boundary already violated")
    nconf=len(prebiology.get("confirmatory_window_ids",[]))
    if nconf < int(req["minimum_confirmatory_windows"]):
        raise Stop("fewer than the frozen minimum confirmatory windows")

def inventory(zip_path:Path, contract:dict):
    try:
        zf=zipfile.ZipFile(zip_path,"r")
    except zipfile.BadZipFile as e:
        raise Stop("species archive is not a readable ZIP") from e

    rows=[]
    seen=set()
    rdata=0
    extensions=set(contract["inventory_rules"]["RData_extension_casefold"])
    try:
        for info in zf.infolist():
            name=info.filename
            if name in seen:
                raise Stop("duplicate ZIP member path")
            seen.add(name)
            p=Path(name)
            is_dir=info.is_dir()
            ext=p.suffix.casefold()
            if not is_dir and ext in extensions:
                rdata+=1
            rows.append({
                "member_path":name,
                "basename":p.name,
                "extension":ext,
                "compressed_size_bytes":info.compress_size,
                "uncompressed_size_bytes":info.file_size,
                "CRC32":f"{info.CRC:08x}",
                "compression_method":info.compress_type,
                "local_header_offset":info.header_offset,
                "directory_flag":1 if is_dir else 0,
            })
    finally:
        zf.close()

    expected=int(contract["inventory_rules"]["require_exact_RData_member_count"])
    if rdata!=expected:
        raise Stop(f"RData member-count drift: {rdata} != {expected}")
    return rows,rdata

def write_manifest(rows:list[dict], path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=[
        "member_path","basename","extension","compressed_size_bytes",
        "uncompressed_size_bytes","CRC32","compression_method",
        "local_header_offset","directory_flag"
    ]
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n")
        w.writeheader()
        for r in sorted(rows,key=lambda x:x["member_path"]):
            w.writerow(r)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("archive",type=Path)
    ap.add_argument("--prebiology-receipt",type=Path,required=True)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    try:
        c=load_json(a.contract)
        if c.get("schema")!="structural.ebird_species_archive_firewall_contract.v1_160":
            raise Stop("contract schema drift")
        pre=load_json(a.prebiology_receipt)
        require_parent(pre,c)
        rows,rdata=inventory(a.archive,c)
        write_manifest(rows,a.manifest)
        result={
            "schema":"structural.ebird_species_archive_inventory_result.v1_160",
            "status":"CONTENT_BLIND_SPECIES_ARCHIVE_INVENTORY_FROZEN",
            "candidate_id":c["candidate_id"],
            "archive_name":a.archive.name,
            "archive_sha256":sha256(a.archive),
            "zip_member_count":len(rows),
            "RData_member_count":rdata,
            "member_manifest_sha256":sha256(a.manifest),
            "prebiology_sed_sha256":pre.get("sed_sha256"),
            "prebiology_island_geometry_sha256":pre.get("island_geometry_sha256"),
            "pilot_window_ids":pre.get("pilot_window_ids",[]),
            "confirmatory_window_ids":pre.get("confirmatory_window_ids",[]),
            "RData_members_opened":0,
            "RData_members_decompressed":0,
            "RData_objects_deserialized":0,
            "species_identity_opened":False,
            "species_detection_opened":False,
            "species_nondetection_constructed":False,
            "annual_species_occupancy_constructed":False,
            "source_loss_events_constructed":False,
            "t2_outcome_opened":False,
            "counts_as_empirical_source_loss_evidence":False,
            "next_action":c["next_gate_if_passed"],
        }
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
            "schema":"structural.ebird_species_archive_inventory_result.v1_160",
            "status":"STOP",
            "reason":str(e),
            "RData_members_opened":0,
            "RData_members_decompressed":0,
            "RData_objects_deserialized":0,
            "species_identity_opened":False,
            "species_detection_opened":False,
            "species_nondetection_constructed":False,
            "annual_species_occupancy_constructed":False,
            "source_loss_events_constructed":False,
            "t2_outcome_opened":False,
            "counts_as_empirical_source_loss_evidence":False,
        }
        code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
