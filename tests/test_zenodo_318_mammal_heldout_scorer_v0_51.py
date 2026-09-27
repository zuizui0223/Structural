from __future__ import annotations

import hashlib
import io
import zipfile

from structural.zenodo_318_mammal_heldout_scorer import (
    extract_heldout_outcomes,
    score_frozen_predictions,
)


def workbook_bytes() -> tuple[bytes,str]:
    species=["spA","spB","spC"]
    digest=hashlib.sha256(("\n".join(species)+"\n").encode()).hexdigest()

    workbook='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="occurrence" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''
    rels='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''

    def inline(ref,value):
        return f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'
    def num(ref,value):
        return f'<c r="{ref}"><v>{value}</v></c>'
    def sealed_error(ref):
        return f'<c r="{ref}" t="e"><v>#VALUE!</v></c>'

    row4="<row r=\"4\">"+ "".join([
        inline("A4","ID"),inline("B4","Island"),inline("C4","Island_group"),
        inline("D4","spA"),inline("E4","spB"),inline("F4","spC"),
    ])+"</row>"
    # ID=1 is sealed non-heldout. Its occurrence cells are deliberately
    # incompatible with the opened-value decoder and must never be decoded.
    row5="<row r=\"5\">"+ "".join([
        num("A5",1),inline("B5","pilot"),inline("C5","A"),
        sealed_error("D5"),sealed_error("E5"),sealed_error("F5"),
    ])+"</row>"
    row6="<row r=\"6\">"+ "".join([
        num("A6",2),inline("B6","held-extreme"),inline("C6","A"),
        num("D6",1),num("E6",0),num("F6",1),
    ])+"</row>"
    row7="<row r=\"7\">"+ "".join([
        num("A7",3),inline("B7","held-non"),inline("C7","B"),
        num("D7",1),num("E7",0),num("F7",1),
    ])+"</row>"
    sheet=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <dimension ref="A1:F7"/>
 <sheetData>{row4}{row5}{row6}{row7}</sheetData>
</worksheet>'''

    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml",workbook)
        z.writestr("xl/_rels/workbook.xml.rels",rels)
        z.writestr("xl/worksheets/sheet1.xml",sheet)
    return out.getvalue(),digest


def test_heldout_router_never_decodes_sealed_nonheldout_occurrence():
    raw,digest=workbook_bytes()
    out=extract_heldout_outcomes(
        workbook_bytes=raw,
        heldout_island_ids=["2","3"],
        fixed_species=["spA","spB","spC"],
        expected_species_headers_sha256=digest,
        expected_species_count=3,
        expected_sheet_dimension="A1:F7",
        first_data_row=5,
        last_data_row=7,
    )
    assert out.targets_by_island=={
        "2":(1,0,1),
        "3":(1,0,1),
    }
    assert out.heldout_islands_opened==2
    assert out.heldout_occurrence_values_parsed==6
    assert out.sealed_nonheldout_occurrence_values_parsed==0


def test_frozen_scoring_and_cluster_bootstrap_are_deterministic():
    raw,digest=workbook_bytes()
    outcomes=extract_heldout_outcomes(
        workbook_bytes=raw,
        heldout_island_ids=["2","3"],
        fixed_species=["spA","spB","spC"],
        expected_species_headers_sha256=digest,
        expected_species_count=3,
        expected_sheet_dimension="A1:F7",
        first_data_row=5,
        last_data_row=7,
    )

    rows=["island_id,species,p_R3_hex,p_C_hex,extreme_q75,archipelago,type\n"]
    for sp in ["spA","spB","spC"]:
        y=1 if sp!="spB" else 0
        pc=0.8 if y else 0.2
        rows.append(f"2,{sp},{float(0.5).hex()},{float(pc).hex()},1,A,Isolated\n")
    for sp in ["spA","spB","spC"]:
        rows.append(f"3,{sp},{float(0.5).hex()},{float(0.5).hex()},0,B,Connected\n")
    pred="".join(rows)
    sha=hashlib.sha256(pred.encode()).hexdigest()

    first=score_frozen_predictions(
        prediction_csv=pred,
        expected_prediction_sha256=sha,
        outcomes=outcomes,
        heldout_order=["2","3"],
        fixed_species=["spA","spB","spC"],
        bootstrap_replicates=1000,
        bootstrap_seed=20260927,
    )
    second=score_frozen_predictions(
        prediction_csv=pred,
        expected_prediction_sha256=sha,
        outcomes=outcomes,
        heldout_order=["2","3"],
        fixed_species=["spA","spB","spC"],
        bootstrap_replicates=1000,
        bootstrap_seed=20260927,
    )
    assert first==second
    assert first["primary_extreme_minus_nonextreme"]<0
    assert first["bootstrap"]["ci_95_high"]<0
    assert first["primary_supported"] is True
    assert first["counts_as_fresh_confirmation"] is False
