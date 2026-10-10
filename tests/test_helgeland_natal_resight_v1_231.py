import hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_natal_resight_v1_231 import score,blob
def fixtures():
    pop=("Location;Island;Year;N_corr;N_obs\n"+
         "".join(f"isle{i};{i};1994;1;1\n" for i in range(1,12))).encode()
    rows=["Year;Island;stage;ID"]
    rows.extend(["1994;1;nest;birdA","1995;2;capt;birdA",
                 "1994;3;nest;birdB","1995;3;obs;birdB",
                 "2015;4;nest;birdC","2016;5;obs;birdC",
                 "2015;6;nest;birdD",
                 "2014;7;nest;birdE","2015;8;obs;birdE",
                 "2015;9;nest;birdF","2015;10;nest;birdF"])
    pres=("\n".join(rows)+"\n").encode()
    c={"source":{"presence_sha":blob(pres),"population_sha":blob(pop)}}
    return pres,pop,c
def test_known_natal_and_bridge():
    a,b,c=fixtures();r=score(a,b,c)
    assert r["periods"]["historical"]["immigrant"]==1
    assert r["periods"]["historical"]["resident"]==1
    assert r["periods"]["later"]["immigrant"]==1
    assert r["periods"]["later"]["unknown_followup"]==1
    assert r["periods"]["bridge"]["immigrant"]==1
    assert r["source_qc"]["ambiguous_natal_id_global"]==1
    assert not r["documented_transfer_is_not_all_dispersal_or_demographic_rescue"] is False
def test_source_blob_guard():
    a,b,c=fixtures();c["source"]["presence_sha"]="0"*40
    try:score(a,b,c)
    except ValueError as e:assert "fingerprint" in str(e)
    else:raise AssertionError("Source drift not rejected")
