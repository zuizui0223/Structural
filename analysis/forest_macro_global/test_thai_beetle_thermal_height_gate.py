"""Synthetic Thai trap-height Event-only parsing; no original species responses."""
import importlib.util
import json
import io
import zipfile
import csv
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_thermal_height_gate.py")
spec=importlib.util.spec_from_file_location("thai_thermal_height_gate",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_named_numeric_fields_require_unambiguous_keys():
    q=m.extract_named_numeric('{"trapHeight":"24 m","temperatureC":31,"lightIntensityLux":4520}')
    assert ("trapheight",24.0) in q
    assert ("temperaturec",31.0) in q
    assert ("lightintensitylux",4520.0) in q
    assert m.extract_named_numeric("the forest canopy is 25 m tall") == []
    assert ("trapheight",15.0) in m.extract_named_numeric("trap height = 15 m")
    assert ("trapheight",21.0) in m.extract_named_numeric("trap height in meters:21")
    assert m.parse_numeric("28.5°C")==28.5
    assert m.parse_numeric("danger:25")==None


def synthetic_events(height_under=True):
    protocols=[
      "light trap (canopy)","light trap (understory)",
      "slam trap (canopy top jar)","slam trap (canopy bottom jar)",
      "slam trap (understory top jar)","slam trap (understory bottom jar)",
      "fit with yellow pan (canopy)","fit with yellow pan (understory)"
    ]
    out=[]
    for p in protocols:
        for _ in range(36):
            layer="canopy" if "canopy" in p else "understory"
            val="25" if layer=="canopy" else "2"
            out.append({"samplingProtocol":p,"dynamicProperties":json.dumps(
                 {"trapHeight":val,"temperatureC":32 if layer=="canopy" else 27,
                  "lightIntensityLux":10000 if layer=="canopy" else 1000}
                 if height_under or layer=="canopy" else {"air":1}
             )})
    return out


def test_only_field_metadata_no_temperature_time_series_is_claimed():
    r=m.audit_rows(synthetic_events())
    assert r["original_event_rows"]==288
    assert r["canopy_trap_height_hypothesis_estimable_from_source_Event_metadata"] is True
    assert r["explicit_numeric_trap_height_by_event_method_layer"]["SLAM|canopy"]["source_rows"]==72
    assert r["explicit_numeric_trap_height_by_event_method_layer"]["SLAM|understorey"]["source_rows"]==72
    assert r["explicit_numeric_event_air_temperature_by_method_layer"]["SLAM|canopy"]["source_rows"]==72
    assert r["source_timeseries_thermal_escape_test_eligible"] is False
    assert r["beetle_occurrence_species_or_abundance_rows_read"]==0
    assert r["all_raw_site_ids_text_coordinates_suppressed"] is True
    r2=m.audit_rows(synthetic_events(height_under=False))
    assert r2["canopy_trap_height_hypothesis_estimable_from_source_Event_metadata"] is False


def test_core_only_reader_ignores_occurrence_extension_and_raw_identifiers():
    fields=["eventID","samplingProtocol","dynamicProperties","decimalLatitude"]
    core=['<archive xmlns="http://rs.tdwg.org/dwc/text/">',
          '<core encoding="UTF-8" fieldsTerminatedBy="\\t" fieldsEnclosedBy="&quot;" ignoreHeaderLines="1" rowType="'+m.EVENT_TYPE+'">',
          '<files><location>event.txt</location></files><id index="0"/>']
    for i,name in enumerate(fields):
        core.append(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{name}"/>')
    core+=['</core>','</archive>']
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.xml","".join(core))
        text=io.StringIO();w=csv.writer(text,delimiter="\t")
        w.writerow(fields)
        w.writerow(["SECRET_EVENT_ID","slam trap (canopy top jar)",'{"trapHeight":21}',"14.21"])
        z.writestr("event.txt",text.getvalue())
        z.writestr("occurrence.txt","scientificName\tindividualCount\nSECRET_BEETLE\t444\n")
    result=m.source_event_rows(buf.getvalue())
    assert len(result)==1
    assert "eventID" not in result[0]
    assert "decimalLatitude" not in result[0]
    assert "SECRET_BEETLE" not in repr(result)
    assert result[0]["dynamicProperties"]=='{"trapHeight":21}'
