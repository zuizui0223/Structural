#!/usr/bin/env python3
"""Only names from a frozen pilot manifest, not pilot counts or external field incidence."""
import argparse,csv,hashlib,json,unicodedata
from pathlib import Path
HASH="4f801eac218edb00f319cd04416af3c6e7d7a90e04b68868eeed47f4d403dfd9"
def norm(text):
    return " ".join(unicodedata.normalize("NFC",text).split()).casefold()
def compare(source,config):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=HASH:
        raise ValueError("Original frozen taxon manifest checksum mismatch")
    with source.open(encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f)
        if "species_name" not in (rd.fieldnames or []):raise ValueError("Missing species column")
        original=[r["species_name"] for r in rd] # Never access pilot occurrence counts.
    if len(original)!=529 or len(set(map(norm,original)))!=529:raise ValueError("Unexpected 529 focal species")
    names=config["published_species_names"]
    if len(names)!=18 or len(set(map(norm,names)))!=18:raise ValueError("Unexpected published taxa")
    mapping={norm(x):x for x in original}
    common=[{"published":name,"original_frozen":mapping[norm(name)]}
            for name in names if norm(name) in mapping]
    return {"schema":"structural.zhoushan_published_taxa_overlap_result.v1_230",
        "status":"STOP_ZERO_TAXON_OVERLAP" if not common else "TAXON_OVERLAP_ONLY",
        "source_published_mammal_taxa":18,"original_ultrarare_taxa":529,
        "exact_shared_species_count":len(common),"exact_shared_binomials":common,
        "field_species_island_incidence_opened":False,
        "original_mammal_heldout_labels_opened":False,
        "original_mammal_predictions_scored":False,
        "fresh_biological_confirmation":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("frozen_taxa",type=Path);p.add_argument("--ledger",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:r=compare(a.frozen_taxa,json.loads(a.ledger.read_text(encoding="utf-8")))
    except Exception as exc:r={"schema":"structural.zhoushan_published_taxa_overlap_result.v1_230",
       "status":"STOP_TAXON_IDENTITY_PRECHECK","error_class":type(exc).__name__,
       "field_species_island_incidence_opened":False,
       "original_mammal_heldout_labels_opened":False}
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
    if r["status"]=="STOP_TAXON_IDENTITY_PRECHECK":raise SystemExit(2)
