from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUTH=ROOT/"development/pnw_stage2_authorization_v0_19.json"

def test_stage2_pins_stage1_feature_fingerprint():
    x=json.loads(AUTH.read_text())
    assert x["locked_inputs"]["stage1_feature_table_sha256"] ==         "f2e85764d736ee069c5805e6a808b7e434bbb2930cfa0808e7ff723927af4ce6"
    assert x["locked_inputs"]["stage1_state_table_sha256"] ==         "bbf407503d1db9f911989d27717bb44e80d4028b65647c7b588d23f5bf87b440"

def test_stage2_applicability_is_frozen_pre_target():
    x=json.loads(AUTH.read_text())
    a=x["applicability"]
    assert a["require_2012_lagged_state_estimable"] is True
    assert a["require_2013_target_estimable"] is True
    assert a["no_other_post_response_site_filtering"] is True

def test_stage2_keeps_primary_contrast_and_no_rescue():
    x=json.loads(AUTH.read_text())
    assert x["scoring"]["primary_contrast"] == "C minus R2"
    assert "change movement worldset" in x["forbidden"]
    assert "change applicability after viewing target" in x["forbidden"]
    assert x["counts_as_pristine_fresh_evidence"] is False
