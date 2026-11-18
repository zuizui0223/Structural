#!/usr/bin/env python3
"""PLOS Weiss2016 six-guild original DOC: temporary text table SHAPE only.

Original DOC is SHA256 locked. Antiword private text is never logged/exported.
No per-species trophic crosswalk is constructed. No Gloor species response read.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,subprocess,tempfile,urllib.error,urllib.request
from pathlib import Path

from weiss2016_plos_r2_original_blob_gate import (
    original_publisher_location_one_get, validate_original_r2_location,
    NoRedirect, SourceStop, R2_HOST, LOCATION_SHA, OLE_MAGIC, MAX_SIZE,
)

PRESPEC="docs/FOREST_MACRO_WEISS2016_ORIGINAL_DOC_GUILD_SCHEMA_PRESPEC_20261118.md"
EXPECTED_BYTES=488960
EXPECTED_SHA="f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de"
GUILDS="mnpsxz"
PUNCT=re.compile(r"\b[A-Z][a-z]{2,}\s+[a-z][a-z\-]{2,}\b")
TOKEN={k:re.compile(r"(?<![A-Za-z])"+k+r"(?![A-Za-z])") for k in GUILDS}
TABLE_TAGS={k:re.compile(r"<"+k+r"(?:\s|>)",re.I) for k in ("table","informaltable","row","entry")}

def original_doc():
    loc=original_publisher_location_one_get()
    validate_original_r2_location(loc)
    req=urllib.request.Request(loc,headers={
        "Accept":"application/msword,application/octet-stream;q=0.8,*/*;q=0.2",
        "User-Agent":"Structural-Weiss2016-PLOS-pinned-S1-structure-only/1.0",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=55) as resp:
            if resp.status!=200:raise SourceStop("SOURCE_ORIGINAL_ISSUED_DOC_NOT_HTTP200")
            raw=resp.read(MAX_SIZE+1)
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_AUTHOR_PLOS_S1_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_AUTHOR_PLOS_S1_TRANSPORT_"+type(exc).__name__) from None
    if (len(raw)!=EXPECTED_BYTES or
        hashlib.sha256(raw).hexdigest()!=EXPECTED_SHA or
        not raw.startswith(OLE_MAGIC)):
        raise SourceStop("SOURCE_WEISS2016_ORIGINAL_PUBLISHED_DOC_SHA_SIZE_OR_TYPE_DRIFT")
    return raw

def private_text_shape(source,docbook=""):
    if not source or len(source)>3_000_000:
        raise SourceStop("SOURCE_ANTIWORD_EXTRACT_TEXT_EMPTY_OR_OVERLIMIT")
    lines=source.splitlines()
    header_flags={k:bool(re.search(r"\b"+k+r"\b",source,re.I))
                  for k in ("Species","Family","Guild","Trophic","Status")}
    candidate=[line for line in lines if PUNCT.search(line)]
    exact_letter={k:sum(len(pattern.findall(line)) for line in lines)
                  for k,pattern in TOKEN.items()}
    return {
        "source_private_extraction_nonempty":True,
        "source_private_antiword_stdout_utf8_bytes":len(source.encode("utf-8",errors="replace")),
        "source_private_total_text_lines":len(lines),
        "source_private_nonblank_lines":sum(bool(s.strip()) for s in lines),
        "approximate_lines_with_Latin_binomial_SHAPES_ONLY":len(candidate),
        "source_frozen_code_single_letter_lexical_counts_NOT_GUILD_RECORDS":exact_letter,
        "original_source_text_header_word_presence_ONLY":header_flags,
        "optional_docbook_XML_raw_bytes_privately_processed":len(docbook.encode("utf-8",errors="replace")) if docbook else 0,
        "optional_docbook_table_tag_lexical_counts":{
            key:len(rx.findall(docbook)) if docbook else 0
            for key,rx in TABLE_TAGS.items()},
        "original_doc_source_text_or_species_taxon_values_NOT_EXPORTED":True,
        "original_species_to_guild_pairs_NOT_EXTRACTED":True,
        "counts_not_proof_of_original_512_species_or_6valid_guilds":True,
    }

def source_private_run(raw):
    antiword=shutil.which("antiword")
    if not antiword:
        raise SourceStop("SOURCE_ANTIWORD_NOT_INSTALLED")
    with tempfile.TemporaryDirectory(prefix="structural_sourceonly_weiss2016_") as t:
        path=Path(t)/"original_author_S1.doc"
        path.write_bytes(raw)
        try:
            cmd=subprocess.run([antiword,"-t","-w","0",str(path)],
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                 timeout=45,check=False)
        except (subprocess.TimeoutExpired,OSError):
            raise SourceStop("SOURCE_ANTIWORD_TEXT_EXECUTION_STOP") from None
        if cmd.returncode or not cmd.stdout:
            raise SourceStop("SOURCE_ANTIWORD_TEXT_FORMAT_STOP")
        if len(cmd.stdout)>3_000_000:
            raise SourceStop("SOURCE_ANTIWORD_TEXT_TOO_LARGE")
        source=cmd.stdout.decode("utf-8",errors="replace")
        db=""
        try:
            doc=subprocess.run([antiword,"-x","db",str(path)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                timeout=45,check=False)
            if doc.returncode==0 and len(doc.stdout)<3_000_000:
                db=doc.stdout.decode("utf-8",errors="replace")
        except (subprocess.TimeoutExpired,OSError):
            db=""
        shape=private_text_shape(source,db)
    return shape

def known_truth():
    s="Species Family Trophic Guild\nCerambyx cerdo Cerambycidae x\nAbdera flexuosa Melandryidae m\n"
    d=private_text_shape(s,"<informaltable><row><entry>GUILDS_HIDDEN</entry></row></informaltable>")
    assert d["approximate_lines_with_Latin_binomial_SHAPES_ONLY"]==2
    assert d["optional_docbook_table_tag_lexical_counts"]["row"]==1
    assert d["source_frozen_code_single_letter_lexical_counts_NOT_GUILD_RECORDS"]["x"]==1
    assert all(x not in json.dumps(d) for x in ("Cerambyx","Abdera","GUILDS_HIDDEN"))
    print("SYNTHETIC_WEISS2016_DOC_SCHEMA_TEXT_REDACTION_AND_GUILD_NONCLAIM_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out needed")
    out={
        "schema":"structural.Weiss2016_original_PLOS_S1_DOC_schema_only.v1",
        "precommit":PRESPEC,"source_original_DOI":"10.1371/journal.pone.0149506.s001",
        "source_original_S1_expected_bytes":EXPECTED_BYTES,
        "source_original_S1_expected_sha256":EXPECTED_SHA,
        "source_original_PLOS_issuer_redirect_SHA256":LOCATION_SHA,
        "source_original_issuer_R2_domain":R2_HOST,
        "original_DOC_trophic_source_text_decoded_ONLY_FOR_METHOD_SHAPE":True,
        "original_species_to_guild_ontology_NOT_VERIFIED":True,
        "original_Gloor_Carpathian_species_identity_abundance_RESPONSES_UNREAD":True,
        "previous_original_Franzen_Dryad_HTTP401_NOT_RETRIED":True,
        "all_previous_Finland_Germany_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
        "new_biodiversity_effect_CALCULATED":False,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=original_doc()
        out["original_source_private_DOC_table_structure_only"]=source_private_run(raw)
        out["status"]="ORIGINAL_WEISS2016_DOC_PRIVATE_STRUCTURE_DIAG_ONLY"
    except SourceStop as exc:
        out["status"]=str(exc)
        out["source_method_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_original_author_DOC_private_schema_aggregate_only.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_ORIGINAL_DOC_TABLE_SCHEMA",out["status"])
    print("NO_GUILD_BY_SPECIES_PAIRS_EXPORTED_OR_GLOOR_OUTCOME_READ")

if __name__=="__main__":main()
