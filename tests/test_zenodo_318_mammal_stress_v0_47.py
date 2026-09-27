from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from structural.response_quality_attrition import (
    ResponseQualityContractStatus,
    contract_fingerprint,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    evaluate_transition_pilot_protocol,
    protocol_fingerprint,
    protocol_from_mapping,
)
from structural.zenodo_318_mammal_pilot_router import (
    MammalStressPilotRouterError,
    build_zenodo_318_mammal_stress_pilot_surface,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "development/zenodo_318_island_mammals_stress_pilot_protocol_v0_47.json"
QUALITY = ROOT / "development/zenodo_318_island_mammals_stress_quality_contract_v0_47.json"
DESIGN = ROOT / "development/zenodo_318_island_mammals_safe_design_result_v0_47.json"
EVIDENCE = ROOT / "development/zenodo_318_island_mammals_evidence_class_v0_47.json"
SCORING = ROOT / "development/zenodo_318_island_mammals_stress_scoring_contract_v0_47.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _synthetic_workbook(*, bad_pilot_value: str | None = None) -> tuple[bytes, str]:
    species = ["spA", "spB", "spC"]
    headers = ["ID", "Island", "Island_group", *species]
    shared = "".join(f"<si><t>{x}</t></si>" for x in headers)
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + shared
        + "</sst>"
    )

    row4 = "".join(
        f'<c r="{col}4" t="s"><v>{i}</v></c>'
        for i, col in enumerate(["A", "B", "C", "D", "E", "F"])
    )

    def data_row(r: int, island_id: str, vals: tuple[str, str, str], sealed: bool = False) -> str:
        if sealed:
            response = "".join(
                f'<c r="{col}{r}" t="str"><v>BOOM_{col}</v></c>'
                for col in ("D", "E", "F")
            )
        else:
            use = list(vals)
            if bad_pilot_value is not None and island_id == "1":
                use[0] = bad_pilot_value
            response = "".join(
                f'<c r="{col}{r}"><v>{v}</v></c>'
                for col, v in zip(("D", "E", "F"), use)
            )
        return (
            f'<row r="{r}">'
            f'<c r="A{r}"><v>{island_id}</v></c>'
            f'<c r="B{r}"><v>999</v></c>'
            f'<c r="C{r}"><v>999</v></c>'
            f'{response}</row>'
        )

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<dimension ref="A1:F8"/>'
        '<sheetData>'
        '<row r="1"><c r="B1" t="s"><v>0</v></c></row>'
        '<row r="2"><c r="B2" t="s"><v>1</v></c></row>'
        f'<row r="4">{row4}</row>'
        + data_row(5, "1", ("1", "1", "0"))
        + data_row(6, "2", ("1", "1", "1"))
        + data_row(7, "3", ("0", "0", "0"), sealed=True)
        + data_row(8, "4", ("0", "0", "0"), sealed=True)
        + '</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="occurrence" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/sharedStrings.xml", shared_xml)

    digest = hashlib.sha256(("\n".join(species) + "\n").encode()).hexdigest()
    return buf.getvalue(), digest


def test_stress_evidence_class_is_not_fresh_confirmation():
    x = load(EVIDENCE)

    assert x["status"] == (
        "design_frozen_response_summary_exposed_independent_stress_test"
    )
    assert x["raw_species_occurrence_matrix_opened"] is False
    assert x["species_occurrence_values_opened"] == 0
    assert x["exposure"]["occurred_after_safe_design_freeze"] is True
    assert x["exposure"]["occurred_before_species_support_rule_and_pilot_protocol_freeze"] is True
    assert x["counts_as_fresh_confirmation"] is False
    assert x["counts_as_primary_confirmatory_evidence"] is False


def test_stress_design_keeps_frozen_split_and_q75():
    x = load(DESIGN)

    assert x["eligible_model_target_islands"] == 309
    assert len(x["pilot_island_ids"]) == 65
    assert len(x["confirmatory_island_ids"]) == 244
    assert set(x["pilot_island_ids"]).isdisjoint(x["confirmatory_island_ids"])
    assert x["dContinent_quantiles_km"]["q75_primary"] == 1124.41
    assert x["safe_design_sha256"] == (
        "d35a583b9b5fd6b5073db11f25ec9584796ba463f19ac5498b9a41d21aa387db"
    )


def test_stress_pilot_protocol_and_quality_are_bound():
    p = protocol_from_mapping(load(PROTOCOL))
    q = contract_from_mapping(load(QUALITY))

    pd = evaluate_transition_pilot_protocol(p)
    qd = evaluate_response_quality_contract(protocol=p, contract=q)

    assert pd.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT
    assert protocol_fingerprint(p) == (
        "98dd81e471f165303503f88fc02ce6b22c624ea9c2b9a72a635869d047fdba9f"
    )
    assert qd.status is ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
    assert contract_fingerprint(q) == (
        "9b6b61c927ae6e5246821781bb842edcf98dd8dd57d5b63246ba5aeb98f57c2a"
    )
    assert p.pilot_used_for_effect_estimation is False


def test_router_does_not_decode_confirmatory_or_excluded_occurrences():
    raw, species_sha = _synthetic_workbook()
    routed = build_zenodo_318_mammal_stress_pilot_surface(
        workbook_bytes=raw,
        pilot_island_ids=["1", "2"],
        confirmatory_island_ids=["3"],
        expected_sheet_dimension="A1:F8",
        expected_species_headers_sha256=species_sha,
        expected_species_count=3,
        first_data_row=5,
        last_data_row=8,
        minimum_species_support_islands=2,
    )

    assert routed.pilot_species_universe == ("spA", "spB")
    assert routed.pilot_species_universe_count == 2
    assert routed.pilot_islands_opened == 2
    assert routed.pilot_occurrence_values_parsed == 6
    assert routed.confirmatory_occurrence_values_parsed == 0
    assert routed.excluded_occurrence_values_parsed == 0
    assert routed.csv_text == (
        "partition_unit,block,target\n"
        "1,1,1\n"
        "1,1,1\n"
        "2,2,1\n"
        "2,2,1\n"
    )


def test_router_fails_closed_on_nonbinary_opened_pilot_value():
    raw, species_sha = _synthetic_workbook(bad_pilot_value="2")

    with pytest.raises(MammalStressPilotRouterError, match="unexpected pilot occurrence value"):
        build_zenodo_318_mammal_stress_pilot_surface(
            workbook_bytes=raw,
            pilot_island_ids=["1", "2"],
            confirmatory_island_ids=["3"],
            expected_sheet_dimension="A1:F8",
            expected_species_headers_sha256=species_sha,
            expected_species_count=3,
            first_data_row=5,
            last_data_row=8,
            minimum_species_support_islands=2,
        )


def test_scoring_contract_freezes_remote_handoff_estimand():
    x = load(SCORING)

    assert x["training_partition"] == "65 frozen pilot islands only"
    assert x["heldout_partition"] == "244 frozen confirmatory islands only"
    assert x["transformations"]["extreme_q75"] == "dContinent_km >= 1124.41"
    assert x["primary_prediction"] == "negative"
    assert x["uncertainty"]["bootstrap_unit"] == "Archipielago"
    assert x["uncertainty"]["replicates"] == 10000
    assert x["counts_as_fresh_confirmation"] is False
