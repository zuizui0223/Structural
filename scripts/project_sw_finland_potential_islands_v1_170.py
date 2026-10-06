#!/usr/bin/env python3
"""Project only species and Potential_islands from the SW Finland supplement.

Input is text produced by pdftotext -layout. Future summary columns to the
right of Num_colonized are discarded as raw text before row parsing.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_potential_lookup_execution_contract_v1_170.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def locate_header(lines:list[str])->tuple[int,int,int]:
    for i,line in enumerate(lines):
        if all(k in line for k in ("species","Potential_islands","Num_colonized","Prop_colonized")):
            p=line.index("Potential_islands")
            n=line.index("Num_colonized")
            if not 0<p<n: raise Stop("invalid supplementary header offsets")
            return i,p,n
    raise Stop("species table header not found")

def project_text(text:str,contract:dict)->tuple[list[tuple[str,int]],dict]:
    if contract.get("schema")!="structural.sw_finland_potential_lookup_execution_contract.v1_170":
        raise Stop("execution contract schema drift")
    lines=text.splitlines()
    start,pot_start,num_start=locate_header(lines)
    rows=[]
    seen=set()
    pending=[]
    table_end_found=False
    prefix_lines_examined=0
    future_summary_values_parsed=0

    for line in lines[start+1:]:
        if "Island_name" in line and "Euref_X" in line and "Potential_spp" in line:
            table_end_found=True
            break
        if not line.strip():
            continue

        # Critical firewall: characters at Num_colonized and to the right are
        # discarded before species/Potential_islands parsing.
        prefix=line[:num_start]
        prefix_lines_examined+=1
        species_part=norm(prefix[:pot_start])
        potential_part=prefix[pot_start:num_start].strip()

        # Ignore page furniture and repeated table headers.
        if species_part.lower() in {"species",""} and "Potential_islands" in potential_part:
            continue
        if species_part.startswith("Ecography") or species_part.startswith("ECOG-"):
            continue

        m=re.search(r"\b(\d{1,3})\b",potential_part)
        if m is None:
            # Layout extraction can wrap a long taxon label before its numeric
            # columns. Only left-prefix text is accumulated.
            if species_part and not species_part.isdigit():
                pending.append(species_part)
            continue

        p=int(m.group(1))
        if not 0<=p<=471:
            raise Stop(f"Potential_islands outside [0,471]: {p}")
        pieces=[x for x in pending if x]
        if species_part: pieces.append(species_part)
        pending=[]
        sp=norm(" ".join(pieces))
        sp=re.sub(r"\s+"," ",sp)
        if not sp:
            raise Stop("blank species at parsed Potential_islands row")
        if sp in seen:
            raise Stop(f"duplicate species: {sp}")
        seen.add(sp)
        rows.append((sp,p))

    if not table_end_found:
        raise Stop("species table end marker not found")
    expected=int(contract["allowed_projection"]["expected_unique_species"])
    if len(rows)!=expected:
        raise Stop(f"expected {expected} projected species, found {len(rows)}")
    anchors=contract["anchor_checks"]
    lookup=dict(rows)
    for sp,p in anchors.items():
        if lookup.get(sp)!=int(p):
            raise Stop(f"anchor mismatch: {sp}: {lookup.get(sp)} != {p}")

    rows.sort(key=lambda x:x[0])
    receipt={
      "schema":"structural.sw_finland_potential_lookup_projection_result.v1_170",
      "status":"SAFE_SPECIES_POTENTIAL_ISLANDS_PROJECTED",
      "candidate_id":contract["candidate_id"],
      "species_count":len(rows),
      "minimum_potential_islands":min(p for _,p in rows),
      "maximum_potential_islands":max(p for _,p in rows),
      "header_potential_column_start":pot_start,
      "header_future_column_start":num_start,
      "table_end_found":table_end_found,
      "prefix_lines_examined":prefix_lines_examined,
      "future_summary_values_parsed":future_summary_values_parsed,
      "future_summary_values_persisted":0,
      "row_level_recent_outcome_opened":False,
      "counts_as_empirical_evidence":False
    }
    return rows,receipt

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("layout_text",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--safe-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text(encoding="utf-8"))
        rows,r=project_text(a.layout_text.read_text(encoding="utf-8",errors="strict"),c)
        a.safe_output.parent.mkdir(parents=True,exist_ok=True)
        with a.safe_output.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n");w.writerow(["species","Potential_islands"]);w.writerows(rows)
        r["safe_projection_sha256"]=sha256_file(a.safe_output)
        code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,UnicodeDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_potential_lookup_projection_result.v1_170",
          "status":"STOP_SUPPLEMENTARY_PROJECTION",
          "reason":str(exc),
          "future_summary_values_parsed":0,
          "future_summary_values_persisted":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False
        };code=2
    txt=json.dumps(r,indent=2,sort_keys=True)+"\n"
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(txt,encoding="utf-8")
    print(txt,end="");return code

if __name__=="__main__":raise SystemExit(main())
