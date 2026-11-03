#!/usr/bin/env python3
"""v1.348: Reproduce blinded JBI Word files from ALREADY FROZEN figure artifact.

Input is strictly the v1.347 original-SOURCE-FREE GitHub Actions archive:
one anonymous Markdown, one anonymous S1 Markdown, three rendered figures,
and original SHA provenance. The BALA 10,379 Event and 63,904 Occurrence
records are NEVER accessed. This program creates editable DOCX with three
embedded figures, a separate landscape editable S1 table, and metadata QA.

Required: pandoc >= 2; python-docx. The source figures are NOT regenerated.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

MAIN_SHA="076a0549d344f16c693cb50866fec1c0d6ed0f9e0cd7b5916e2d5b18db17bb9b"
S1_SHA="775c7fa3efb5a7d5119a5e363f893cdf32eaeeab6b8f60a3b87bd7edb88df5bc"
DATA_SHA="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
FIGS=("figure1_temporal_excess.png","figure2_spatial_beta_by_island.png",
      "figure3_alpha_spatial_decoupling.png")

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def set_black_headings(doc):
    for style in doc.styles:
        if style.style_id.startswith("Heading") or style.style_id=="Title":
            style.font.color.rgb=RGBColor(0,0,0)

def add_header_footer(doc,running):
    for s in doc.sections:
        head=s.header.paragraphs[0]
        head.text=running;head.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        for r in head.runs:r.font.size=Pt(8)
        foot=s.footer.paragraphs[0]
        foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
        foot.add_run("Page ")
        fld=OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"),"PAGE")
        foot._p.append(fld)
    doc.core_properties.author=""
    doc.core_properties.last_modified_by=""
    doc.core_properties.comments=""
    doc.core_properties.keywords=""
    doc.core_properties.identifier=""

def build(inp,out):
    inp=Path(inp);out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    raw=(inp/"JBI_anonymized_main_text_v1_347.md").read_bytes()
    si=(inp/"JBI_anonymized_Supplementary_Table_S1_v1_347.md").read_bytes()
    assert sha(raw)==MAIN_SHA and sha(si)==S1_SHA
    manifest=json.loads((inp/"figure_bundle_manifest.json").read_text())
    assert manifest["original_archive_SHA256"]==DATA_SHA
    assert manifest["original_Event_or_Occurrence_rows_opened"]==0
    assert all((inp/name).is_file() for name in FIGS)
    body=[]
    for line_no,line in enumerate(raw.decode("utf-8").splitlines()):
        if line_no in (2,3) and ("ANONYMIZED WORKING MANUSCRIPT" in line or line.startswith("Version v1.345")):
            continue
        if line.strip()=="---":continue
        if line.startswith("## References (verified"):line="## References"
        if line=="## Data availability and reproducibility":line="## Data accessibility statement"
        if line.startswith("**Keywords:**"):line=line.replace("Azores; arthropods;","arthropods; Azores;")
        body.append(line)
    main_md="\n".join(body)+"\n"
    s1_md=si.decode("utf-8").replace(
        "# Supplementary Table S1 — Original BALA seven-island uncertainty, v1.346",
        "# Supplementary Table S1. Seven-island uncertainty of temporal turnover and spatial beta diversity")
    s1_md=s1_md.replace(chr(92)*2+"(",chr(92)+"(").replace(chr(92)*2+")",chr(92)+")")
    assert "zuizui0223" not in main_md+s1_md
    (out/"main_source_blinded.md").write_text(main_md,encoding="utf-8")
    (out/"S1_source_blinded.md").write_text(s1_md,encoding="utf-8")
    for name in FIGS:
        assert (inp/name).stat().st_size>10000
    def convert(src,dest):
        subprocess.run(["pandoc",str(src),"--from=markdown+tex_math_single_backslash+pipe_tables",
                        "--to=docx","-o",str(dest)],check=True)
    convert(out/"main_source_blinded.md",out/"main_raw.docx")
    convert(out/"S1_source_blinded.md",out/"S1_raw.docx")
    d=Document(out/"main_raw.docx")
    s=d.sections[0]
    s.page_width=Inches(8.27);s.page_height=Inches(11.69)
    s.left_margin=Inches(1.05);s.right_margin=Inches(1.05)
    s.top_margin=Inches(.95);s.bottom_margin=Inches(.87)
    for st in d.styles:
        if st.style_id in ("Normal","BodyText","FirstParagraph"):
            st.font.name="Times New Roman";st.font.size=Pt(11)
            st.paragraph_format.line_spacing=1.25
    set_black_headings(d);add_header_footer(d,"Two dimensions of island turnover")
    for para in d.paragraphs:
        if para.text.strip()=="Figure legends":para.paragraph_format.page_break_before=True
    d.add_page_break()
    for i,f in enumerate(FIGS):
        if i:d.add_page_break()
        d.add_paragraph("Figure "+str(i+1),style="Heading1")
        p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pict=p.add_run().add_picture(str(inp/f),width=Inches(6.05))
        pict._inline.docPr.set("descr",("Temporal community turnover","Spatial beta diversity","Alpha richness and beta diversity")[i])
    main=out/"BALA_JBI_v1_348_anonymous_manuscript_with_figures.docx"
    d.save(main)
    s1doc=Document(out/"S1_raw.docx")
    sect=s1doc.sections[0]
    sect.page_width=Inches(11.69);sect.page_height=Inches(8.27)
    sect.left_margin=Inches(.7);sect.right_margin=Inches(.7)
    sect.top_margin=Inches(.75);sect.bottom_margin=Inches(.7)
    set_black_headings(s1doc);add_header_footer(s1doc,"Supplementary Table S1 | Seven-island uncertainty")
    for table in s1doc.tables:
        table.autofit=False;table.alignment=WD_TABLE_ALIGNMENT.CENTER
        for row in table.rows:
            for cell in row.cells:
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for para in cell.paragraphs:
                    for r in para.runs:r.font.size=Pt(8.25)
        if table.rows:
            trPr=table.rows[0]._tr.get_or_add_trPr()
            repeat=OxmlElement("w:tblHeader");repeat.set(qn("w:val"),"true");trPr.append(repeat)
    s1doc.save(out/"BALA_JBI_v1_348_anonymous_supplementary_table_S1.docx")
    rendered=Document(main);s1read=Document(out/"BALA_JBI_v1_348_anonymous_supplementary_table_S1.docx")
    assert len(rendered.inline_shapes)==3 and len(s1read.tables)==1
    assert "github.com/zuizui0223" not in "\n".join(x.text for x in rendered.paragraphs)
    receipt={"schema":"structural.bala_jbi_blinded_word_sourcefree.v1_348",
        "status":"BLINDED_EDITABLE_WORD_AND_S1_RECREATED_FROM_FIXED_SOURCE_FREE_CI",
        "source_original_10k_Event_or_64k_Occurrence_rows_reopened":0,
        "original_source_archive_SHA256":DATA_SHA,
        "original_blinded_main_SHA256":MAIN_SHA,"original_blinded_S1_SHA256":S1_SHA,
        "docx_main_sha256":sha(main.read_bytes()),
        "docx_S1_sha256":sha((out/"BALA_JBI_v1_348_anonymous_supplementary_table_S1.docx").read_bytes()),
        "embedded_figure_count":3,"editable_S1_tables":1,
        "source_7_islands_same_archipelago_not_independent":True,
        "island_spatial_beta_95pct_interval_crosses_zero":True,
        "no_new_confirmatory_system":True,"GEB_scientific_HOLD":True,
        "not_submitted":True}
    (out/"Word_sourcefree_manifest.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.input,a.out),sort_keys=True))
