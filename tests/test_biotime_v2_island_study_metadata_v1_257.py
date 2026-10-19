"""Source-free regression for two frozen BioTIME terrestrial-island candidate study IDs."""
import csv
import io
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from biotime_v2_island_study_metadata_v1_257 import audit, COLUMNS

CONTRACT={
 "schema":"structural.biotime_island_study_metadata_admission.v1_257",
 "studied_ids":["373","375"],
 "authority":{"expected_md5":"3daed71ed554888309f9f2443a847bea",
              "canonical_source_doi":"10.5281/zenodo.15222193"}
}

def fake_metadata():
    out=io.StringIO()
    fields=list(COLUMNS)+["CONTACT_1","CONT_1_MAIL"]
    w=csv.DictWriter(out,fieldnames=fields)
    w.writeheader()
    for k in range(1,709):
        study_id="373" if k==373 else ("375" if k==375 else str(1000+k))
        rec={f:"" for f in fields}
        rec.update({
          "STUDY_ID":study_id,
          "REALM":"Terrestrial",
          "TITLE":"recorded title",
          "CEN_LATITUDE":"12.0" if k==373 else ("12.0" if k==375 else "0"),
          "CEN_LONGITUDE":"14" if k==373 else ("15" if k==375 else "0"),
          "METHODS":"*Study Methods*" if k==373 else "",
          "CONTACT_1":"DO_NOT_OUTPUT_SOURCE_CONTACT",
          "CONT_1_MAIL":"secret@invalid.test"})
        w.writerow(rec)
    return out.getvalue().encode()

def test_only_two_approved_original_metadata_studies_are_extracted():
    r=audit(fake_metadata(),CONTRACT)
    assert r["total_unique_studies_in_publisher_metadata"]==708
    assert set(r["chosen_studies"])=={"373","375"}
    assert r["centroid_distance_km"]>100
    assert r["species_or_site_year_responses_read"] is False
    assert r["study_centers_prove_archipelago_independence"] is False
    assert "DO_NOT_OUTPUT_SOURCE_CONTACT" not in str(r)
    assert "secret@invalid.test" not in str(r)

def test_modifying_frozen_target_study_ids_fails_closed():
    bad=dict(CONTRACT,studied_ids=["373","376"])
    try:
        audit(fake_metadata(),bad)
    except ValueError as exc:
        assert "Unanticipated" in str(exc)
    else:
        raise AssertionError("Study IDs must remain fixed before published metadata access")

def test_extra_biological_contact_columns_never_pass_to_output():
    r=audit(fake_metadata(),CONTRACT)
    allowed=set(COLUMNS)
    for study in r["chosen_studies"].values():
        assert set(x for x in study if not x.endswith("_text_truncated"))==allowed
        assert not any("CONTACT" in k or "MAIL" in k for k in study)
