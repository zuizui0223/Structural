"""BALA v1.345 publication-format manuscript and source-free figure regression."""
from pathlib import Path
import copy,csv,json,re,sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_jbi_sourcefree_figures_v1_345 import render,make_ledger
from bala_temporal_spatial_paper_sourcefree_v1_344 import analyze

DRAFT=ROOT/"docs/BALA_JBI_ANONYMIZED_FULL_MANUSCRIPT_DRAFT_V1_345.md"

def sources():
    def get(path):
        return json.loads((ROOT/"development"/path).read_text(encoding="utf-8"))
    return (
      get("bala_within_campaign_detection_original_result_freeze_v1_316.json"),
      get("bala_spatial_original_result_freeze_v1_318.json"),
      get("bala_temporal_spatial_cross_axis_sourcefree_protocol_v1_344.json"),
    )

def test_manuscript_meets_current_journal_structured_abstract_and_title_limits():
    m=DRAFT.read_text(encoding="utf-8")
    first=m.splitlines()[0]
    assert first.startswith("# ")
    assert len(first[2:])<=115
    running=re.search(r"\*\*Running title:\*\*\s*(.*)",m)
    assert running and len(running.group(1))<40
    ab=m.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    for heading in ("Aim","Location","Taxon","Methods","Results","Main conclusions"):
        assert "**"+heading+":**" in ab
    count=len(ab.replace("**","").split())
    assert 130<=count<=300, count
    for heading in ("1 | Introduction","2 | Materials and Methods",
                    "3 | Results","4 | Discussion","5 | Conclusions",
                    "Data availability and reproducibility","Figure legends","References"):
        assert heading in m
    assert "source-sink" in m.lower() or "source–sink" in m.lower()
    assert "not directly observed" in m.lower() or "not directly measured" in m.lower()

def test_paper_claims_are_validated_only_by_original_source_free_numeric_rows():
    v316,v318,p=sources()
    r=analyze(v316,v318,p)
    audit,records=make_ledger(v316,v318,p)
    assert audit==r
    assert len(records)==14
    assert sum(x["physical_plots_spatial"] for x in records if x["guild"]=="araneae")==29
    assert sum(x["physical_plots_spatial"] for x in records if x["guild"]=="coleoptera")==28
    beetles={v["island_code"]:v for v in records if v["guild"]=="coleoptera"}
    spiders={v["island_code"]:v for v in records if v["guild"]=="araneae"}
    assert {i for i,x in beetles.items() if x["spatial_simpson_delta_B3_minus_B1"]<0}=={"flo","sjg","smr","ter"}
    assert {i for i,x in beetles.items()
            if x["spatial_simpson_delta_B3_minus_B1"]<0 and
               x["mean_local_richness_delta_B3_minus_B1"]>0}=={"flo","sjg","smr"}
    assert sum(x["spatial_simpson_delta_B3_minus_B1"]<0 for x in spiders.values())==3
    assert r["source_pitfall_guilds"]["coleoptera"]["source_one_island_delete_negative_count"]==7
    assert r["source_pitfall_guilds"]["araneae"]["source_one_island_delete_negative_count"]==2

def test_figure_bundle_contains_only_14_island_guild_aggregate_rows(tmp_path):
    v316,v318,p=sources()
    manifest=render(v316,v318,p,tmp_path)
    assert manifest["status"]=="ORIGINAL_BALA_NUMERICAL_FIGURES_GENERATED_WITHOUT_BIOLOGICAL_SOURCE"
    assert manifest["original_Event_or_Occurrence_rows_opened"]==0
    assert manifest["physical_sites"]==29 and manifest["physical_islands"]==7
    assert manifest["original_archive_SHA256"]=="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
    assert manifest["beetle_one_island_delete_negative_n"]==7
    assert manifest["GEB_scientific_HOLD"] and manifest["new_confirmatory_systems"]==0
    assert not manifest["eBird_used"]
    for name in manifest["figures"]:
        assert (tmp_path/(name+".png")).stat().st_size>15_000
        assert (tmp_path/(name+".svg")).stat().st_size>5_000
    with (tmp_path/"sourcefree_island_figure_data.csv").open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==14
    assert all(r["island_name"] and r["physical_plots_spatial"] for r in rows)
    assert not any("scientificName" in k or "source_coreid" in k or "locationID" in k
                   for k in rows[0])

def test_source_archive_drift_and_false_independence_never_silently_pass():
    v316,v318,p=sources()
    changed=copy.deepcopy(v318)
    changed["original_evidence"]["original_result_JSON_SHA256"]="tampered"
    with pytest.raises(ValueError,match="source field data identity"):
        make_ledger(v316,changed,p)
    changed=copy.deepcopy(v318)
    changed["main_pitfall"]["coleoptera"]["per_island"]["flo"]["dependent_pairs"]+=1
    with pytest.raises(ValueError,match="site and dependent-pair"):
        make_ledger(v316,changed,p)

def test_prior_work_artifact_and_scientific_seals_always_present():
    m=DRAFT.read_text(encoding="utf-8")
    for doi in ("10.15468/rpdkx9",
                "10.1038/s41598-026-57146-5",
                "10.1038/s41597-024-03174-7",
                "10.1111/j.1466-822X.2006.00214.x",
                "10.1111/j.1466-8238.2009.00490.x"):
        assert doi in m
    for guard in ("once", "not independent", "not submitted"):
        assert guard in m.lower()
    assert "v1.314" in m and "v1.316" in m and "v1.318" in m
