"""Source original Brisbane 80 observed traps vs 79 environmental records join tests."""
import importlib.util
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_brisbane_environment_obs_join.py")
spec=importlib.util.spec_from_file_location("Brisbane_original_obs_environment_join",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fake_env_rows(*,missing=("T","10","Canopy",16)):
    bio=[{0:"Obs",1:"Abundance",2:"Richness",3:"Edge.dist",4:"Height"}]
    ground=[{0:"Edge.Dist",1:"Edge.Dist",2:"Dist.CBD",3:"Can.cov",4:"Lit.cov"}]
    canopy=[{0:"Traps",1:"Edge dist",2:"LogEdge.dist",3:"Dist.CBD",
             4:"Can.cov",5:"Trap.height"}]
    for site in range(1,11):
        for layer,edges in (("Ground",(1,4,16,64,256)),("Canopy",(1,16,256))):
            for edge in edges:
                code=f"T{site}{'G' if layer=='Ground' else 'C'}{edge}A"
                bio.append({0:code,1:"10",2:"5",3:str(edge),4:layer})
                base={0:code,1:str(edge),2:str(site),3:"55"}
                if layer=="Ground":
                    ground.append(base)
                elif not (missing and ("T",str(site),layer,edge)==missing):
                    canopy.append({0:code,1:str(edge),2:str(edge),3:str(site),
                                   4:"60",5:"1.1"})
    assert len(bio)==81 and len(ground)==51 and len(canopy)==30
    return bio,ground,canopy

def test_missing_one_canopy_metadata_does_not_invalidate_primary_sites():
    src=fake_env_rows()
    r=m.inspect(src)
    assert r["original_beetle_traps"]==80
    assert r["environment_rows_with_exact_original_Obs_matched_and_stratum_checked"]==79
    assert r["missing_environment_stratum_type"]=="Canopy"
    assert r["missing_environment_edge_distance_m"]==16
    assert r["source_pairwise_ground_and_canopy_environment_join_by_edge_m"]=={
        "1":{"complete_pairs":10,"expected_pairs":10},
        "16":{"complete_pairs":9,"expected_pairs":10},
        "256":{"complete_pairs":10,"expected_pairs":10}
    }
    assert r["original_species_taxon_columns_read"]==0
    assert r["new_species_environment_effect_calculated"] is False
    assert "T10C16A" not in str(r)
    assert r["no_source_Obs_trap_site_IDs_or_species_names_exported"]

def test_bad_raw_site_ID_join_is_fail_closed():
    orig=list(fake_env_rows())
    orig[2]=[dict(v) for v in orig[2]]
    orig[2][2][0]="T99C1A"
    with pytest.raises(ValueError,match="unmatched_to_original_stratum"):
        m.inspect(orig)

def test_source_identity_conflict_is_not_ignored():
    orig=list(fake_env_rows())
    orig[1]=[dict(v) for v in orig[1]]
    orig[1][1][0]="T1C1A"
    with pytest.raises(ValueError,match="unmatched_to_original_stratum"):
        m.inspect(orig)
