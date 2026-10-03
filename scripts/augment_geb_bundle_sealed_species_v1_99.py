#!/usr/bin/env python3
"""Augment the neutralized GEB review bundle with the sealed 96-species validation."""
from __future__ import annotations
import argparse,ast,json,re,shutil,hashlib
from pathlib import Path

import scripts.build_geb_anonymous_review_bundle_v1_91 as base

SECOND_MAGIC_STRINGS={
    "STRUCTURAL_MAMMAL_SECOND_LAYER_PRED_V1":"REVIEW_MAMMAL_SECOND_LAYER_PRED_V1",
    "STRUCTURAL_MAMMAL_SECOND_LAYER_GRAPH_EMPTY_V1":"REVIEW_MAMMAL_SECOND_LAYER_GRAPH_EMPTY_V1",
}

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def neutralize_source(src:Path,dst:Path):
    text=src.read_text(encoding="utf-8")
    for old,new in SECOND_MAGIC_STRINGS.items():
        text=text.replace(old,new)
    tree=ast.parse(text)
    tree=base.NeutralizePython(None,None).visit(tree)
    ast.fix_missing_locations(tree)
    out="# Review-only neutralized source snapshot\n"+ast.unparse(tree)+"\n"
    out=re.sub(r"from scripts\\.[A-Za-z0-9_]+ import", "from review_dependencies import", out)
    out=re.sub(r"import scripts\\.[A-Za-z0-9_]+", "import review_dependencies", out)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(out,encoding="utf-8")

