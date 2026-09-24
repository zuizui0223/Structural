#!/usr/bin/env python3
"""Freeze a deterministic species-ID pilot/confirmatory split before distribution access."""
from __future__ import annotations

import hashlib
import json

from metadata_census_v0_1 import VERSION, fetch, s

SALT = "structural-gift-pilot-v1"
N_BUCKETS = 5
PILOT_BUCKET = 0
TARGET_TAXON = "Angiospermae"


def fetch_species_metadata():
    rows = []
    metas = []
    for start in range(0, 600000, 100000):
        page, meta = fetch("species", extra={"startat": str(start)})
        rows.extend(page)
        metas.append(meta)
        if len(page) < 100000:
            break
    return rows, metas


def main() -> int:
    if VERSION != "3.2":
        raise RuntimeError(f"partition is frozen for GIFT 3.2, got {VERSION}")

    taxonomy, taxonomy_meta = fetch("taxonomy")
    target = next(row for row in taxonomy if s(row.get("taxon_name")) == TARGET_TAXON)
    left, right = float(target["lft"]), float(target["rgt"])

    genus_ids = set()
    for row in taxonomy:
        if s(row.get("taxon_lvl")) != "genus":
            continue
        lft, rgt = float(row["lft"]), float(row["rgt"])
        if lft >= left and rgt <= right:
            genus_ids.add(s(row["taxon_ID"]))

    species, species_meta = fetch_species_metadata()
    work_ids = sorted(
        {
            int(row["work_ID"])
            for row in species
            if s(row.get("genus_ID")) in genus_ids
        }
    )

    assignments = []
    bucket_counts = {str(i): 0 for i in range(N_BUCKETS)}
    for work_id in work_ids:
        digest = hashlib.sha256(
            f"GIFT{VERSION}|{work_id}|{SALT}".encode("utf-8")
        ).hexdigest()
        bucket = int(digest[:16], 16) % N_BUCKETS
        bucket_counts[str(bucket)] += 1
        assignments.append((work_id, bucket))

    pilot = [work_id for work_id, bucket in assignments if bucket == PILOT_BUCKET]
    confirmatory = [work_id for work_id, bucket in assignments if bucket != PILOT_BUCKET]

    def sha(value) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    payload = {
        "schema": "structural.gift_species_partition.v0_1",
        "status": "response_blind_species_partition_frozen",
        "gift_version": VERSION,
        "target_taxon": TARGET_TAXON,
        "species_distribution_accessed": False,
        "partition_axis": "GIFT work_ID deterministic hash bucket",
        "hash_rule": f"SHA256('GIFT{VERSION}|<work_ID>|{SALT}') first_64_bits mod {N_BUCKETS}",
        "pilot_bucket": PILOT_BUCKET,
        "confirmatory_buckets": [1, 2, 3, 4],
        "n_angiosperm_work_ids": len(work_ids),
        "n_pilot_work_ids": len(pilot),
        "n_confirmatory_work_ids": len(confirmatory),
        "bucket_counts": bucket_counts,
        "angiosperm_work_id_set_sha256": sha(work_ids),
        "assignment_sha256": sha(assignments),
        "pilot_work_id_set_sha256": sha(pilot),
        "confirmatory_work_id_set_sha256": sha(confirmatory),
        "taxonomy_source": taxonomy_meta,
        "species_metadata_sources": species_meta,
        "pilot_predictive_denominator_contribution": 0,
        "confirmatory_response_authorized": False,
    }
    payload["receipt_sha256"] = sha(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
