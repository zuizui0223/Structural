from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
W171=ROOT/".github/workflows/sw-finland-exact-source-dispatch-v1_171.yml"
W172=ROOT/".github/workflows/sw-finland-topology-dispatch-v1_172.yml"

def test_v171_dispatch_requires_validated_t0_lookup_only():
    s=W171.read_text()
    assert "sw_finland_species_potential_islands_v1_168.csv" in s
    assert 'future_summary_values_persisted"]==0' in s
    assert 'row_level_recent_outcome_opened"] is False' in s
    assert '"future_outcome_access_requested":False' in s
    assert "lookup_sha256" in s

def test_v172_dispatch_binds_all_four_v171_outputs():
    s=W172.read_text()
    for key in ("reconstruction","geometry","species","membership"):
        assert f'"{key}"' in s
    assert 'future_outcome_values_opened"]==0' in s
    assert '"future_outcome_access_requested":False' in s
    assert "input_sha256" in s
