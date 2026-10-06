#!/usr/bin/env python3
"""Extract only species + Potential_islands from the frozen Ecography supplement.

Input is pdftotext -layout output. Future colonization summary fields are used
only as trailing row-shape delimiters and are never persisted, returned, or
used for eligibility.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_potential_islands_projection_contract_v1_170.json"

class Stop(RuntimeError): pass

ROW_RE=re.compile(
    r"^\s*(?P<species>.+?)\s+"
    r"(?P<potential>\d{1,3})\s+"
    r"(?P<num>\d+)\s+"
    r"(?P<prop>(?:\d+(?:\.\d*)?|\.\d+))\s+"
    r"(?P<random>NA|[-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*$"
)

def norm_species(x:str)->str:
    return " ".join(unicodedata.normalize("NFC",str(x)).strip().split())

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise Stop("contract must be JSON object")
    return x

def extract(text:str,contract:dict):
    if contract.get("schema")!="structural.sw_finland_potential_islands_projection_contract.v1_170":
        raise Stop("contract schema drift")
    start_i=text.find("Potential_islands")
    if start_i<0:raise Stop("species table start not found")
    end_i=text.find("Island_name",start_i)
    if end_i<0:raise Stop("island table end marker not found")
    segment=text[start_i:end_i]

    rows=[];seen={};unparsed=[]
    for raw in segment.splitlines()[1:]:
        line=raw.strip()
        if not line or line.isdigit():continue
        if "Potential_islands" in line or line.startswith("ECOG-05013"):
            continue
        m=ROW_RE.match(line)
        if not m:
            if any(ch.isalpha() for ch in line):unparsed.append(line[:80])
            continue
        species=norm_species(m.group("species"))
        potential=int(m.group("potential"))
        if not species:raise Stop("blank species")
        if not 0<=potential<=471:raise Stop(f"Potential_islands outside range for {species}")
        if species in seen:raise Stop(f"duplicate species: {species}")
        seen[species]=potential
        rows.append({
            "species":species,
            "Potential_islands":potential,
            "historical_source_count":471-potential,
        })

    expected=int(contract["validation"]["expected_unique_species"])
    if len(rows)!=expected:
        raise Stop(
            f"expected {expected} parsed species, found {len(rows)}; "
            f"unparsed_alpha_lines={len(unparsed)}"
        )
    for species,expected_p in contract["validation"]["sentinels"].items():
        if seen.get(species)!=int(expected_p):raise Stop(f"sentinel mismatch for {species}")
    rows.sort(key=lambda r:r["species"])
    return rows

def write_safe(rows,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(
            f,fieldnames=["species","Potential_islands","historical_source_count"],
            lineterminator="\n"
        )
        w.writeheader();w.writerows(rows)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("layout_text",type=Path)
    p.add_argument("--source-pdf",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--safe-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=load(a.contract)
        rows=extract(a.layout_text.read_text(encoding="utf-8",errors="strict"),c)
        write_safe(rows,a.safe_output)
        receipt={
          "schema":"structural.sw_finland_potential_islands_projection_result.v1_170",
          "status":"T0_ONLY_POTENTIAL_ISLANDS_LOOKUP_PROJECTED",
          "candidate_id":c["candidate_id"],
          "source_pdf_sha256":sha256_file(a.source_pdf),
          "safe_lookup_sha256":sha256_file(a.safe_output),
          "species_count":len(rows),
          "minimum_Potential_islands":min(r["Potential_islands"] for r in rows),
          "maximum_Potential_islands":max(r["Potential_islands"] for r in rows),
          "species_with_zero_historical_sources":sum(r["historical_source_count"]==0 for r in rows),
          "future_summary_values_persisted":0,
          "future_summary_values_used_for_eligibility":False,
          "archive_outcome_values_read":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False,
          "next_gate":c["next_gate"],
        };code=0
    except (OSError,UnicodeDecodeError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        a.safe_output.unlink(missing_ok=True)
        receipt={
          "schema":"structural.sw_finland_potential_islands_projection_result.v1_170",
          "status":"STOP_SUPPLEMENT_T0_PROJECTION",
          "reason":str(exc),
          "future_summary_values_persisted":0,
          "future_summary_values_used_for_eligibility":False,
          "archive_outcome_values_read":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False,
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
