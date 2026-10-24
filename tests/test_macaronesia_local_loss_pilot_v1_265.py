"""Original workbook S1 local extirpation data parser/accountant regression.
Synthetic names and events ONLY; never test against known paper outcomes.
"""
import io, zipfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1, summarize_source_events

NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFF="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL="http://schemas.openxmlformats.org/package/2006/relationships"

def fake_xlsx():
    headers=["Species","Extinction category","Category","Island","Archipelago",
             "Date","Pollination mechanism","Seed dispersal mechanism",
             "Habit","Endemicity"]
    events=[
       ["Alpha beta","Extirpation (Island level)","Well-supported","Island 1","Azores",
        "1980","Entomophily","Zoochory","Woody","Endemic"],
       ["Alpha beta","Extirpation (Island level)","Well-supported","Island 2","Azores",
        "1990","Entomophily","Zoochory","Woody","Endemic"],
       ["Alpha beta","Extirpation (Island level)","Well-supported","Island 2","Azores",
        "1991","Entomophily","Zoochory","Woody","Endemic"],
       ["Gamma delta","Globally extinct","Well-supported","Island 3","Canary Islands",
        "1992","Anemophily","Autochory","Herbaceous","Native"],
       ["Zeta lambda","Extirpation (Island level)","Doubtful","Island 3","Canary Islands",
        "1801","Anemophily","Autochory","Herbaceous","Native"],
       ["Kappa rho","Extirpation (Archipelago level)","Well-supported","Island 4","Madeira",
        "1900","Anemophily","Zoochory","Woody","Native"],
    ]
    def cells(data,n):
        out=[]
        for j,v in enumerate(data):
            # Construct A, B, C... cells in inline string encoding.
            c=chr(ord("A")+j)
            out.append(f'<c r="{c}{n}" t="inlineStr"><is><t>{v}</t></is></c>')
        return f'<row r="{n}">{"".join(out)}</row>'
    xml=(f'<worksheet xmlns="{NS}"><dimension ref="A1:J7"/><sheetData>'
         +cells(headers,1)+"".join(cells(row,i+2) for i,row in enumerate(events))
         +'</sheetData></worksheet>')
    with io.BytesIO() as b:
        with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr("xl/workbook.xml",f'<workbook xmlns="{NS}" xmlns:r="{OFF}"><sheets><sheet name="Table S1" sheetId="1" r:id="rId1"/><sheet name="Table S3" sheetId="3" r:id="rId3"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels",f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId3" Target="worksheets/sheet3.xml"/></Relationships>')
            z.writestr("xl/worksheets/sheet1.xml",xml)
            z.writestr("xl/worksheets/sheet3.xml",f'<worksheet xmlns="{NS}"><sheetData><row r="2"><c r="A2" t="inlineStr"><is><t>PROTECTED_FUTURE_HOLDOUT_SPECIES</t></is></c></row></sheetData></worksheet>')
        return b.getvalue()

def test_parses_ONLY_S1_six_local_and_global_observed_records():
    rec=parse_sheet_s1(fake_xlsx())
    assert len(rec)==6
    assert rec[0]["Species"]=="Alpha beta"
    assert rec[0]["Island"]=="Island 1"
    assert "PROTECTED_FUTURE_HOLDOUT_SPECIES" not in str(rec)

def test_strict_island_well_supported_filters_global_archipelago_uncertain_and_duplicate():
    r=summarize_source_events(parse_sheet_s1(fake_xlsx()),expected_num_records=None)
    assert r["source_species_records"]==6
    assert r["strict_well_supported_island_loss_raw_records"]==3
    assert r["strict_distinct_taxon_island_loss_pairs"]==2
    assert r["taxa_with_strict_losses_on_two_plus_islands"]==1
    assert r["taxa_with_strict_losses_in_two_plus_archipelagos"]==0
    assert r["strict_island_loss_archipelagos"]=={"Azores":2}
    assert r["strict_island_loss_named_island_count"]==2
    assert r["source_confidence_categories"]["Doubtful"]==1
    assert r["source_extinction_categories"]["Globally extinct"]==1

def test_no_taxon_identity_escapes_public_aggregate():
    r=summarize_source_events(parse_sheet_s1(fake_xlsx()),expected_num_records=None)
    assert "Alpha beta" not in str(r)
    assert "Zeta lambda" not in str(r)
    assert "Island 1" not in str(r)
    assert "pollination" in str(r).lower()

def test_author_168_records_remains_fail_closed_when_expected():
    try:
        summarize_source_events(parse_sheet_s1(fake_xlsx()),expected_num_records=168)
    except ValueError as exc:
        assert "168" in str(exc)
    else:
        raise AssertionError("Must stop when original published 168 source event denominator not met")

def test_malformed_or_missing_original_s1_workbook_cannot_be_replaced_by_s3():
    try:
        parse_sheet_s1(b"<html>access denied</html>")
    except ValueError:
        pass
    else:
        raise AssertionError("Unverified workbook source body cannot be accepted")
