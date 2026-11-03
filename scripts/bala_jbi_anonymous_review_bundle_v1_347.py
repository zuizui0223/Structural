#!/usr/bin/env python3
"""BALA v1.347: build clean JBI double-anonymous reviewer materials.

Editorial packaging ONLY: manuscript and source-free island numerical
supplement. No original Event/Occurrence, no field species values, no
image rendering and no recalculation of ecological effects.

Keeps internal project work-in-progress source, signatures and author
review requirements in the GitHub development draft, not in the
reviewer-visible manuscript or Supplementary Table S1.

Output section order follows current JBI Guide for Authors:
title/running title/structured abstract/main text, REFERENCES,
Data Accessibility, figure legends. Title-page biosketch and signed author
statements are NOT generated or fabricated.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANUSCRIPT=ROOT/"docs/BALA_JBI_ANONYMIZED_FULL_MANUSCRIPT_DRAFT_V1_345.md"
S1=ROOT/"docs/BALA_JBI_SUPPLEMENTARY_TABLE_S1_ISLAND_UNCERTAINTY_V1_346.md"

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def anonymize(main,supp):
    if (not main.startswith("# Decadal arthropod turnover")
        or "### Internal non-submission notes" not in main
        or "## Declarations requiring author review before submission" not in main
        or "## Figure legends" not in main
        or "## References (" not in main
        or "## Data availability and reproducibility" not in main):
        raise ValueError("Source manuscript not the reviewed JBI v1.346 draft")
    public=main.split("### Internal non-submission notes",1)[0]
    before,data_tail=public.split("## Data availability and reproducibility",1)
    data,notes_tail=data_tail.split("## Declarations requiring author review before submission",1)
    notes,legend_tail=notes_tail.split("## Figure legends",1)
    if "Authors and contributions" not in notes:
        raise ValueError("Author-approval checklist absent from internal-only source")
    legend,references=legend_tail.split("## References (",1)
    # Strip internal reviewer-workflow notes and reorder public sections.
    out=(
        before.rstrip()+"\n\n"+
        "## References ("+references.rstrip()+"\n\n"+
        "## Data availability and reproducibility"+data.rstrip()+"\n\n"+
        "## Figure legends"+legend.rstrip()+"\n"
    )
    if ("**Aim:**" not in out or "**Main conclusions:**" not in out
        or "### 4.5 | Conclusions" not in out
        or "seven-island 95% t interval" not in out
        or "−0.440 to +0.089" not in out):
        raise ValueError("Anonymized text is missing core journal or science qualifications")
    abstract=out.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    words=len(abstract.replace("**","").strip().split())
    if not 140<=words<=300:
        raise ValueError("Reviewer-facing structured abstract exceeds JBI 300 word limit")
    if (len(out.splitlines()[0].removeprefix("# "))>115
        or "github.com/zuizui0223" in out
        or "Internal non-submission" in out
        or "Declarations requiring author review" in out):
        raise ValueError("Manuscript anonymization or journal title limit failed")

    if (not supp.startswith("# Supplementary Table S1")
        or "**Evidence and exact reproducibility:**" not in supp
        or "−0.4399" not in supp
        or "0.187500" not in supp
        or "128" not in supp):
        raise ValueError("Evidence-locked source free Supplement S1 missing")
    reviewer_s1=supp.split("**Evidence and exact reproducibility:**",1)[0].rstrip()+"\n"
    if ("github.com" in reviewer_s1
        or "source original" in reviewer_s1.lower() and "date" in reviewer_s1.lower()
        and "authors' identifying" in reviewer_s1.lower()):
        raise ValueError("Reviewer-facing supplement provenance exposure")
    return out,reviewer_s1,words

def build(main,supp,dest):
    doc,s1,words=anonymize(main,supp)
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"JBI_anonymized_main_text_v1_347.md").write_text(doc,encoding="utf-8")
    (dest/"JBI_anonymized_Supplementary_Table_S1_v1_347.md").write_text(s1,encoding="utf-8")
    original_manifest=dest/"figure_bundle_manifest.json"
    if not original_manifest.exists():
        raise ValueError("First create v1.345 source-free figure/CSV bundle and SHA manifest")
    ledger=json.loads(original_manifest.read_text(encoding="utf-8"))
    if (ledger.get("status")!="ORIGINAL_BALA_NUMERICAL_FIGURES_GENERATED_WITHOUT_BIOLOGICAL_SOURCE"
        or ledger.get("original_Event_or_Occurrence_rows_opened")!=0
        or ledger.get("physical_islands")!=7
        or ledger.get("physical_sites")!=29
        or ledger.get("new_confirmatory_systems")!=0
        or not ledger.get("GEB_scientific_HOLD")):
        raise ValueError("Source original manuscript figure bundle is not evidence-locked")
    manifest={
        "schema":"structural.bala_jbi_anonymous_submission_package.v1_347",
        "status":"JBI_REVIEWER_SAFE_MARKDOWN_S1_THREE_FIGURES_SOURCEFREE",
        "blinded_main_manuscript_sha256":sha(doc),
        "blinded_uncertainty_S1_sha256":sha(s1),
        "JBI_structured_abstract_words":words,
        "original_figure_manifest_schema":ledger["schema"],
        "source_original_BALA_zip_sha256":ledger["original_archive_SHA256"],
        "figures_png_and_svg":ledger["figures"],
        "original_source_7_islands":7,
        "original_source_29_physical_transects":29,
        "reviewer_facing_original_biological_rows_reopened":0,
        "author_identifying_git_links_in_reviewer_text":0,
        "internal_author_contributions_and_biosketch_not_fabricated":True,
        "not_submitted":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }
    (dest/"JBI_blinded_package_manifest_v1_347.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manuscript",type=Path,default=MANUSCRIPT)
    p.add_argument("--S1",type=Path,default=S1)
    p.add_argument("--bundle",type=Path,required=True)
    a=p.parse_args()
    ledger=build(a.manuscript.read_text(encoding="utf-8"),
                 a.S1.read_text(encoding="utf-8"),a.bundle)
    print(json.dumps(ledger,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    main()
