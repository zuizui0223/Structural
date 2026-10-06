from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/project_sw_finland_potential_islands_v1_170.py"
CONTRACT=ROOT/"development/sw_finland_potential_islands_projection_contract_v1_170.json"

def load():
    spec=importlib.util.spec_from_file_location("swf170",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def contract(n=4):
    c=json.loads(CONTRACT.read_text());c=dict(c)
    c["validation"]=dict(c["validation"])
    c["validation"]["expected_unique_species"]=n
    c["validation"]["sentinels"]={}
    return c

def word(text,x1,x2):
    return f'<word xMin="{x1}" yMin="1" xMax="{x2}" yMax="2">{text}</word>'

def line(*words):
    return '<line xMin="1" yMin="1" xMax="500" yMax="2">'+"".join(words)+"</line>"

def synthetic_bbox():
    header=line(
        word("species",10,40),
        word("Potential_islands",200,270),
        word("Num_colonized",300,360),
        word("Prop_colonized",380,440),
        word("Random_effect",450,510),
    )
    rows=[
      line(word("Acer",10,30),word("platanoides",35,90),word("464",220,240),word("17",320,330),word("0.03",400,420),word("NA",470,485)),
      line(word("Alchemilla",10,50),word("filicaulis",55,95),word("ssp.",100,120),word("filicaulis",125,165),word("455",220,240),word("0",320,330),word("0",400,405),word("NA",470,485)),
      line(word("Allium",10,35),word("schoenoprasum",40,110),word("56",225,237),word("35",320,330),word("0.625",400,425),word("1.2",470,485)),
      line(word("Anchusa",10,40),word("arvensis",45,80),word("471",220,240),word("0",320,330),word("0",400,405),word("NA",470,485)),
    ]
    end=line(
        word("Island_name",10,70),word("Euref_X",100,150),word("Euref_Y",160,210),
        word("Potential_spp",220,280)
    )
    return '<html><body><page width="600" height="800"><flow><block>'+header+"".join(rows)+end+'</block></flow></page></body></html>'

def test_bbox_extract_reads_only_species_and_potential_column():
    m=load()
    rows=m.extract_bbox(synthetic_bbox(),contract())
    assert [(r["species"],r["Potential_islands"]) for r in rows]==[
      ("Acer platanoides",464),
      ("Alchemilla filicaulis ssp. filicaulis",455),
      ("Allium schoenoprasum",56),
      ("Anchusa arvensis",471),
    ]
    assert rows[0]["historical_source_count"]==7
    assert rows[-1]["historical_source_count"]==0
    assert all(set(r)=={"species","Potential_islands","historical_source_count"} for r in rows)

def test_future_summary_values_are_not_returned_or_semantically_parsed():
    x=json.loads(CONTRACT.read_text())
    f=x["forbidden_future_summary_semantics"]
    assert f["may_be_persisted"] is False
    assert f["may_define_eligibility"] is False
    assert f["may_be_returned_in_receipt"] is False
    assert f["values_decoded_by_structural_parser"]==0

def test_wrong_species_count_stops():
    m=load()
    c=contract(5)
    try:m.extract_bbox(synthetic_bbox(),c)
    except m.Stop:pass
    else:raise AssertionError("incomplete supplement extraction must stop")
