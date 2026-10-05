from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_145"

def test_bala_freeze_is_exact_and_non_supportive():
    x=json.loads((ROOT/"development/bala_source_loss_result_freeze_v1_144.json").read_text())
    assert x["population"]["eligible_taxa"]==20
    assert x["population"]["target_rows"]==64
    assert x["population"]["t2_contractions"]==20
    assert x["population"]["t2_persistences"]==44
    assert x["primary"]["point_C_minus_R2"]==0.00067423414692237
    assert x["primary"]["bootstrap_ci95_low"]==-0.02130441194511585
    assert x["primary"]["bootstrap_ci95_high"]==0.025579070508640226
    assert x["primary"]["primary_supported"] is False
    assert x["response_firewall"]["rerun_authorized"] is False

def test_bala_secondary_summaries_cannot_rescue_primary():
    x=json.loads((ROOT/"development/bala_source_loss_result_freeze_v1_144.json").read_text())
    assert x["secondary_nonrescuing"]["mean_E_i_contraction"]==0.4659640925585486
    assert x["secondary_nonrescuing"]["mean_E_i_persistence"]==0.28745616955060244
    assert x["secondary_nonrescuing"]["full_data_standardized_E_i_coefficient"]==0.2794138545592927
    assert x["scientific_interpretation"]["secondary_direction_may_not_rescue_primary"] is True

def test_current_status_restricts_conservation_claim():
    x=json.loads((ROOT/"development/current_status_v1_144.json").read_text())
    assert x["source_leverage_conservation_test"]["primary_supported"] is False
    assert "not yet validated" in x["revised_ecological_synthesis"]["core"]
    assert x["revised_ecological_synthesis"]["causal_rescue_or_extinction_established"] is False
    assert x["analysis_state"]["same_BALA_lineage_rerun_authorized"] is False

def test_cross_system_synthesis_does_not_promote_source_leverage():
    x=json.loads((ROOT/"development/source_loss_leverage_cross_system_synthesis_v1_144.json").read_text())
    assert x["independent_temporal_test"]["primary_supported"] is False
    assert any("general island-conservation prioritization metric" in z for z in x["ecological_update"]["not_validated"])
    assert "do not use BALA secondary E_i summaries to overturn the failed primary" in x["anti_rescue"]

def test_geb_v145_reports_temporal_non_support_and_stays_within_format():
    s=(GEB/"blinded_main_text.md").read_text()
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    main=s.split("## References",1)[0]
    assert len(abstract.split()) <= 300
    assert len(main.split()) < 5000
    assert "C−R2 = +0.00067" in abstract
    assert "Spatial source leverage is not yet a validated conservation-priority metric" in s
    assert "did not improve heldout prediction" in s
    assert "Pozsgai et al. 2024" in s

def test_geb_manifest_binds_v1144_science():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["scientific_freeze"]=="development/current_status_v1_144.json"
    b=x["independent_temporal_boundary"]
    assert b["taxa"]==20
    assert b["target_rows"]==64
    assert b["primary_supported"] is False
    assert x["claim_boundary"]["source_leverage_validated_management_metric"] is False
    assert x["claim_boundary"]["temporal_source_loss_consequence_supported"] is False

def test_priority_closes_bala_without_rescue():
    x=json.loads((ROOT/"development/structural_active_priority_v1_144.json").read_text())
    assert x["status"]=="bala_source_loss_primary_closed_non_support_no_rescue"
    do_not="\n".join(x["do_not"])
    assert "rerun BALA" in do_not
    assert "positive descriptive BALA E_i summaries" in do_not
    assert "search BALA taxa, islands or thresholds" in do_not
