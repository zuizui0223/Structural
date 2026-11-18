#!/usr/bin/env python3
"""Source-only PLOS Weiss2016 DOC layout/row-boundary feasibility diagnosis.

Original source OLE DOC is SHA-frozen. antiword text is private; NEVER exports
individual species/guild pair, original token or any Carpathian taxa/abundances.
"""
from __future__ import annotations
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path

from weiss2016_plos_doc_schema_only import original_doc, PUNCT, TOKEN, SourceStop

PRESPEC="docs/FOREST_MACRO_WEISS2016_S1_GUILD_LAYOUT_DIAGNOSTIC_PRESPEC_20261118.md"
WIDTHS=(0,120,200)
STRUCT={
    "docbook_para":re.compile(r"<(?:\w+:)?para(?:\s|>)",re.I),
    "docbook_row":re.compile(r"<(?:\w+:)?row(?:\s|>)",re.I),
    "docbook_entry":re.compile(r"<(?:\w+:)?entry(?:\s|>)",re.I),
    "docbook_table":re.compile(r"<(?:\w+:)?(?:table|informaltable)(?:\s|>)",re.I),
}
def private_line_metrics(text):
    lines=[line for line in text.splitlines() if line.strip()]
    paired=single_species=multiple_species=single_guild=multiple_guild=0
    for line in lines:
        species=len(PUNCT.findall(line))
        guild=sum(len(rx.findall(line)) for rx in TOKEN.values())
        single_species += species==1
        multiple_species += species>1
        single_guild += guild==1
        multiple_guild += guild>1
        paired += species==1 and guild==1
    return {
       "source_extracted_total_lines":len(text.splitlines()),
       "source_extracted_nonblank_lines":len(lines),
       "source_lines_EXACTLY_one_Latin_binomial_shape":single_species,
       "source_lines_multiple_Latin_binomial_shapes":multiple_species,
       "source_lines_EXACTLY_one_standalone_sixcode_token":single_guild,
       "source_lines_multiple_standalone_sixcode_tokens":multiple_guild,
       "source_lines_one_binomial_ONE_code_both":paired,
       "source_TAB_separator_count":text.count("\t"),
       "source_FORMFEED_separator_count":text.count("\f"),
       "source_VERTICALTAB_separator_count":text.count("\v"),
       "source_double_or_more_SPACE_separator_occurrences":len(re.findall(r" {2,}",text)),
       "source_guild_token_counts_NOT_individual_guild_records":{
            k:len(rx.findall(text)) for k,rx in TOKEN.items()},
       "original_per_line_and_original_species_guild_values_NOT_EXPORTED":True,
       "unlabelled_structural_counts_not_valid_taxonomic_identifications":True,
    }

def layout_diag(original):
    antiword=shutil.which("antiword")
    if antiword is None:
        raise SourceStop("SOURCE_ANTIWORD_NOT_INSTALLED")
    report={}
    with tempfile.TemporaryDirectory(prefix="structural_weiss_layout_sourceonly_") as folder:
        p=Path(folder)/"frozen_original_weiss_S1.doc"
        p.write_bytes(original)
        for width in WIDTHS:
            try:
                r=subprocess.run([antiword,"-t","-w",str(width),str(p)],
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    timeout=45,check=False)
            except (OSError,subprocess.TimeoutExpired):
                raise SourceStop("SOURCE_PRIVATE_ANTIWORD_TEXT_LAYOUT_STOP") from None
            if r.returncode!=0 or not 10<len(r.stdout)<2_000_000:
                raise SourceStop("SOURCE_PRIVATE_ANTIWORD_TEXT_LAYOUT_EMPTY_OR_TOO_LARGE")
            text=r.stdout.decode("utf-8",errors="replace")
            report["width_"+str(width)]=private_line_metrics(text)
        try:
            d=subprocess.run([antiword,"-x","db",str(p)],stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,timeout=45,check=False)
        except (OSError,subprocess.TimeoutExpired):
            raise SourceStop("SOURCE_PRIVATE_ANTIWORD_DOCBOOK_LAYOUT_STOP") from None
        if d.returncode!=0 or not d.stdout or len(d.stdout)>2_000_000:
            raise SourceStop("SOURCE_PRIVATE_ANTIWORD_DOCBOOK_EMPTY_OR_OVERSIZE")
        xml=d.stdout.decode("utf-8",errors="replace")
        report["docbook_structure_tags_COUNT_ONLY"]={
            k:len(rx.findall(xml)) for k,rx in STRUCT.items()
        }
    report["source_guild_or_species_text_values_EXPORTED"]=False
    report["Carpathian_Gloor_taxa_or_abundance_DATA_OPENED"]=False
    report["species_to_guild_pair_MAPPING_ESTABLISHED"]=False
    # This is only a method-layout gate; never infer original species coverage.
    report["status"]="ORIGINAL_WEISS_DOC_SOURCE_LAYOUT_DIAGNOSTIC_ONLY"
    return report

def known_truth():
    q=private_line_metrics("Cerambyx cerdo x\nAbdera flexuosa m\n")
    assert q["source_lines_one_binomial_ONE_code_both"]==2
    assert q["source_lines_EXACTLY_one_Latin_binomial_shape"]==2
    assert all(name not in json.dumps(q) for name in ("Cerambyx","Abdera"))
    print("SYNTHETIC_WEISS2016_ORIGINAL_PRIVATE_DOC_LAYOUT_SHAPE_NO_TAXON_EXPORT_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={
       "schema":"structural.Weiss2016_original_DOC_source_layout_method_only.v1",
       "precommit":PRESPEC,
       "source_original_DOI":"10.1371/journal.pone.0149506.s001",
       "source_original_DOC_locked_sha256":"f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de",
       "source_Gloor_species_taxon_identity_or_abundance_OPENED":False,
       "previous_Franzen_Dryad_HTTP401_NOT_RETRIED":True,
       "earlier_Finland_Germany_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED":True,
       "new_ecological_effect_estimated":False,
       "eBird_used":False,"TinyFish_used":False
    }
    try:
        out["method_only_source_layout_diagnostic"]=layout_diag(original_doc())
        out["status"]="ORIGINAL_WEISS_DOC_SOURCE_LAYOUT_DIAGNOSTIC_ONLY"
    except SourceStop as e:
        out["status"]=str(e)
        out["source_method_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_source_DOC_layout_token_counts_anonymous_only.json").write_text(
       json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_ORIGINAL_DOC_LAYOUT_GATE",out["status"])
    print("NO_SPECIES_GUILD_PAIRING_OR_GLOOR_OUTCOMES")
if __name__=="__main__":main()
