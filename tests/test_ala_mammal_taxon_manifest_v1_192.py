from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_ala_mammal_taxon_manifest_v1_192.py"
CONTRACT=ROOT/"development/global_mammals_ala_taxon_manifest_gate_v1_192.json"

def load():
    s=importlib.util.spec_from_file_location("ala_v192",SCRIPT)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

def dbf_fixture():
    # Only a synthetic DBF. FID is explicitly present but must never be decoded.
    fields=[("FID",8),("scientific",25)]
    n=3; header_len=32+32*len(fields)+1; record_len=1+sum(w for _,w in fields)
    hdr=bytearray(header_len);hdr[0]=3
    hdr[4:8]=n.to_bytes(4,"little");hdr[8:10]=header_len.to_bytes(2,"little")
    hdr[10:12]=record_len.to_bytes(2,"little")
    for i,(name,width) in enumerate(fields):
        pos=32+i*32
        hdr[pos:pos+11]=name.encode().ljust(11,b"\0")
        hdr[pos+11]=ord("C");hdr[pos+16]=width
    hdr[-1]=13
    data=[("F1","Rattus testus"),("F2","Rattus testus"),("F3","Petaurus breviceps")]
    rows=b"".join(b" "+fid.encode().ljust(8,b" ")+tax.encode().ljust(25,b" ") for fid,tax in data)
    return bytes(hdr)+rows+b"\x1a"

def test_dbf_reads_only_unique_taxon_field():
    m=load()
    taxa,meta=m.dbf_taxon_set(dbf_fixture(),"scientific")
    assert taxa=={"rattus testus","petaurus breviceps"}
    assert meta["rows"]==3
    assert meta["field_name"]=="scientific"
    assert "FID" in meta["field_names"]
    # No original or external island/species pairs were returned.
    assert "F1" not in str((taxa,meta))

def test_unregistered_field_cannot_be_substituted():
    m=load()
    try:m.dbf_taxon_set(dbf_fixture(),"scientificName")
    except m.Stop:pass
    else:raise AssertionError("field substitution should fail")

def test_frozen_biology_boundary_and_minimum():
    c=json.loads(CONTRACT.read_text())
    assert c["geometry_authority"]["frozen_exact_matches"]==167
    assert c["parsing_policy"]["min_distinct_matching_focal_species"]==20
    assert c["external"]["taxon_dbf_column"]=="scientific"
    assert c["parsing_policy"]["no_species_by_FID_pair_materialized"] is True
    assert c["response_boundary"]["ala_species_by_island_positive_pairs_read"]==0
    assert c["response_boundary"]["original_heldout_responses_opened"]==0
    assert c["response_boundary"]["model_refit"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
