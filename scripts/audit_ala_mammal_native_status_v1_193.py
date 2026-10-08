#!/usr/bin/env python3
"""Response-opaque ALA native-status screening of already-public aggregate names."""
from __future__ import annotations
import argparse,csv,hashlib,json,re,unicodedata
from pathlib import Path

class Stop(ValueError):
    pass

def norm(x):
    return " ".join(unicodedata.normalize("NFC",str(x)).replace("."," ").replace("_"," ").split()).casefold()

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def git_blob_sha1(blob):
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

def author_exclusions(source_text,sections):
    removed={}
    for sec in sections:
        start=source_text.find(sec["start"])
        if start<0:raise Stop("source R section start missing: "+sec["start"])
        end=source_text.find(sec["end"],start+len(sec["start"]))
        if end<0 or end<=start:raise Stop("source R section end missing: "+sec["end"])
        span=source_text[start:end]
        names=[norm(m.group(1)) for m in re.finditer(r'"([^"]+)"',span)]
        if not names:raise Stop("source R section is empty: "+sec["reason"])
        for key in names:
            removed.setdefault(key,sec["reason"])
    return removed

def audit(manifest,geometry,source_bytes,contract):
    if contract["schema"]!="structural.ala_mammal_native_status_gate.v1_193":
        raise Stop("contract schema mismatch")
    req=contract["input_identity"]
    if manifest.get("status")!=req["v1_192_required_status"]:raise Stop("v1.192 status drift")
    if manifest.get("distinct_exact_focal_taxon_overlap")!=req["focal_name_overlap"]:
        raise Stop("v1.192 focal overlap drift")
    if manifest.get("ALA_island_x_species_pairs_semantically_decoded")!=0 or manifest.get("ALA_FID_values_from_response_archive_read")!=0:
        raise Stop("pre-existing external event response already opened")
    if manifest.get("original_heldout_response_values_read")!=0:
        raise Stop("original heldout response opened")
    if geometry.get("exact_one_to_one_heldout_matches")!=req["exact_heldout_islands"]:
        raise Stop("v1.191.2 geometry drift")
    if geometry.get("crosswalk_sha256")!=manifest.get("original_island_crosswalk_sha256"):
        raise Stop("v1.191/192 crosswalk drift")
    if geometry.get("biological_scoring_authorized") is not False:raise Stop("pre-gate scoring authorized")

    upstream=contract["author_taxon_exclusions"]
    if git_blob_sha1(source_bytes)!=upstream["source_git_blob_sha1"]:
        raise Stop("pinned R source git blob drift")
    text=source_bytes.decode("utf-8")
    removed=author_exclusions(text,upstream["sections"])
    raw=manifest["matching_focal_species"]
    if len(raw)!=70 or len({norm(x) for x in raw})!=70:
        raise Stop("70-name exact population drift")
    expected=upstream["expected_excluded_overlap"]
    for name,reason in expected.items():
        if removed.get(norm(name))!=reason:raise Stop("author exclusion drift: "+name)
    extra={norm(name):(name,obj["reason"]) for name,obj in contract["conservative_additional_exclusions"].items()}
    result=[];author_count=extra_count=0
    for name in sorted(raw,key=norm):
        n=norm(name)
        if n in removed:
            reason=removed[n];eligible=False;author_count+=1
        elif n in extra:
            reason=extra[n][1];eligible=False;extra_count+=1
        else:
            reason="provisional_taxon_only_not_island_nativeness";eligible=True
        result.append({"species_name":name,"eligible_provisional":str(eligible).lower(),"screening_reason":reason})
    e=contract["expected_outcome_without_opening_pairs"]
    retained=sum(x["eligible_provisional"]=="true" for x in result)
    if (len(result),author_count,extra_count,retained)!=(e["exact_matching_names_before_screen"],e["excluded_by_author_source"],e["excluded_conservative"],e["provisionally_retained_taxa"]):
        raise Stop(f"predeclared species status counts fail {(len(result),author_count,extra_count,retained)}")
    return result,{
        "schema":"structural.ala_mammal_native_status_result.v1_193",
        "status":"HOLD_ALA_65_PROVISIONAL_TAXA_PENDING_EXACT_PAIR_PROTOCOL",
        "islands_exactly_matched":167,"names_examined":70,"excluded_author_rules":author_count,
        "excluded_conservative":extra_count,"provisional_taxa":retained,
        "excluded_taxa":{x["species_name"]:x["screening_reason"] for x in result if x["eligible_provisional"]=="false"},
        "source_R_blob_sha1":upstream["source_git_blob_sha1"],
        "site_specific_nativeness_verified":False,
        "external_species_x_island_positive_pairs_opened":0,
        "original_heldout_labels_opened":0,
        "external_FID_read":False,"biological_scoring_authorized":False,
        "independently_surveyed_absences":False,"eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("geometry_receipt",type=Path)
    ap.add_argument("source_r_script",type=Path)
    ap.add_argument("--contract",type=Path,default=Path("development/global_mammals_ala_native_status_gate_v1_193.json"))
    ap.add_argument("--eligibility-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        rows,receipt=audit(json.loads(a.manifest.read_text()),json.loads(a.geometry_receipt.read_text()),a.source_r_script.read_bytes(),c)
        a.eligibility_output.parent.mkdir(parents=True,exist_ok=True)
        with a.eligibility_output.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["species_name","eligible_provisional","screening_reason"],lineterminator="\n")
            w.writeheader();w.writerows(rows)
        receipt["eligibility_table_sha256"]=digest(a.eligibility_output)
        exitcode=0
    except (OSError,ValueError,KeyError,UnicodeError,json.JSONDecodeError) as exc:
        receipt={"schema":"structural.ala_mammal_native_status_result.v1_193",
                 "status":"STOP_ALA_AUTHOR_NATIVE_FILTER_OR_METADATA_DRIFT","reason":str(exc),
                 "external_species_x_island_positive_pairs_opened":0,"original_heldout_labels_opened":0,
                 "biological_scoring_authorized":False,"eBird_used":False}
        exitcode=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return exitcode

if __name__=="__main__":raise SystemExit(main())
