"""Bounded forest publisher Event-core parsing: synthetic tests, no network."""
import csv
import importlib.util
import io
import json
import zipfile
from pathlib import Path

FILE = Path(__file__).with_name("audit_publisher_event_core.py")
spec = importlib.util.spec_from_file_location("forest_original_events", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def make_zip(records, *, row_type=m.EVENT_ROW_TYPE, include_location=True):
    fields = ["eventID", "locationID", "parentEventID", "eventDate", "samplingProtocol",
              "habitat", "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters"]
    if not include_location:
        fields.remove("locationID")
    core = [
        '<archive xmlns="http://rs.tdwg.org/dwc/text/">',
        ('<core encoding="UTF-8" fieldsTerminatedBy="\\t" fieldsEnclosedBy="&quot;" '
         f'ignoreHeaderLines="1" rowType="{row_type}">'),
        '<files><location>event.txt</location></files>',
        '<id index="0"/>',
    ]
    for i, field in enumerate(fields):
        core.append(f'<field index="{i}" term="http://rs.tdwg.org/dwc/terms/{field}"/>')
    core += ["</core>", "</archive>"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.xml", "".join(core))
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in records:
            writer.writerow(row)
        z.writestr("event.txt", output.getvalue())
        z.writestr("occurrence.txt", "scientificName\tindividualCount\nSECRET SPECIES\t999\n")
    return buf.getvalue()


def sample_events():
    return [
        dict(eventID="forest-A-2019",locationID="plotA",eventDate="2019-05-18",
             samplingProtocol="tree census",habitat="old-growth forest",
             decimalLatitude="35.10000",decimalLongitude="139.20000",coordinateUncertaintyInMeters="25"),
        dict(eventID="forest-A-2021",locationID="plotA",parentEventID="forest-A-2019",
             eventDate="2021-06-01",samplingProtocol="tree census",habitat="old-growth forest",
             decimalLatitude="35.10000",decimalLongitude="139.20000",coordinateUncertaintyInMeters="25"),
        dict(eventID="forest-B-1997",locationID="plotB",eventDate="1997-07-01",
             samplingProtocol="pitfall",habitat="forest",
             decimalLatitude="36.0",decimalLongitude="140.0"),
    ]


def test_repeated_events_are_not_three_independent_plots():
    output = m.summarize_event_core(make_zip(sample_events()))
    assert output["original_event_core_rows"] == 3
    assert output["distinct_original_eventID_values"] == 3
    assert output["original_distinct_locationID_candidates_NOT_independent_plots"] == 2
    assert output["distinct_parentEventID_references"] == 1
    assert output["parentEventID_references_unresolved_in_core"] == 0
    assert output["rows_with_eventDate_in_2019_2026"] == 2
    assert output["rows_with_coordinateUncertaintyInMeters"] == 2
    assert output["verified_independent_forest_plots"] == 0
    text = json.dumps(output)
    assert "SECRET SPECIES" not in text and "plotA" not in text
    assert "139.2" not in text
    assert output["source_original_occurrence_extension_rows_read"] == 0


def test_missing_location_column_fails_closed():
    try:
        m.summarize_event_core(make_zip(sample_events(), include_location=False))
        assert False
    except ValueError as e:
        assert "location_id" in str(e).lower()


def test_wrong_core_type_fails_closed():
    try:
        m.summarize_event_core(make_zip(sample_events(),row_type="http://rs.tdwg.org/dwc/terms/Occurrence"))
        assert False
    except ValueError as e:
        assert "not_darwin_core_Event" in str(e)


def test_gbif_endpoint_identity_and_security():
    uid="b471e8c8-237a-4444-b2ef-0d5ba1903ead"
    source={"dataset_uuid":uid,"predefined_source_role_NOT_geography_proven":"japan",
            "indexed_occurrence_count_2019_2026_NOT_sites":"100"}
    meta={"key":uid,"type":"SAMPLING_EVENT","title":"Forest survey","license":"CC_BY_4_0",
          "endpoints":[{"type":"DWC_ARCHIVE","url":"https://publisher.example/archive.zip"}]}
    r=m.audit_one(source,get_json=lambda _:meta,download=lambda _:make_zip(sample_events()))
    assert r["status"]=="PUBLISHER_ORIGINAL_EVENT_CORE_VERIFIED_NOT_PLOT_VERIFIED"
    assert r["original_event_core_rows"]==3
    assert r["original_independent_plot_count_verified"]==0
    assert r["original_distinct_locationID_candidates_NOT_independent_plots"]==2
    meta["endpoints"]=[{"type":"DWC_ARCHIVE","url":"http://publisher.example/archive.zip"}]
    stop=m.audit_one(source,get_json=lambda _:meta,download=lambda _:make_zip(sample_events()))
    assert stop["status"]=="ORIGINAL_SOURCE_GATE_STOP"
    assert stop["original_independent_plot_count_verified"]==0


def test_fixed_cohort_and_no_biology_export(tmp_path):
    source=tmp_path/"sources.csv"
    names=["dataset_uuid","predefined_source_role_NOT_geography_proven",
           "source_2020_canopy_alignment_status"]
    with source.open("w",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=names); w.writeheader()
        for i in range(7):
            w.writerow({"dataset_uuid":f"uuid-{i}", "predefined_source_role_NOT_geography_proven":"forest",
                        "source_2020_canopy_alignment_status":"RECENT_OCCURRENCE_CANDIDATE_NOT_SITE_VERIFIED"})
    def fake_meta(url):
        return {"key":url.rsplit("/",1)[-1],"type":"SAMPLING_EVENT","title":"forest","license":"CC0_1_0",
                "endpoints":[{"type":"DWC_ARCHIVE","url":"https://test.example/archive.zip"}]}
    manifest=m.run(source,tmp_path/"out",get_json=fake_meta,download=lambda _:make_zip(sample_events()))
    assert manifest["original_event_core_verified_networks"] == 7
    assert manifest["verified_independent_forest_plots"] == 0
    assert manifest["verbatim_original_occurrence_extensions_opened"] == 0
    exported=(tmp_path/"out"/"original_event_core_network_counts_NOT_plot_counts.csv").read_text()
    assert "SECRET SPECIES" not in exported
    assert "forest-A-2019" not in exported
