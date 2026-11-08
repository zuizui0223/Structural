"""Known truth for original Brisbane 10-site edge1m / interior256m vertical beta."""
import importlib.util,json,math
from pathlib import Path
import pytest

p=Path(__file__).with_name("score_brisbane_matched_vertical_edge_beta.py")
spec=importlib.util.spec_from_file_location("brisbane_beta_source",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture(kind="amplified"):
    taxa=[f"Synthetic_beetle_group_{i}" for i in range(24)]
    hdr=["Obs","Abundance","Richness","Edge.dist","Height"]+taxa
    rows=[{i:v for i,v in enumerate(hdr)}]
    for site in range(1,11):
        for layer,edges in (("G",(1,4,16,64,256)),("C",(1,16,256))):
            for edge in edges:
                # All treatments preserve positive richness and matched effort;
                # only original site×edge strata differentiation changes.
                ca=[1]*12+[0]*12
                cb=[0]*12+[1]*12
                mix=[1]*24
                if kind=="amplified":
                    c=(cb if edge==1 else mix if edge==16 else ca)
                elif kind=="homogenized":
                    c=(ca if edge==1 else mix if edge==16 else cb)
                else:c=ca
                counts=ca if layer=="G" else c
                code=f"T{site}{layer}{edge}A"
                vals=[code,sum(counts),sum(n>0 for n in counts),
                      edge,"Ground" if layer=="G" else "Canopy"]+counts
                rows.append({i:str(v) for i,v in enumerate(vals)})
    assert len(rows)==81
    return rows

def test_expected_original_ten_study_sites_and_30_pairs_positive_edge_amplification():
    r=m.analyze_rows(fixture("amplified"),expect_species_246=False,boot_reps=500)
    assert r["source_trap_records"]==80
    assert r["source_original_10_sampling_sites_one_region"]==10
    assert r["source_full_30_site_by_edge_ground_canopy_pair_opportunities"]==30
    assert math.isclose(r["descriptive_vertical_brays_by_edge_m"]["1"]["mean_relative_abundance_BrayCurtis"],1,abs_tol=1e-12)
    assert r["descriptive_vertical_brays_by_edge_m"]["256"]["mean_relative_abundance_BrayCurtis"]==0
    assert abs(r["descriptive_vertical_brays_by_edge_m"]["16"]["mean_relative_abundance_BrayCurtis"]-.5)<1e-10
    result=r["within_source_site_primary_effect"]
    assert result["source_sites_used"]==10
    assert math.isclose(result["primary_edge1minus_interor256_relative_BrayCurtis_mean"],1,abs_tol=1e-12)
    assert all(math.isclose(x,1,abs_tol=1e-12) for x in result["site_bootstrap_95CI"])
    assert result["conditional_2sided_exact_site_signflip_p_NOT_independent_forest_replicates"]==2/(2**10)
    assert result["sites_edge_amplification_positive"]==10
    assert r["source_technical_quality_counts"]["source_abundance_metadata_differs_selected_taxa"]==0
    assert "Synthetic_beetle_group" not in json.dumps(r)
    assert "T1G1A" not in json.dumps(r)
    assert r["raw_original_morphospecies_names_Obs_siteIDs_NOT_exported"]

def test_original_same_design_can_produce_negative_or_no_edge_change():
    negative=m.analyze_rows(fixture("homogenized"),expect_species_246=False,boot_reps=300)
    main=negative["within_source_site_primary_effect"]
    assert math.isclose(main["primary_edge1minus_interor256_relative_BrayCurtis_mean"],-1,abs_tol=1e-12)
    assert main["sites_edge_homogenization_negative"]==10
    zero=m.analyze_rows(fixture("none"),expect_species_246=False,boot_reps=300)
    result=zero["within_source_site_primary_effect"]
    assert result["primary_edge1minus_interor256_relative_BrayCurtis_mean"]==0
    assert result["conditional_2sided_exact_site_signflip_p_NOT_independent_forest_replicates"]==1

def test_source_species_blank_not_automatically_biological_zero():
    rows=fixture()
    rows[1][5]=""
    with pytest.raises(ValueError,match="taxon_cell_blank_unknown_not_zero"):
        m.analyze_rows(rows,expect_species_246=False,boot_reps=50)

def test_source_edge_and_layer_must_match_original_obs_code():
    rows=fixture()
    rows[1][3]="4" # original T1G1A is edge 1
    with pytest.raises(ValueError,match="Obs_edge_conflicts"):
        m.analyze_rows(rows,expect_species_246=False,boot_reps=50)
    rows=fixture()
    rows[1][4]="Canopy"
    with pytest.raises(ValueError,match="Obs_layer_conflicts"):
        m.analyze_rows(rows,expect_species_246=False,boot_reps=50)


def test_secondary_16m_zero_capture_does_not_drop_primary_edge1_vs256_site():
    rows=fixture("amplified")
    # Simulate the one actual original zero-selected-taxa canopy trap at
    # middle distance: all 246 taxa had been filtered upstream (<2 traps).
    target=next(row for row in rows[1:] if row[0]=="T2C16A")
    for c in range(5,29):
        target[c]="0"
    target[1]="0"
    target[2]="0"
    r=m.analyze_rows(rows,expect_species_246=False,boot_reps=300)
    assert r["descriptive_vertical_brays_by_edge_m"]["16"]["valid_pairs"]==9
    assert r["descriptive_vertical_brays_by_edge_m"]["1"]["valid_pairs"]==10
    assert r["descriptive_vertical_brays_by_edge_m"]["256"]["valid_pairs"]==10
    assert r["within_source_site_primary_effect"]["source_sites_used"]==10
    assert r["within_source_site_primary_effect"]["sites_edge_amplification_positive"]==10
    assert r["site_specific_pair_diagnostics_NO_SOURCE_ID"][1]["complete_3dist_ground_canopy_site"] is False