def copy_json(src:Path,dst:Path):
    base.copy_sanitized_json(src,dst,None,None)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--source-root",type=Path,required=True)
    ap.add_argument("--bundle-root",type=Path,required=True)
    a=ap.parse_args()
    repo=a.repo_root.resolve();src=a.source_root.resolve();out=a.bundle_root.resolve()

    mappings={
      "development/global_mammals_sealed_species_pilot_contract_v1_93.json":"sealed/contracts/pilot_selection.json",
      "development/global_mammals_sealed_species_replication_contract_v1_94.json":"sealed/contracts/replication_predictions.json",
      "development/global_mammals_sealed_species_scoring_contract_v1_95.json":"sealed/contracts/scoring.json",
      "development/global_mammals_sealed_species_result_freeze_v1_97.json":"sealed/results/result_freeze.json",
    }
    for rel,dst in mappings.items():copy_json(repo/rel,out/dst)

    scripts={
      "scripts/freeze_global_mammals_sealed_species_pilot_v1_93.py":"sealed/analysis/pilot_selection.py",
      "scripts/freeze_global_mammals_sealed_species_predictions_v1_94.py":"sealed/analysis/preconfirm_predictions.py",
      "scripts/run_global_mammals_sealed_species_response_v1_95.py":"sealed/analysis/heldout_router.py",
      "scripts/score_global_mammals_sealed_species_v1_95.py":"sealed/analysis/score_predictions.py",
      "scripts/build_sealed_species_figure_v1_97.py":"sealed/analysis/figure4.py",
    }
    for rel,dst in scripts.items():neutralize_source(repo/rel,out/dst)

    copies={
      "sealed_pilot/second_layer_species_universe.csv":"sealed/inputs/species_universe.csv",
      "sealed_pilot/second_layer_pilot_matrix.csv":"sealed/inputs/pilot_matrix.csv",
      "sealed_preconfirm/preconfirm_receipt.json":"sealed/results/preconfirm_receipt.json",
      "sealed_preconfirm/actual_graph_empty_mask.u8":"sealed/outputs/actual_graph_empty_mask.u8",
      "sealed_result/second_layer_heldout_matrix.csv":"sealed/outputs/heldout_matrix.csv",
      "sealed_result/second_layer_block_scores.csv":"sealed/outputs/block_scores.csv",
      "sealed_result/second_layer_null_scores.csv":"sealed/outputs/null_scores.csv",
      "sealed_result/second_layer_response_receipt.json":"sealed/results/response_receipt.json",
      "sealed_result/second_layer_result.json":"sealed/results/scoring_result.json",
      "sealed_figure/fig4_sealed_species_validation.png":"figures/Figure_4.png",
      "sealed_figure/fig4_sealed_species_validation.svg":"figures/Figure_4.svg",
    }
    for rel,dst in copies.items():
        sp=src/rel;dp=out/dst;dp.parent.mkdir(parents=True,exist_ok=True)
        if sp.suffix==".json":copy_json(sp,dp)
        else:shutil.copy2(sp,dp)

    caption=(repo/"manuscript/submission/GEB_v1_97/figure4_caption.md").read_text(encoding="utf-8")
    caption=base.clean_string(caption)
    with (out/"FIGURE_CAPTIONS.md").open("a",encoding="utf-8") as h:
        h.write("\n\n"+caption.strip()+"\n")

    with (out/"README.md").open("a",encoding="utf-8") as h:
        h.write("""
## Prospective sealed rare-species validation

A second, disjoint mammal species layer was defined from pilot data only (5–12 pilot presences). Its 96-species held-out response had not been decoded during the original 79-species analysis.

Before held-out access, R3, actual-graph C and 20 degree- and edge-length-matched rewired-graph prediction surfaces were frozen. The 396,096 held-out targets were then decoded once and scored immediately.

The preregistered primary did not replicate the original overall gain. The rare layer also reversed the original presence/absence asymmetry and showed no advantage of the actual graph over matched rewired topologies. Files under 'sealed/' contain the pilot surface, contracts, frozen receipts, held-out focal matrix, block/null scores and neutralized implementation snapshots.

The large 20-null probability binary is intentionally omitted from the peer-review ZIP to keep Supporting Information compact; its exact response-free generation algorithm, seeds, graph fingerprints and final score outputs are preserved in the included contracts and receipts.
""")

    prov=json.loads((out/"ANONYMIZED_PROVENANCE.json").read_text())
    prov["sealed_species_validation"]={
      "species":96,"pilot_presence_range":[5,12],"heldout_islands":4126,
      "heldout_target_cells":396096,"primary_supported":False,
      "actual_topology_better_than_nulls":"11/20",
      "geographically_independent_replication":False,
    }
    (out/"ANONYMIZED_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")

    sums=out/"SHA256SUMS.txt"
    if sums.exists():sums.unlink()
    files=sorted(p for p in out.rglob("*") if p.is_file() and p.name!="SHA256SUMS.txt")
    with sums.open("w",encoding="utf-8") as h:
        for p in files:h.write(f"{sha(p)}  {p.relative_to(out).as_posix()}\n")

    forbidden=["github.com","zuizui0223","workflow_run_id","workflow_head_sha","workflow_job_id",
               "artifact_id","artifact_name",".github/workflows","structural.","global_mammals_",
               "global_island_native_mammals_barreto_2024"]
    commit=re.compile(r"\\b[0-9a-fA-F]{40}\\b");hits=[]
    for p in out.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md",".txt",".json",".py",".csv",".svg"}:continue
        try:t=p.read_text(encoding="utf-8")
        except UnicodeDecodeError:continue
        low=t.casefold()
        for f in forbidden:
            if f.casefold() in low:hits.append((str(p.relative_to(out)),f))
        if commit.search(t):hits.append((str(p.relative_to(out)),"40-hex-token"))
    if hits:raise SystemExit(f"sealed bundle anonymity failure: {hits[:30]}")

    print(json.dumps({
      "schema":"review.anonymous_bundle_sealed_species_augmentation",
      "status":"SEALED_SPECIES_VALIDATION_ADDED_ANONYMOUSLY",
      "sealed_species":96,
      "heldout_target_cells":396096,
      "raw_biological_response_included":False,
      "public_repository_identifiers_included":False
    },indent=2,sort_keys=True))

if __name__=="__main__":main()
