"""Known-truth Brisbane OOXML original 80 beetle / 50 ground / 29 canopy support."""
import hashlib,importlib.util,zipfile
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_brisbane_stratum_env_grain.py")
spec=importlib.util.spec_from_file_location("Brisbane_beetle_source_grain",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def cell(col,row,value):
    if isinstance(value,str):
        return f'<c r="{col}{row}" t="inlineStr"><is><t>{value}</t></is></c>'
    return f'<c r="{col}{row}"><v>{value}</v></c>'

def fake(path):
    ns=m.OOXML
    sheets=[
        ("Beetle data",["TrapID","EDGE","Edge.dist","Height","SECRET_speciesName"],
         [(str(i),str(i%4),str(i*2), "Ground" if i<=50 else "Canopy","SECRET_TAXON") for i in range(1,81)]),
        ("Ground level enviros",["","Edge.Dist","Can.cov"],
         [(str(i),str(i*3),str(i%80)) for i in range(1,51)]),
        ("Canopy level enviros",["Traps","Edge dist","Trap.height"],
         [(str(i),str(i*4),str(i%20)) for i in range(51,80)])
    ]
    zip_entries={}
    rxml=[]
    relxml=[]
    for n,(name,header,data) in enumerate(sheets,1):
        rows=[]
        for ri,vals in enumerate([header]+data,1):
            content=""
            for ci,val in enumerate(vals):
                col=chr(ord("A")+ci)
                if val=="" :continue
                content+=cell(col,ri,val)
            rows.append(f'<row r="{ri}">{content}</row>')
        zip_entries[f"xl/worksheets/sheet{n}.xml"]=f'<worksheet xmlns="{ns}"><sheetData>{"".join(rows)}</sheetData></worksheet>'
        rxml.append(f'<sheet name="{name}" sheetId="{n}" r:id="rId{n}"/>')
        relxml.append(f'<Relationship Id="rId{n}" Target="worksheets/sheet{n}.xml"/>')
    zip_entries["xl/workbook.xml"]=f'<workbook xmlns="{ns}" xmlns:r="{m.REL}"><sheets>{"".join(rxml)}</sheets></workbook>'
    zip_entries["xl/_rels/workbook.xml.rels"]=f'<Relationships xmlns="{m.PKGREL}">{"".join(relxml)}</Relationships>'
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for k,v in zip_entries.items():z.writestr(k,v)

def test_80_observations_and_79_separate_environment_rows_not_80_woods(tmp_path):
    file=tmp_path/"source.xlsx";fake(file)
    original=m.SOURCE_MD5
    m.SOURCE_MD5=hashlib.md5(file.read_bytes()).hexdigest()
    try:res=m.run(file,tmp_path/"out")
    finally:m.SOURCE_MD5=original
    assert res["source_original_Beetle_data_TRAP_records_NOT_80_FORESTS"]==80
    assert res["source_Ground_level_environment_rows"]==50
    assert res["source_Canopy_level_environment_rows"]==29
    assert res["one_fewer_source_environment_row_than_biological_trap_count"]==1
    assert res["source_original_Height_stratum_or_value_counts"]=={"Ground":50,"Canopy":30}
    assert res["source_original_Height_stratum_or_value_counts"]=={"Ground":50,"Canopy":30}
    assert res["beetle_source_Edge_dist_nonempty_record_count"]==80
    assert res["taxon_abundance_source_columns_read"]==0
    assert res["original_first_column_beetle_vs_env_ID_overlap_NOT_JOIN_PROOF"]=={"ground":50,"canopy":29}
    assert "SECRET_TAXON" not in str(res)

def test_original_checksum_and_exact_workbook_sheets_required(tmp_path):
    file=tmp_path/"source.xlsx";fake(file)
    with pytest.raises(ValueError,match="original_Brisbane_xlsx_source_hash_mismatch"):
        m.audit(file)
