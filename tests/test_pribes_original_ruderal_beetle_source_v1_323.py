"""PRIBES original taxon response scorer: all source-free known truth fixtures."""
import copy,itertools,json,math,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from pribes_original_ruderal_beetle_source_v1_323 import (
    ranks,spearman,exact_island_permutation,island_site_similarity,
    score_original,source_frame
)
from pribes_original_onehour_sites_v1_322 import original_onehour_cohort
from test_pribes_original_onehour_sites_v1_322 import example

ORDER=("FAI","FLO","PIC","TER","SMG","SMR")

def settings():
    def file(name):
        return json.loads((ROOT/"development"/name).read_text(encoding="utf-8"))
    return (
       file("pribes_ruderal_beetle_source_forest_beta_protocol_v1_323.json"),
       file("pribes_equal_onehour_original_event_protocol_v1_322.json"),
       file("pribes_original_event_site_contract_v1_321.json"),
       file("pribes_equal_onehour_site_receipt_freeze_v1_322.json")
    )

def fake_source():
    events=example()
    main,onehour,older,receipt=settings()
    previous=original_onehour_cohort(events,onehour,older)
    assert previous["status"]=="NEW_SEPARATE_72_RUDERAL_SITES_ONEHOUR_EACH_TAXON_RESPONSES_SEALED"
    receipt["source_onehour_selected_original_Event_coreids_sha256"]=previous["source_onehour_selected_original_Event_coreids_sha256"]
    receipt["source_fullhour_sites_by_island"]=previous["onehour_source_physical_sites_by_BALA_overlap_island"]
    chosen,frame=source_frame(events,onehour,older,receipt)
    names={}
    for core,(isl,site) in chosen.items():
        names.setdefault(isl,[]).append((core,site))
    occ=[]
    for island in ORDER:
        for index,(core,site) in enumerate(sorted(names[island])):
            diversity_idx=ORDER.index(island)
            modulo=diversity_idx+2
            for name,status,order in (
                ("Coleoptera introduced shared","Introduced","Coleoptera"),
                (f"Coleoptera island{diversity_idx} group{index%modulo}","exotic","Coleoptera"),
                ("Coleoptera native shared","native","Coleoptera"),
                (f"Coleoptera native class{index%2}","endemic","Coleoptera"),
                ("Spider introduced shared","introduced","Araneae"),
                (f"Spider introduced class{index%modulo}","introduced","Araneae")
            ):
                occ.append({"__original_event_coreid":core,"scientificName":name,
                    "taxonRank":"species","order":order,"establishmentMeans":status})
    pad=next(e["original_coreid"] for e in events if e["island"]=="Corvo")
    occ.extend([{"__original_event_coreid":pad,"scientificName":"Unscored Corvo species",
       "taxonRank":"species","order":"Coleoptera","establishmentMeans":"introduced"}
       for _ in range(2836-len(occ))])
    assert len(occ)==2836
    return events,occ,main,onehour,older,receipt

def test_six_island_exact_permutation_ranks_and_status_filter():
    events,occ,main,onehour,older,receipt=fake_source()
    r=score_original(events,occ,main,onehour,older,receipt)
    assert r["status"]=="SOURCE_OBSERVED_SIX_ISLAND_ASSOCIATION_SCORED_NOT_CAUSAL"
    assert r["source_onehour_physical_sites"]==72
    assert r["source_original_Event_rows_opened"]==80
    assert r["source_original_Occurrence_rows_opened_once"]==2836
    assert r["source_original_Event_Occurrence_join_fraction"]==1.0
    assert r["source_unclassified_rank_named_origin_fraction"]==0
    assert r["original_conflicting_island_taxon_status_count"]==0
    assert set(r["per_island"])==set(ORDER)
    for i in ORDER:
        assert r["per_island"][i]["introduced_beetle_source"]["source_site_similarity_admissible"]
        assert r["per_island"][i]["introduced_beetle_source"]["distinct_recognized_taxa"]>=2
    p=r["primary_introduced_beetle_source_similarity_vs_forest_homogenization"]
    assert p is not None
    assert p["exact_island_label_permutations"]==720
    assert -1.<=p["spearman_rho"]<=1.
    assert 0<p["one_sided_positive_association_permutation_p"]<=1
    assert r["negative_control_native_endemic_beetle_source_similarity_vs_forest_homogenization"] is not None
    assert r["original_BALA_source_Event_and_Occurrence_rows_REOPENED"]==0
    assert r["source_original_full_80_Event_effort_gate_v1_321_TERMINAL"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "Coleoptera introduced shared" not in json.dumps(r)
    assert "SITE_FAI" not in json.dumps(r)

def test_missing_one_island_source_beetles_stops_not_broadens_to_arthropods():
    events,occ,main,onehour,older,receipt=fake_source()
    cores=set()
    selected,_=source_frame(events,onehour,older,receipt)
    for core,(island,_) in selected.items():
        if island=="FLO":cores.add(core)
    for row in occ:
        if row["__original_event_coreid"] in cores and row["order"]=="Coleoptera":
            row["establishmentMeans"]="native"
    r=score_original(events,occ,main,onehour,older,receipt)
    assert r["status"]=="STOP_ORIGINAL_INTRO_BEETLE_SOURCE_SUPPORT_OR_ORIGIN"
    assert r["stop_reason"]=="At least one source island lacks 4 nonempty introduced Beetle sites / 2 taxa"
    assert r["primary_introduced_beetle_source_similarity_vs_forest_homogenization"] is None
    assert r["source_onehour_physical_sites"]==72

def test_unclassified_status_fraction_is_scientific_STOP():
    events,occ,main,onehour,older,receipt=fake_source()
    selected,_=source_frame(events,onehour,older,receipt)
    k=0
    for row in occ:
        if row["__original_event_coreid"] in selected:
            if k%2==0:row["establishmentMeans"]="indeterminate"
            k+=1
    r=score_original(events,occ,main,onehour,older,receipt)
    assert r["status"]=="STOP_ORIGINAL_INTRO_BEETLE_SOURCE_SUPPORT_OR_ORIGIN"
    assert "ontology" in r["stop_reason"]
    assert r["primary_introduced_beetle_source_similarity_vs_forest_homogenization"] is None

def test_spearman_ranks_and_full_720_label_null_with_ties():
    assert ranks([9,1,1,7])==[4.0,1.5,1.5,3.0]
    a=exact_island_permutation([0,1,2,3,4,5],[0,1,2,3,4,5])
    assert math.isclose(a["spearman_rho"],1,abs_tol=1e-12)
    assert a["exact_island_label_permutations"]==720
    assert math.isclose(a["one_sided_positive_association_permutation_p"],1/720)
    assert spearman([1]*6,[1,2,3,4,5,6]) is None
    assert island_site_similarity({"a":{"A"},"b":{"A"},"c":{"B"},"d":{"B"}},
          {"a","b","c","d"})["source_site_similarity_admissible"]
    assert not island_site_similarity({"a":{"A"},"b":set(),"c":set(),"d":set()},
          {"a","b","c","d"})["source_site_similarity_admissible"]
