"""Synthetic original Event / Occurrence extension audit tests (no private rows)."""
import csv,io,importlib.util,zipfile,json
from pathlib import Path

FILE=Path(__file__).with_name("audit_thai_beetle_canopy_original.py")
spec=importlib.util.spec_from_file_location("thai_beetles",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def make_archive():
    emap=["eventID","locationID","eventDate","samplingProtocol","habitat","eventRemarks"]
    omap=["family","genus","specificEpithet","taxonRank","individualCount"]
    root=[
        '<archive xmlns="http://rs.tdwg.org/dwc/text/">',
        '<core encoding="UTF-8" fieldsTerminatedBy="\\t" fieldsEnclosedBy="&quot;" ignoreHeaderLines="1" rowType="'+m.EVENT_TYPE+'">',
        '<files><location>event.txt</location></files><id index="0"/>'
    ]
    for i,t in enumerate(emap):root.append('<field index="'+str(i)+'" term="http://rs.tdwg.org/dwc/terms/'+t+'"/>')
    root.append('</core>')
    root.append('<extension encoding="UTF-8" fieldsTerminatedBy="\\t" fieldsEnclosedBy="&quot;" ignoreHeaderLines="1" rowType="'+m.OCC_TYPE+'">')
    root.append('<files><location>occurrence.txt</location></files><coreid index="0"/>')
    for i,t in enumerate(omap,1):root.append('<field index="'+str(i)+'" term="http://rs.tdwg.org/dwc/terms/'+t+'"/>')
    root+=['</extension>','</archive>']
    events=[
        ["e1","KhaoYai","2019-06-21","SLAM 10 days","forest","trap in canopy"],
        ["e2","KhaoYai","2019-06-21","SLAM 10 days","forest","trap in understory"],
        ["e3","KhaoYai","2019-06-21","SLAM 10 days","forest",""],
        ["e4","KlongNaka","2020-09-01","SLAM 10 days","forest","trap at 2m"]
    ]
    occurrence=[
        ["e1","Staphylinidae","","","family","3"],
        ["e1","Curculionidae","X","","genus","1"],
        ["e2","Staphylinidae","","","family","2"],
        ["e9","Notrealidae","","","family","1"]
    ]
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.xml","".join(root))
        for path,rows in (("event.txt",events),("occurrence.txt",occurrence)):
            out=io.StringIO()
            w=csv.writer(out,delimiter="\t")
            w.writerow(["ignored source header"])
            w.writerows(rows)
            z.writestr(path,out.getvalue())
    return buf.getvalue()

def test_dwc_core_extension_join_and_strata_assignment():
    data=m.inspect_bytes(make_archive())
    assert data["source_publisher_event_rows"]==4
    assert data["publisher_occurrence_extension_rows"]==4
    assert data["occurrence_extensions_with_nonmatching_Event_coreID"]==1
    assert data["stratum_assignment_from_explicit_original_event_fields"]=={
      "canopy":1,"understorey":1,"unknown":2}
    assert data["occurrences_by_explicit_original_stratum_field"]=={"canopy":2,"understorey":1}
    assert data["occurrence_rows_with_family_label"]==3
    assert data["occurrence_rows_with_specificEpithet"]==0
    assert data["new_beetle_canopy_vs_understorey_effect_scored"] is False
    assert "Notrealidae" not in json.dumps(data)

def test_ambiguous_stratum_and_missing_id_rejected():
    assert m.stratum("canopy trap")=="canopy"
    assert m.stratum("Understorey level")=="understorey"
    assert m.stratum("no relevant text") is None

def test_wrong_license_fails_before_downloading(tmp_path):
    def meta(url):
        return {"key":m.UID,"type":"SAMPLING_EVENT","license":"CC_BY_NC_4_0",
                "endpoints":[{"type":"DWC_ARCHIVE","url":"https://example.org/source.zip"}]}
    try:
        m.run(tmp_path,request=meta,download=lambda url:make_archive())
        assert False
    except ValueError as e:
        assert "requires_cc_by_original_license" in str(e)
