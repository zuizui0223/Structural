from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/project_global_mammals_appendix2_safe_rows_v1_23.py"
CONTRACT = ROOT / "development/global_mammals_appendix2_safe_rows_contract_v1_23.json"
FIREWALL = ROOT / "development/global_mammals_appendix2_column_firewall_v1_22.json"

HEADERS = [
    "ID",
    "Island_name",
    "CountryISO",
    "Longitude_centroid",
    "Latitude_centroid",
    "Area",
    "Current_isolation",
    "Past_isolation",
    "Climate_velocity",
    "Temperature_mean",
    "Temperature_sd",
    "Precipitation_mean",
    "Precipitation_sd",
    "Elevation_sd",
    "Richness_mammal",
    "Richness_bat",
    "Richness_nonVol",
    "SIE_mammal",
    "SIE_bats",
    "SIE_nonVol",
    "pSIE_mammal",
    "pSIE_bats",
    "pSIE_nonVol",
    "bioregion",
    "bioregion_SIE",
]


def load_module():
    spec = importlib.util.spec_from_file_location("global_mammals_v123", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _col(n: int) -> str:
    out = ""
    n += 1
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(ord("A") + rem) + out
    return out


def _header_sha(values):
    return hashlib.sha256(
        "".join(f"{value}\n" for value in values).encode("utf-8")
    ).hexdigest()


def synthetic_xlsx(path: Path):
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="table_s1" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
  Target="worksheets/sheet1.xml"/>
</Relationships>"""
    header_cells = "".join(
        f'<c r="{_col(i)}1" t="s"><v>{i}</v></c>'
        for i in range(len(HEADERS))
    )

    safe_numeric = {
        "Longitude_centroid": "-105.25",
        "Latitude_centroid": "55.75",
        "Area": "12.5",
        "Current_isolation": "3.0",
        "Past_isolation": "4.0",
        "Climate_velocity": "0.5",
        "Temperature_mean": "9.0",
        "Temperature_sd": "1.5",
        "Precipitation_mean": "800",
        "Precipitation_sd": "20",
        "Elevation_sd": "30",
    }

    def data_row(row_number: int, id_value: str, realm_index: int):
        cells = []
        for i, header in enumerate(HEADERS):
            ref = f"{_col(i)}{row_number}"
            if header == "ID":
                cells.append(f'<c r="{ref}"><v>{id_value}</v></c>')
            elif header == "bioregion":
                cells.append(f'<c r="{ref}" t="s"><v>{realm_index}</v></c>')
            elif header in safe_numeric:
                cells.append(
                    f'<c r="{ref}"><v>{safe_numeric[header]}</v></c>'
                )
            elif header in {"Island_name", "CountryISO"}:
                cells.append(f'<c r="{ref}" t="s"><v>27</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="s"><v>28</v></c>')
        return f'<row r="{row_number}">' + "".join(cells) + "</row>"

    sheet = (
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <sheetData>
  <row r="1">"""
        + header_cells
        + "</row>"
        + data_row(2, "101", 25)
        + data_row(3, "102", 26)
        + """
 </sheetData>
</worksheet>"""
    )

    shared_entries = [
        f"<si><t>{h}</t></si>".encode("utf-8")
        for h in HEADERS
    ]
    shared_entries += [
        b"<si><t>RealmA</t></si>",
        b"<si><t>RealmB</t></si>",
        b"<si><t>\xff\xfeCLOSED_SECRET</t></si>",
        b"<si><t>\xff\xfePROTECTED_SECRET</t></si>",
    ]
    shared = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + b"".join(shared_entries)
        + b"</sst>"
    )
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
</Types>"""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
        zf.writestr("xl/sharedStrings.xml", shared)


def synthetic_contract(path: Path):
    x = load(CONTRACT)
    x["source"] = dict(x["source"])
    x["source"]["expected_size_bytes"] = path.stat().st_size
    x["source"]["expected_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    x["source"]["expected_header_sha256"] = _header_sha(HEADERS)
    x["source"]["expected_data_row_count"] = 2
    return x


def test_contract_projects_only_13_prospectively_safe_columns():
    x = load(CONTRACT)
    assert len(x["safe_columns_in_source_order"]) == 13
    assert x["closed_unneeded_columns_in_source_order"] == [
        "Island_name",
        "CountryISO",
    ]
    assert len(x["protected_response_derived_columns_in_source_order"]) == 10
    assert x["xlsx_firewall"]["closed_unneeded_cell_values_decoded_required"] == 0
    assert x["xlsx_firewall"][
        "protected_response_derived_cell_values_decoded_required"
    ] == 0
    assert x["evidence_boundary"]["Appendix_1_response_file_reopened"] is False
    assert x["evidence_boundary"]["fresh_system_denominator_contribution"] == 0


def test_safe_projection_ignores_invalid_utf8_closed_and_protected_values(tmp_path: Path):
    module = load_module()
    xlsx = tmp_path / "Appendix_2-dryad.xlsx"
    synthetic_xlsx(xlsx)

    csv_text, receipt = module.project_safe_rows(
        xlsx,
        contract=synthetic_contract(xlsx),
        firewall=load(FIREWALL),
    )

    assert receipt["status"] == "APPENDIX2_5592_SAFE_ROWS_PROJECTED"
    assert receipt["row_count"] == 2
    assert receipt["distinct_id_count"] == 2
    assert receipt["safe_column_count"] == 13
    assert receipt["closed_unneeded_cell_values_decoded"] == 0
    assert receipt["protected_response_derived_cell_values_decoded"] == 0
    assert receipt["Appendix_1_response_file_reopened"] is False
    assert receipt["biological_response_values_opened_in_v1_23"] is False
    assert receipt["fresh_system_denominator_contribution"] == 0
    assert all(value == 0 for value in receipt["null_counts"].values())

    assert "CLOSED_SECRET" not in csv_text
    assert "PROTECTED_SECRET" not in csv_text
    rows = list(csv.reader(io.StringIO(csv_text)))
    assert rows[0] == load(CONTRACT)["safe_columns_in_source_order"]
    assert rows[1][0] == "101"
    assert rows[2][0] == "102"
    assert rows[1][-1] == "RealmA"
    assert rows[2][-1] == "RealmB"
    assert rows[1][1] == float(-105.25).hex()
    assert rows[1][2] == float(55.75).hex()


def test_safe_csv_is_deterministic(tmp_path: Path):
    module = load_module()
    xlsx = tmp_path / "Appendix_2-dryad.xlsx"
    synthetic_xlsx(xlsx)
    contract = synthetic_contract(xlsx)
    firewall = load(FIREWALL)
    csv1, receipt1 = module.project_safe_rows(
        xlsx, contract=contract, firewall=firewall
    )
    csv2, receipt2 = module.project_safe_rows(
        xlsx, contract=contract, firewall=firewall
    )
    assert csv1 == csv2
    assert receipt1 == receipt2


def test_duplicate_safe_ID_fails_closed(tmp_path: Path):
    module = load_module()
    xlsx = tmp_path / "Appendix_2-dryad.xlsx"
    synthetic_xlsx(xlsx)
    raw = xlsx.read_bytes()
    # Keep this test at the row-projection layer by rewriting the generated
    # worksheet member only.
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zin:
        members = {n: zin.read(n) for n in zin.namelist()}
    members["xl/worksheets/sheet1.xml"] = members[
        "xl/worksheets/sheet1.xml"
    ].replace(b"<v>102</v>", b"<v>101</v>", 1)
    with zipfile.ZipFile(xlsx, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, payload in members.items():
            zout.writestr(name, payload)
    contract = synthetic_contract(xlsx)

    try:
        module.project_safe_rows(
            xlsx,
            contract=contract,
            firewall=load(FIREWALL),
        )
    except module.GlobalMammalSafeRowsError as exc:
        assert "not unique" in str(exc)
    else:
        raise AssertionError("duplicate ID did not fail closed")
