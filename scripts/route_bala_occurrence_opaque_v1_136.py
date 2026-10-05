#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,unicodedata,zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_opaque_taxon_routing_contract_v1_136.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def normalize_token(raw:bytes)->str:
    try:s=raw.decode("utf-8")
    except UnicodeDecodeError as e:raise Stop("MF routing token UTF-8 decode failed") from e
    s=unicodedata.normalize("NFC",s).strip()
    if not s:raise Stop("blank MF routing token")
    return s

def bucket(token,salt):
    h=hashlib.sha256((salt+token).encode("utf-8")).hexdigest()
    return int(h[:8],16)%4,h

def set_fingerprint(digests):
    h=hashlib.sha256()
    for x in sorted(digests):h.update(x.encode("ascii"));h.update(b"\n")
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("archive",type=Path)
    ap.add_argument("partition_spec",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--pilot-surface",type=Path,required=True)
    ap.add_argument("--confirmatory-surface",type=Path,required=True)
    ap.add_argument("--pilot-token-manifest",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text());spec=json.loads(a.partition_spec.read_text())
        if c["schema"]!="structural.bala_opaque_taxon_routing_contract.v1_136":raise Stop("contract schema drift")
        if sha(a.archive)!=c["source"]["archive_sha256"]:raise Stop("archive SHA drift")
        if sha(a.partition_spec)!=c["partition"]["partition_spec_sha256"]:raise Stop("partition spec SHA drift")
        if spec["routing_field_index"]!=c["partition"]["routing_field_index"]:raise Stop("routing index drift")
        with zipfile.ZipFile(a.archive) as z:
            try:occ=z.read(c["source"]["occurrence_location"])
            except KeyError as e:raise Stop("Occurrence member missing") from e
        if hashlib.sha256(occ).hexdigest()!=c["source"]["occurrence_sha256"]:raise Stop("Occurrence SHA drift")
        lines=occ.splitlines(keepends=True)
        if len(lines)<2:raise Stop("Occurrence surface empty")
        header=lines[0];data=lines[1:]
        if len(data)!=c["source"]["expected_occurrence_data_rows"]:raise Stop("Occurrence row-count drift")
        idx=int(c["partition"]["routing_field_index"]);nfields=int(c["source"]["expected_field_count"]);salt=c["partition"]["salt"]
        pilot=bytearray(header);confirm=bytearray(header)
        pc=Counter();ptoken_digest={};ctoken_digests=set();pilot_rows=confirm_rows=0
        for rn,line in enumerate(data,1):
            body=line[:-2] if line.endswith(b"\r\n") else line[:-1] if line.endswith((b"\n",b"\r")) else line
            fields=body.split(b"\t")
            if len(fields)!=nfields:raise Stop(f"Occurrence field-count drift at row {rn}")
            token=normalize_token(fields[idx]);b,digest=bucket(token,salt)
            if b==0:
                pilot.extend(line);pilot_rows+=1;pc[token]+=1;ptoken_digest[token]=digest
            elif b in {1,2,3}:
                confirm.extend(line);confirm_rows+=1;ctoken_digests.add(digest)
            else:raise Stop("partition bucket outside 0..3")
        if pilot_rows+confirm_rows!=len(data):raise Stop("routing row conservation failed")
        a.pilot_surface.parent.mkdir(parents=True,exist_ok=True)
        a.pilot_surface.write_bytes(bytes(pilot));a.confirmatory_surface.write_bytes(bytes(confirm))
        with a.pilot_token_manifest.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["MF_token","bucket","occurrence_rows","salted_token_sha256"])
            for token in sorted(pc):w.writerow([token,0,pc[token],ptoken_digest[token]])
        result={
          "schema":"structural.bala_opaque_taxon_routing_result.v1_136",
          "status":"BALA_MF_ONLY_OPAQUE_TAXON_ROUTING_COMPLETE",
          "occurrence_data_rows_routed":len(data),
          "routing_tokens_decoded":len(data),
          "pilot_rows":pilot_rows,"confirmatory_rows":confirm_rows,
          "pilot_distinct_taxa":len(pc),"confirmatory_distinct_taxa":len(ctoken_digests),
          "pilot_token_manifest_sha256":sha(a.pilot_token_manifest),
          "pilot_surface_sha256":sha(a.pilot_surface),
          "confirmatory_surface_sha256":sha(a.confirmatory_surface),
          "confirmatory_token_set_fingerprint":set_fingerprint(ctoken_digests),
          "pilot_nonrouting_fields_semantically_opened":0,
          "confirmatory_nonrouting_fields_semantically_opened":0,
          "organismQuantity_values_decoded":0,"eventID_values_decoded":0,"taxonomy_values_decoded":0,
          "event_by_taxon_combinations_summarized":0,"source_loss_effects_computed":0,
          "confirmatory_token_identities_persisted":False,
          "confirmatory_occurrence_semantic_access_authorized":False,
          "pilot_occurrence_semantic_access_authorized":False,
          "confirmatory_eligible":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,zipfile.BadZipFile,Stop) as e:
        result={"schema":"structural.bala_opaque_taxon_routing_result.v1_136","status":"STOP","reason":str(e),
          "organismQuantity_values_decoded":0,"eventID_values_decoded":0,"taxonomy_values_decoded":0,
          "source_loss_effects_computed":0,"confirmatory_eligible":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
