#!/usr/bin/env python3
"""Make a source-free, anonymity-audited reviewer code archive for BALA JBI.

No original archived Event/Occurrence values are fetched or embedded.
The optional original public-data pipeline is included as source CODE ONLY
and is never executed in the packaging workflow. The default reproducible
test suite uses frozen source-aggregate islands, n=7 (not site-pairs n=49/56).
"""
from __future__ import annotations
import argparse, hashlib, io, json, re, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANUSCRIPT_ARCHIVE_FILES=(
 "JBI_anonymized_main_text_v1_347.md",
 "JBI_anonymized_Supplementary_Table_S1_v1_347.md",
 "figure1_temporal_excess.png", "figure1_temporal_excess.svg",
 "figure2_spatial_beta_by_island.png", "figure2_spatial_beta_by_island.svg",
 "figure3_alpha_spatial_decoupling.png", "figure3_alpha_spatial_decoupling.svg",
 "sourcefree_island_figure_data.csv",
)
SOURCEFREE_SCRIPTS=(
 "bala_temporal_spatial_paper_sourcefree_v1_344.py",
 "bala_jbi_sourcefree_figures_v1_345.py",
 "bala_jbi_island_unit_uncertainty_sourcefree_v1_346.py",
)
OPTIONAL_SOURCE_PIPELINE_SCRIPTS=(
 "bala_original_metadata_only_v1_310.py",
 "bala_repeated_transect_event_only_v1_311.py",
 "bala_published_island_code_event_v1_312.py",
 "bala_equal_original_event_samples_v1_313.py",
 "bala_original_species_replacement_v1_314.py",
 "bala_within_campaign_detection_control_v1_316.py",
 "bala_original_island_spatial_beta_v1_318.py",
)
TESTS=(
 "test_bala_temporal_spatial_paper_sourcefree_v1_344.py",
 "test_bala_jbi_island_unit_uncertainty_sourcefree_v1_346.py",
)
SOURCEFREE_AGGREGATES=(
 "bala_within_campaign_detection_original_result_freeze_v1_316.json",
 "bala_spatial_original_result_freeze_v1_318.json",
 "bala_temporal_spatial_cross_axis_sourcefree_protocol_v1_344.json",
 "bala_jbi_island_unit_uncertainty_protocol_v1_346.json",
)
ORIGINAL_SOURCE_CONTRACTS=(
 "bala_longitudinal_original_source_protocol_v1_310.json",
 "bala_original_event_repeat_gate_v1_311.json",
 "bala_published_island_code_event_protocol_v1_312.json",
 "bala_equal_sampling_opportunity_contract_v1_313.json",
 "bala_equal_event_source_original_receipt_v1_313.json",
 "bala_three_decade_species_replacement_protocol_v1_314.json",
 "bala_seven_island_species_replacement_original_result_v1_314.json",
 "bala_within_campaign_detection_control_protocol_v1_316.json",
 "bala_within_campaign_detection_original_result_freeze_v1_316.json",
 "bala_spatial_homogenization_pre_response_protocol_v1_318.json",
 "bala_spatial_original_result_freeze_v1_318.json",
)
PUBLIC_SOURCE_SHA="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
DATA_DOI="10.15468/rpdkx9"
DIRECT_AUTHOR_IDENTIFIERS=("zuizui0223","github.com/","githubusercontent.com","@gmail.com","@tohoku.ac.jp","Rachel")
# Copy source CODE, not cached source data. IDs from developer CI are
# non-scientific and link back to a named repository: remove them only in
# these reviewer-specific numeric copies. Scientific source SHA-256 and frozen
# sampling cohort/dataset IDs are preserved.
PROVENANCE_FIELDS=(
 "original_first_v314_biological_run", "v316_original_biological_run",
 "v316_artifact_id", "original_run_id", "original_artifact_id",
 "source_v316_artifact_id", "source_v318_artifact_id",
)

def pack_code(relative):
    raw=(ROOT/relative).read_text(encoding="utf-8")
    # This changes only the creator-identifying User-Agent/legacy project
    # string and documentation, not scientific numeric algorithms.
    anonymized=raw.replace("Structural","AnonymousIslandAnalysis")
    verify_anonymous(anonymized,relative)
    compile(anonymized,relative,"exec")
    return anonymized.encode("utf-8")

def strip_only_developer_run_provenance(obj):
    if isinstance(obj,dict):
        return {k:strip_only_developer_run_provenance(v)
                for k,v in obj.items() if k not in PROVENANCE_FIELDS}
    if isinstance(obj,list):return [strip_only_developer_run_provenance(v) for v in obj]
    return obj

