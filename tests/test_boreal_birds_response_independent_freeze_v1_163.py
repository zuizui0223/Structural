from __future__ import annotations

import importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_birds_response_independent_v1_163.py"

def module():
    spec=importlib.util.spec_from_file_location("birdfreeze163",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_canonical_freeze_replays_exact_response_free_outputs():
    m=module()
    ens,raw,topo,receipt=m.freeze(
        freeze_parent_sha="a"*40,
        request_commit_sha="b"*40,
    )
    r=json.loads(receipt)
    assert r["status"]=="CANONICAL_RESPONSE_INDEPENDENT_FREEZE"
    assert r["children"]["null_ensemble"]["null_count"]==20
    assert r["children"]["null_ensemble"]["sha256"]=="069eae639ed8a544d09680b7034c697bad608b7652a0cee60e92d41029d48e12"
    assert r["children"]["raw_configuration_surface"]["sha256"]=="70f36be8cb2318ad7589491fb448f5787be9df3e8457e5b919953243a6c08d79"
    assert r["children"]["topology_residual_surface"]["sha256"]=="d7913be64b62ae92378ab8279c6eea9fa69289d3908d9c3916694f7ea83a22e7"
    assert r["children"]["topology_residual_surface"]["H_topo_min_hex"]=="0x1.91df3c1a44aaap-9"
    assert r["children"]["topology_residual_surface"]["H_topo_max_hex"]=="0x1.5dfe6126b8b8dp+1"
    assert r["children"]["topology_residual_surface"]["H_topo_unique_count"]==13
    assert r["response_boundary"]["bird_response_values_opened"]==0
    assert r["response_boundary"]["pilot_response_authorized"] is False
    assert r["response_boundary"]["confirmatory_response_authorized"] is False

def test_workflow_exact_binds_parent_and_refuses_moving_branch():
    s=(ROOT/".github/workflows/boreal-birds-response-independent-freeze-v1_163.yml").read_text()
    assert 'ref: ${{ github.sha }}' in s
    assert 'git rev-parse HEAD^' in s
    assert 'parent==req["freeze_parent_sha"]' in s
    assert 'git ls-remote origin refs/heads/science/boreal-birds-topology-canonical-v1-163' in s
    assert 'canonical branch moved after request; refusing output commit' in s
