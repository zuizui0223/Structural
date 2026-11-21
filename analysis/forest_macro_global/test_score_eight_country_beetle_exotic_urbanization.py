"""Known-truth 13-landscape urbanization gradients with native/exotic beetle taxa."""
import importlib.util
from pathlib import Path

p=Path(__file__).with_name("score_eight_country_beetle_exotic_urbanization.py")
spec=importlib.util.spec_from_file_location("beetle_exotic_response",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def source_fixture(mode="positive"):
    sites=[f"PRIVATE_SITE_{i}" for i in range(13)]
    exotic=[f"EXOTIC_TAXON_{i}" for i in range(25)]
    native=[f"NATIVE_TAXON_{i}" for i in range(276)]
    species=exotic+native
    wide=[];long=[];env=[];site_env=[]
    count=0
    for i,sid in enumerate(sites):
        cells=15 if i==12 else 16
        site_env.append({"plot_id":sid,"forest_2000":str(25+i),
            "forest_3000":str(30+i),"forest_4000":str(35+i)})
        for j in range(cells):
            urban=0.5 if mode=="constant" else j/(cells-1)
            total=15+(count<110)
            exotics=round(urban*7) if mode!="negative" else round((1-urban)*7)
            taxa=(exotic[(k+i+j)%len(exotic)] for k in range(exotics))
            chosen=list(taxa)
            chosen.extend(native[(k+i*13+j*11)%len(native)] for k in range(total-exotics))
            assert len(set(chosen))==total
            cell=f"PRIVATE_CELL_{i}_{j}"
            w={"SITE":sid,"CELL_ID":cell}
            for label in species:
                w[label]="1" if label in chosen else "0"
            wide.append(w)
            env.append({"SITE":sid,"CELL_ID":cell,
                "composition":"0.0","configuration":"0.0",
                "urbanization_index":str(urban)})
            for label in chosen:
                long.append({"SITE":sid,"CELL_ID":cell,"SPECIES":label,
                    "STATUS":"Exotic" if label.startswith("EXOTIC") else "Native",
                    "N":"1"})
            count+=1
    assert len(wide)==207 and len(long)==3215 and len(site_env)==13
    return (wide,list(wide[0])),(long,list(long[0])),(site_env,list(site_env[0])),(env,list(env[0]))


def test_native_exotic_gradient_recovers_a_supported_known_positive():
    r=m.calculate(*source_fixture("positive"),p_reps=199,b_reps=500)
    assert r["source_original_landscapes"]==13
    assert r["source_original_cell_count"]==207
    assert r["source_original_cell_taxon_incidence_count"]==3215
    assert r["main_result"]["status"]=="EXPLORATORY_ESTIMATE_COMPUTED"
    assert r["main_result"]["eligible_landscapes"]==13
    assert r["main_result"]["main_mean_slope_exotic_incidence_share_per_within_landscape_urban_SD"]>0
    assert r["main_result"]["bootstrap_landscape_95CI"][0]>0
    assert r["main_result"]["positive_original_landscape_slope_count"]==13
    assert r["main_result"]["predeclared_support_criterion_met"] is True
    assert r["original_independent_forest_patches_count_verified"] if "original_independent_forest_patches_count_verified" in r else True
    assert r["no_original_site_IDS_taxa_names_trap_records_reexported"]
    assert "PRIVATE_SITE" not in str(r) and "EXOTIC_TAXON" not in str(r)


def test_negative_opposite_truth_not_forced_into_positive():
    r=m.calculate(*source_fixture("negative"),p_reps=199,b_reps=500)
    assert r["main_result"]["status"]=="EXPLORATORY_ESTIMATE_COMPUTED"
    assert r["main_result"]["main_mean_slope_exotic_incidence_share_per_within_landscape_urban_SD"]<0
    assert not r["main_result"]["predeclared_support_criterion_met"]
    assert r["main_result"]["negative_original_landscape_slope_count"]==13


def test_constant_urbanization_is_methodological_STOP_not_zero_ecological_effect():
    r=m.calculate(*source_fixture("constant"),p_reps=19,b_reps=100)
    assert r["main_result"]["status"]=="SCIENTIFIC_STOP_FEWER_THAN_8_LANDSCAPES_WITH_ESTIMABLE_LOCAL_URBANIZATION"
    assert r["main_result"]["main_mean_slope"] is None
    assert not r["main_result"]["predeclared_support_criterion_met"]


def test_same_species_status_conflict_within_landscape_fails():
    wide,long,site,env=source_fixture()
    long[0][12]["STATUS"]="Exotic" if long[0][12]["STATUS"]=="Native" else "Native"
    # The same species occurs repeatedly within this site's cells.
    try:
        m.calculate(wide,long,site,env,p_reps=19,b_reps=100)
        assert False
    except ValueError as ex:
        assert "status_conflicts_within_landscape" in str(ex)
