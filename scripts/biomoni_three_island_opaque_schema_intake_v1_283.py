#!/usr/bin/env python3
"""v1.283 BioMonI three-island source intake: ZIP central directory + meta.xml ONLY.

NEVER opens biological Event or Occurrence body, never reads a CSV or TSV
header, never obtains a taxon label or a 0/1 field occurrence. Published sample
counts are source-METADATA claims only, not verified biological denominators.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

SOURCE = "https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7"
DATASET = "eab982cf-81df-4d08-b9f4-c2f5c56b8ad3"
MAX_ZIP_BYTES = 5_000_000
MAX_XML_BYTES = 256_000


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_table(element):
    info = {
        "rowType": element.attrib.get("rowType", ""),
        "encoding": element.attrib.get("encoding", ""),
        "fieldsTerminatedBy": element.attrib.get("fieldsTerminatedBy", ""),
        "ignoreHeaderLines": element.attrib.get("ignoreHeaderLines", ""),
        "id_index_declared": False,
        "coreid_index_declared": False,
        "declared_file_locations": [],
        "declared_field_terms": [],
    }
    for e in element.iter():
        kind = _local(e.tag)
        if kind == "id":
            info["id_index_declared"] |= "index" in e.attrib
        elif kind == "coreid":
            info["coreid_index_declared"] |= "index" in e.attrib
        elif kind == "location" and e.text:
            info["declared_file_locations"].append(e.text.strip())
        elif kind == "field":
            term = e.attrib.get("term", "").rstrip("/").split("/")[-1].split("#")[-1]
            if term:
                info["declared_field_terms"].append(term)
    info["declared_field_terms"] = sorted(set(info["declared_field_terms"]))
    return info


def schema_inventory_from_archive(data: bytes) -> dict:
    result = {
        "schema": "structural.biomoni_three_island_opaque_preflight_result.v1_283",
        "status": "METADATA_STOP_UNCLASSIFIED",
        "source_version": "1.7",
        "source_dataset_uuid": DATASET,
        "archive_sha256": sha256(data).hexdigest(),
        "archive_bytes": len(data),
        "Event_rows_opened": 0,
        "Occurrence_rows_opened": 0,
        "taxon_or_island_values_opened": 0,
        "predictive_effects_scored": 0,
        "new_confirmatory_systems": 0,
        "GEB_scientific_HOLD": True,
        "eBird_used": False,
        "macaronesia_S2_S3_S4_opened": 0,
        "original_mammal_BioTIME_RLS_heldouts_opened": 0,
        "published_event_rows_claimed_not_verified": 30,
        "published_occurrence_rows_claimed_not_verified": 402,
    }
    if len(data) > MAX_ZIP_BYTES:
        raise ValueError("zip exceeds frozen cap")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        entries = z.infolist()
        if not entries or len(entries) > 75:
            raise ValueError("Unexpected original archive entry count")
        paths = [p.filename for p in entries]
        for path in paths:
            name = PurePosixPath(path)
            if name.is_absolute() or ".." in name.parts or path.startswith("\\"):
                raise ValueError("Unsafe archive path")
        meta_names = [n for n in paths if n.lower() == "meta.xml"]
        if len(meta_names) != 1:
            raise ValueError("Exact root meta.xml not present")
        result["archive_entries"] = [
            {"file": e.filename, "compressed_bytes": e.compress_size,
             "uncompressed_bytes": e.file_size, "crc32_hex": f"{e.CRC:08x}"}
            for e in entries
        ]
        info = z.getinfo(meta_names[0])
        if info.file_size > MAX_XML_BYTES:
            raise ValueError("meta.xml exceeds frozen cap")
        # The sole semantically opened original archive member.
        metadata = z.read(meta_names[0])
        if len(metadata) > MAX_XML_BYTES:
            raise ValueError("meta.xml read exceeded frozen cap")
        root = ET.fromstring(metadata)
        core = [e for e in root if _local(e.tag) == "core"]
        ext = [e for e in root if _local(e.tag) == "extension"]
        if len(core) != 1 or not ext:
            raise ValueError("Event/Occurrence meta schema absent")
        core_info = _parse_table(core[0])
        occurrence = [_parse_table(e) for e in ext
                      if _parse_table(e)["rowType"].rstrip("/").endswith("/Occurrence")]
        if not core_info["rowType"].rstrip("/").endswith("/Event") or len(occurrence) != 1:
            raise ValueError("Original archive does not have one Event and one Occurrence role")
        occ_info = occurrence[0]
        declared = core_info["declared_file_locations"] + occ_info["declared_file_locations"]
        if len(declared) != 2 or any(p not in paths for p in declared):
            raise ValueError("Declared Event/Occurrence data locations do not exist")
        result["Event_meta_only"] = core_info
        result["Occurrence_meta_only"] = occ_info
        result["meta_xml_bytes_only"] = len(metadata)
        result["data_files_opened"] = 0
        event_terms = set(core_info["declared_field_terms"])
        occurrence_terms = set(occ_info["declared_field_terms"])
        event_required = {"eventID", "locationID", "island"}
        occ_required = {"scientificName", "establishmentMeans"}
        missing_event = sorted(event_required - event_terms)
        missing_occurrence = sorted(occ_required - occurrence_terms)
        if not core_info["id_index_declared"] or not occ_info["coreid_index_declared"]:
            result["status"] = "STOP_NO_DECLARED_EVENT_OCCURRENCE_CORE_ID_JOIN"
        elif missing_event or missing_occurrence:
            result["status"] = "STOP_REQUIRED_PLOT_OR_NATIVE_ALIEN_STATUS_SCHEMA_MISSING"
        else:
            result["status"] = "METADATA_SCHEMA_POSSIBLE_RESPONSE_SEALED_HOLD"
        result["missing_required_Event_fields"] = missing_event
        result["missing_required_Occurrence_fields"] = missing_occurrence
        result["eligibility_not_yet_known"] = [
            "10 independent author plot identifiers per island cannot be proven without Event values",
            "Complete woody 3-island species census cannot be proven from metadata",
            "Native/introduced status vocabulary not opened or validated",
            "Reunion sampling opportunity is unlike other islands and needs design",
            "At-risk historical local-loss focal species overlap unverified",
        ]
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if (protocol.get("schema") != "structural.biomoni_three_island_response_opaque_intake.v1_283"
            or protocol.get("status") != "PROTOCOL_FROZEN_BEFORE_BIOMONI_ORIGINAL_ARCHIVE_RETRIEVAL"
            or protocol["original_public_source"]["fixed_source_archive_url"] != SOURCE
            or protocol["original_public_source"]["dataset_uuid"] != DATASET):
        raise ValueError("Biological source identity/protocol not frozen")
    result = {
        "schema": "structural.biomoni_three_island_opaque_preflight_result.v1_283",
        "status": "TRANSPORT_STOP_NO_SOURCE_META",
        "source_dataset_uuid": DATASET,
        "Event_rows_opened": 0,
        "Occurrence_rows_opened": 0,
        "taxon_or_island_values_opened": 0,
        "data_files_opened": 0,
        "predictive_effects_scored": 0,
        "new_confirmatory_systems": 0,
        "GEB_scientific_HOLD": True,
        "eBird_used": False
    }
    try:
        req = urllib.request.Request(SOURCE, headers={
            "User-Agent": "Structural-BioMonI-Response-Opaque-Schema-Only-v1.283/1.0"})
        with urllib.request.urlopen(req, timeout=50) as raw:
            data = raw.read(MAX_ZIP_BYTES + 1)
        result = schema_inventory_from_archive(data)
    except Exception as e:
        result["stop_reason"] = str(e)[:300]
        result["stop_type"] = type(e).__name__
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"status":result["status"],
                      "original_archive_sha256":result.get("archive_sha256"),
                      "Event_fields": result.get("Event_meta_only",{}).get("declared_field_terms"),
                      "Occurrence_fields": result.get("Occurrence_meta_only",{}).get("declared_field_terms"),
                      "missing_required_Event_fields":result.get("missing_required_Event_fields"),
                      "missing_required_Occurrence_fields":result.get("missing_required_Occurrence_fields"),
                      "data_files_opened":0, "predictive_effects_scored":0,
                      "stop_reason":result.get("stop_reason")}, sort_keys=True))


if __name__ == "__main__":
    main()
