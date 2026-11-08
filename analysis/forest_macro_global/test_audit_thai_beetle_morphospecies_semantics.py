"""Original morphospecies token semantics: known truth and no species inflation."""
import importlib.util
import json
from pathlib import Path

script=Path(__file__).with_name("audit_thai_beetle_morphospecies_semantics.py")
spec=importlib.util.spec_from_file_location("thai_morpho",script)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_code_vs_sp_unspecified_and_binomial():
    assert m.identify_class("Genus sp. 1","genus")=="explicit_morphospecies_code"
    assert m.identify_class("Genus spB2","genus")=="explicit_morphospecies_code"
    assert m.identify_class("Genus morphospecies 17","genus")=="explicit_morphospecies_code"
    assert m.identify_class("Genus alpha","species")=="binomial_label_no_morphocode"
    assert m.identify_class("Genus sp.","genus")=="generic_sp_without_unique_code"
    assert m.identify_class("Curculionidae","family")=="higher_rank_or_genus_label_no_explicit_species_key"
    assert m.identify_class("Genus","genus")=="higher_rank_or_genus_label_no_explicit_species_key"
    assert m.identify_class("","genus")=="empty_source_scientificName"


def make_source():
    ev=[{"_core_id":f"private_Event_{j}"} for j in range(288)]
    labels=[("Genus sp. 1","genus"),("Genus sp.","genus"),
            ("Staphylinidae","family"),("Genus alpha","species")]
    occ=[]
    for i in range(1073):
        name,rank=labels[i%4]
        count=2 if i<549 else 1
        occ.append({"_core_id":ev[i%288]["_core_id"],"scientificName":name,
                    "taxonRank":rank,"individualCount":str(count)})
    assert sum(int(r["individualCount"]) for r in occ)==1622
    return ev,occ


def test_1073_occurrence_1622_beetles_do_not_become_437_species():
    ev,occ=make_source()
    r=m.inspect(ev,occ)
    assert r["publisher_event_rows"]==288
    assert r["publisher_occurrence_rows"]==1073
    assert r["source_original_beetle_individuals"]==1622
    assert r["published_species_and_morphospecies_count_REFERENCE_ONLY"]==437
    assert r["source_unique_verbatim_scientificName_total_NOT_species_richness"]==4
    assert r["source_species_identity_admission_not_proven"]
    assert r["has_any_unresolved_identification_labels"]
    assert "Genus alpha" not in json.dumps(r)
    assert "private_Event" not in json.dumps(r)
    assert r["raw_taxon_labels_coreIDs_and_locations_not_exported"]


def test_original_count_and_event_join_fail_closed():
    ev,occ=make_source()
    occ[0]["_core_id"]="unknown_original_event"
    try:
        m.inspect(ev,occ)
        assert False
    except ValueError as e:
        assert "dangling" in str(e)
    ev,occ=make_source()
    occ.pop()
    try:
        m.inspect(ev,occ)
        assert False
    except ValueError as e:
        assert "1073" in str(e)
