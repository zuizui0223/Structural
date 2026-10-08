#!/usr/bin/env python3
"""Audit only source island names and species headers from Hébert et al. Dryad CSVs.

Never interpret or decode the species x island 0/1 body. Individual lines are
held as opaque bytes; only the first CSV field of each body row is decoded.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json"

class GateStop(RuntimeError):pass

def canonical(x):
    return " ".join(unicodedata.normalize("NFC",x).split()).casefold()

def island_key(x):
    return " ".join(unicodedata.normalize("NFC",x).split())

def first_field_only(raw):
    """Decode exactly the leading RFC4180 field, without interpreting suffix."""
    raw=raw.rstrip(b"\r\n")
    if not raw:raise GateStop("empty body line")
    if raw.startswith(b'"'):
        i=1;out=bytearray()
        while i<len(raw):
            ch=raw[i]
            if ch==34:
                if i+1<len(raw) and raw[i+1]==34:
                    out.append(34);i+=2;continue
                i+=1
                if i>=len(raw) or raw[i]!=44:raise GateStop("invalid closing first-field quote")
                return out.decode("utf-8-sig")
            out.append(ch);i+=1
        raise GateStop("unterminated first-field quote")
    i=raw.find(b",")
    if i<1:raise GateStop("no CSV delimiter after island key")
    return raw[:i].decode("utf-8-sig")

def schema_only(raw,name):
    lines=raw.splitlines(keepends=True)
    if len(lines)<2:raise GateStop(f"empty CSV: {name}")
    header=list(csv.reader(io.StringIO(lines[0].decode("utf-8-sig"))))
    if len(header)!=1 or len(header[0])<2:raise GateStop(f"invalid header: {name}")
    names=[island_key(first_field_only(row)) for row in lines[1:] if row.strip()]
    if any(not n for n in names):raise GateStop(f"empty island name in {name}")
    if len(names)!=len(set(names)):raise GateStop(f"ambiguous duplicated island names in {name}")
    taxa=[island_key(x) for x in header[0][1:]]
    ctaxa=[canonical(x) for x in taxa]
    if len(ctaxa)!=len(set(ctaxa)) or any(not x for x in ctaxa):
        raise GateStop(f"nonunique or empty species header in {name}")
    return names,taxa

def inspect_files(species_path,source_dir,contract):
    if contract.get("schema")!="structural.external_archipelago_mammal_checklist_preintake.v1_188":
        raise GateStop("contract schema mismatch")
    frozen=contract["frozen_original"]
    raw_species=species_path.read_bytes()
    if hashlib.sha256(raw_species).hexdigest()!=frozen["original_species_universe_sha256"]:
        raise GateStop("frozen original 529 species universe SHA mismatch")
    rows=list(csv.DictReader(io.StringIO(raw_species.decode("utf-8-sig"))))
    if len(rows)!=529 or any(not r.get("species_name") for r in rows):
        raise GateStop("ultrarare species universe mismatch")
    focals={canonical(r["species_name"]):r["species_name"] for r in rows}
    if len(focals)!=529:raise GateStop("focal canonical species collision")
    out=[];listings=[];unique_islands=set();unique_matches=set();groups_with_match=0;total=0
    for expected in contract["files"]:
        name=expected["name"];path=source_dir/name
        raw=path.read_bytes()
        if not raw or len(raw)>200_000:raise GateStop(f"source size invalid: {name}")
        labels,taxa=schema_only(raw,name)
        match=sorted(set(canonical(s) for s in taxa)&set(focals))
        if match:groups_with_match+=1
        unique_matches.update(match)
        total+=len(labels)
        for island in labels:
            unique_islands.add((expected["group"],island))
            listings.append({"group":expected["group"],"island_name":island})
        out.append({
          "file":name,"file_id":int(expected["id"]),"group":expected["group"],
          "source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),
          "named_islands":len(labels),"taxon_header_count":len(taxa),
          "exact_ultrarare_taxon_header_overlap":len(match),
          "overlap_species_names":[focals[z] for z in match]
        })
    assert len(out)==9
    gate=contract["preoutcome_thresholds"]
    reasons=[]
    if total!=int(contract["source"]["reported_islands"]):reasons.append("published total island rows drift")
    if len(unique_matches)<gate["min_exact_focal_species_header_overlap"]:reasons.append("too few exact focal species header overlaps")
    if len(unique_islands)<gate["min_named_external_islands"]:reasons.append("too few named external islands")
    if groups_with_match<gate["min_archipelagos_with_focal_species_headers"]:reasons.append("too few archipelagos with focal species headers")
    return listings,{
      "schema":"structural.external_archipelago_mammal_checklist_header_audit.v1_188",
      "status":contract["gate_outcome"]["if_header_support_fails"] if reasons else contract["gate_outcome"]["if_header_support_passes"],
      "reason_codes":reasons,
      "files":out,
      "published_islands":int(contract["source"]["reported_islands"]),
      "observed_row_name_count":total,
      "unique_group_island_names":len(unique_islands),
      "unique_529_species_header_overlap":len(unique_matches),
      "groups_with_header_overlap":groups_with_match,
      "frozen_529_species_universe_sha256":frozen["original_species_universe_sha256"],
      "external_checklist_binary_cells_decoded":0,
      "original_mammal_heldout_cells_opened":0,
      "island_id_crosswalk_available":False,
      "external_endpoint_scoring_authorized":False,
      "scientific_evidence_produced":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("species_universe",type=Path)
    ap.add_argument("source_dir",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--receipt",type=Path,required=True)
    ap.add_argument("--island-names",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        names,receipt=inspect_files(a.species_universe,a.source_dir,c)
        a.island_names.parent.mkdir(parents=True,exist_ok=True)
        a.island_names.write_text(json.dumps(names,indent=2,ensure_ascii=False)+"\n")
        receipt["island_names_sha256"]=hashlib.sha256(a.island_names.read_bytes()).hexdigest()
        code=0
    except (OSError,ValueError,UnicodeError,KeyError,GateStop) as ex:
        receipt={
          "schema":"structural.external_archipelago_mammal_checklist_header_audit.v1_188",
          "status":"STOP_EXTERNAL_CHECKLIST_PRE_OUTCOME_INTAKE",
          "reason":str(ex),
          "external_checklist_binary_cells_decoded":0,
          "original_mammal_heldout_cells_opened":0,
          "external_endpoint_scoring_authorized":False,
          "scientific_evidence_produced":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(receipt,sort_keys=True,ensure_ascii=False))
    return code

if __name__=="__main__":
    raise SystemExit(main())