def pack_json(relative):
    data=json.loads((ROOT/relative).read_text(encoding="utf-8"))
    data=strip_only_developer_run_provenance(data)
    raw=json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    raw=raw.replace("Structural","AnonymousIslandAnalysis")
    verify_anonymous(raw,relative)
    return raw.encode("utf-8")

def verify_anonymous(text,relative):
    for ident in DIRECT_AUTHOR_IDENTIFIERS:
        if ident.lower() in text.lower():
            raise ValueError(f"Anonymous reviewer material leaks creator identity in {relative}: {ident}")
    if "Structural" in text:
        raise ValueError(f"Identity-bearing project name in {relative}")

def make_readme():
    return f"""# Island forest arthropod biodiversity: anonymous reviewer code

**Research code accompanying a draft; not a submitted or published paper.**
The original biological data belong to their publishers and are NOT
included. Original archival source: University of the Azores BALA,
GBIF DOI https://doi.org/{DATA_DOI} (cite the publisher's authors and
the published 2024 data descriptor). Public source ZIP SHA256:
\`{PUBLIC_SOURCE_SHA}\`.

## A. Immediate offline replication (recommended; no biological download)

Requirements: Python 3.11 or later; install \`python -m pip install -r requirements.txt\`
(or use already available Matplotlib and pytest). From this archive root:

\`\`\`sh
python -m pytest -q tests/test_bala_temporal_spatial_paper_sourcefree_v1_344.py tests/test_bala_jbi_island_unit_uncertainty_sourcefree_v1_346.py
python scripts/bala_temporal_spatial_paper_sourcefree_v1_344.py --out output/bala_beta_audit.json
python scripts/bala_jbi_island_unit_uncertainty_sourcefree_v1_346.py --out output/7_island_uncertainty.json
python scripts/bala_jbi_sourcefree_figures_v1_345.py --out output/figures
\`\`\`

The \`development/\` directory contains only compact, source-frozen
*aggregate numerical evidence* and source-only protocols; neither original
10,379 Event nor 63,904 Occurrence rows or any source-specific species names
are in this archive. All results are from original survey detections, NOT
demographic immigrations or extinctions. The figure CSV has 14
island×guild summary rows, not 49/56 independent plot pairs.

Expected results:
- Within-campaign half-sample corrected *descriptive excess* of
  source-detected B1–B3 temporal Sørensen: +0.1908 Spiders and +0.2212
  Beetles, across all seven island means.
- Within-island B3−B1 spatial Simpson β seven-island means: +0.0224
  Spiders; −0.1753 Beetles.
- Beetle spatial 95% seven-island descriptive t interval
  [−0.4399,+0.0893] crosses zero, exploratory two-sided island sign flip
  p=0.1875 from 128 signed relabelings. NO universal island-wide or
  statistically established guild-specific spatial direction is claimed.
- At Flores, São Jorge and Santa Maria, original Beetle richness
  increased despite sampled among-plot community convergence.

## B. OPTIONAL original-data source pipeline (NOT part of default tests)

\`scripts/bala_original_*.py\`,
\`scripts/bala_repeated_transect_event_only_v1_311.py\`,
\`scripts/bala_published_island_code_event_v1_312.py\`,
\`scripts/bala_equal_original_event_samples_v1_313.py\` and
\`scripts/bala_within_campaign_detection_control_v1_316.py\`
are supplied for inspection of the complete source-to-summary method.
Their published-source downloading functions are **not called by archive
creation, default tests or figure replication**.

The source-original cohort construction and parameter files are retained
verbatim except for creator-identifying string-only metadata; developer
CI run/artifact IDs were removed from reviewer copies but publication
DOIs, source ZIP SHA, original source-event sampling SHA and every
numeric ecological result are retained. To fully replay the public
source-processing pipeline, a reviewer must explicitly invoke the
original-data scripts and obtain the authors' public source archive;
the scripts verify the original ZIP SHA before biological interpretation.
The original research project did not rerun the exploratory one-shot
biological outcome scorers after recording results. Re-running from
published data independently is a reviewer choice, **not** a new
confirmatory validation system.

## Methodological ceilings

Seven source islands belong to ONE archipelago. Individual physical
transects, trap Events, 49/56 dependent plot pairs, and 18 repeated
source-only half-sample splits must not be treated as independent island
replicates. The seven-island Student-t interval assumes independent
island contexts and the 128 sign-flip tail assumes a symmetric null;
both are exploratory post hoc diagnostics. Guild source plot frames
differ (28 Beetle vs 29 Spider physical plots). Climate, habitat changes,
survey timing, taxonomic reidentification and detection heterogeneity
could contribute. The source 2026 field paper's reported stability in
overall aggregate abundance/richness and significant ground-dwelling
richness decline are prior art, not new discoveries here.

## Files and accountability

- \`scripts/\`: original public-source processing CODE and source-free
  numerical/figure verification CODE.
- \`tests/\`: source-free numerical tests; never fetches biological rows.
- \`development/\`: original field source-free numeric summaries and
  their frozen methods.
- \`figures/\`: 3 original aggregate-based paper figures (PNG and SVG)
  and the 14-row original island×guild plotting CSV.
- \`manuscript/\`: blinded reviewer main Markdown and uncertainty S1.
- \`MANIFEST_SHA256.json\`: per-file SHA checksums and scientific gates.

The original authors/custodians should be consulted about contribution
and data-use expectations. This code archive is **anonymous for reviewer
circulation only** and should be deposited under actual contributor names
after peer review; no external archive DOI or author approval is claimed.
"""
def build(original_v1347_archive,output):
    src=Path(original_v1347_archive)
    output=Path(output)
    content={}
    for s in (*SOURCEFREE_SCRIPTS,*OPTIONAL_SOURCE_PIPELINE_SCRIPTS):
        content["scripts/"+s]=pack_code("scripts/"+s)
    for test in TESTS:
        content["tests/"+test]=pack_code("tests/"+test)
    for name in set((*SOURCEFREE_AGGREGATES,*ORIGINAL_SOURCE_CONTRACTS)):
        content["development/"+name]=pack_json("development/"+name)

    with zipfile.ZipFile(src) as archive:
        original_set=set(archive.namelist())
        for name in MANUSCRIPT_ARCHIVE_FILES:
            found=[k for k in original_set if k.split("/")[-1]==name]
            if len(found)!=1:
                raise ValueError(f"Missing or ambiguous validated v1.347 source-free artifact: {name}")
            data=archive.read(found[0])
            if name.endswith(".md"):
                verify_anonymous(data.decode("utf-8"),name)
            content[("figures/" if name.startswith("figure") or name.endswith(".csv")
                else "manuscript/")+name]=data
        original_manifest=[k for k in original_set if k.endswith("figure_bundle_manifest.json")]
        if len(original_manifest)!=1:raise ValueError("Missing original source-free figure SHA manifest")
        m=json.loads(archive.read(original_manifest[0]))
        if (m.get("original_archive_SHA256")!=PUBLIC_SOURCE_SHA
            or m.get("original_Event_or_Occurrence_rows_opened")!=0
            or m.get("physical_islands")!=7 or m.get("physical_sites")!=29
            or m.get("GEB_scientific_HOLD") is not True):
            raise ValueError("Reviewer figures are not tied to frozen BALA original data")
    content["README.md"]=make_readme().encode("utf-8")
    content["requirements.txt"]=b"matplotlib>=3.7,<4\npytest>=7,<10\n"
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in sorted(content.items())}
    manifest={
      "schema":"anonymous.island_arthropod_reviewer_reproducibility.v1_349",
      "status":"BLINDED_SOURCE_FREE_SEVEN_ISLAND_FIGURES_AND_PUBLIC_SOURCE_CODE_AVAILABLE",
      "original_published_BALA_DwCA_SHA256":PUBLIC_SOURCE_SHA,
      "original_BALA_field_Event_rows_contained":0,
      "original_BALA_field_Occurrence_rows_contained":0,
      "embedded_source_figure_count":3,
      "sourcefree_original_island_guild_plotting_rows":14,
      "source_original_biology_reopened_during_build":0,
      "sourcefree_reproduction_default_without_network":True,
      "original_source_replay_scripts_are_present_but_not_executed":True,
      "original_islands_n":7,
      "original_site_frame_n":29,
      "observed_beetle_spatial_Simpson_mean":-0.17530148423005568,
      "observed_beetle_island_level_t95_includes_zero":True,
      "archive_is_not_original_field_data_or_an_independent_confirmation":True,
      "archive_direct_identifying_repository_urls":0,
      "file_sha256":hashes,
      "file_n":len(hashes)+1,
    }
    content["MANIFEST_SHA256.json"]=(json.dumps(manifest,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
    if any(k.endswith((".parquet",".gpkg",".feather",".xlsx",".sqlite",".db")) for k in content):
        raise ValueError("No original biological source database or raw field table permitted")
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for filename,data in sorted(content.items()):
            archive.writestr(filename,data)
    with zipfile.ZipFile(output) as archive:
        if sorted(archive.namelist())!=sorted(content):
            raise AssertionError("Reviewer archive file inventory does not match SHA manifest")
        for filename in content:
            if hashlib.sha256(archive.read(filename)).hexdigest()!=hashlib.sha256(content[filename]).hexdigest():
                raise AssertionError("Reviewer source file SHA mismatch: "+filename)
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sourcefree-v1347",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(build(args.sourcefree_v1347,args.out),sort_keys=True))
