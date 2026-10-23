"""Synthetic regression for retrospective MOVECLIM introduced-plant context, no source rows."""
import copy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from azores_MOVECLIM_introduced_pressure_v1_281 import audit_introduced_pressure


def fixture():
    events = []
    obs = []
    for island in ("Pico", "Flores"):
        for plot in range(1, 5):
            for sub in range(1, 5):
                coreid = f"{island}.{plot}.{sub}"
                events.append({
                    "coreid": coreid, "island": island,
                    "locationID": f"{island}.plot{plot}",
                    "eventID": coreid, "year": "2013",
                    "eventDate": "2013-07-15",
                    "minimumElevationInMeters": str(100 * plot),
                })

    def row(isl, p, sub, taxon, status="native", cover="4", rank="species"):
        obs.append({
            "coreid": f"{isl}.{p}.{sub}",
            "scientificName": taxon, "taxonRank": rank,
            "establishmentMeans": status,
            "organismQuantity": cover, "organismQuantityType": "OTV",
        })

    for taxon in ("Alpha alba", "Amber azorica"):
        for p in (1, 3):
            for sub in (1, 3):
                row("Pico", p, sub, taxon, "native")
    for n in ("Beta beta", "Gamma gamma", "Delta delta", "Epsilon epsilon", "Zeta zeta"):
        for p in (2, 4):
            row("Pico", p, 1, n)
    row("Pico", 2, 1, "Alien minor", "introduced", cover="1")
    row("Pico", 3, 2, "Alien minor", "introduced", cover="3")
    row("Pico", 4, 1, "Alien minor", "introduced", cover="5")
    row("Pico", 4, 4, "Alien major", "introduced", cover="6")
    row("Pico", 1, 1, "Uncertain plant", "unknown")
    row("Pico", 1, 1, "Alien unranked", "introduced", rank="genus")
    # All four Flores plots genuinely surveyed, with simple reference incidence.
    row("Flores", 1, 1, "Beta beta", "native")
    losses = [
        {"Species": "Alpha alba", "Archipelago": "Azores", "Island": "Pico",
         "Category": "Well-supported", "Extinction category": "Extirpation (Island level)"},
        {"Species": "Amber azorica", "Archipelago": "Azores", "Island": "São Miguel",
         "Category": "Well-supported", "Extinction category": "Extirpation (Island level)"},
    ]
    return events, obs, losses


def test_intro_context_v281_taxon_group_and_fixed_elevation_halves():
    result = audit_introduced_pressure(*fixture(), expected_plots=8, expected_events=32)
    pico = result["by_island"]["Pico"]
    assert pico["independent_plots"] == 4
    assert pico["focal_native_taxa"] == 2
    assert pico["reference_native_taxa"] == 5
    assert pico["introduced_taxon_plot_positives"] == 4
    assert pico["plots_with_any_introduced_taxon"] == 3
    assert pico["introduced_richness_min"] == 0
    assert pico["introduced_richness_max"] == 2
    assert pico["focal_taxon_plot_positives"] == 4
    assert pico["reference_taxon_plot_positives"] == 10
    assert pico["primary_focal_minus_reference_intro_richness"] == -1
    assert pico["elevation_half_adjusted_focal_minus_reference_intro"] == -1
    assert pico["source_OTV_not_percent_cover"] is True
    assert result["by_island"]["Flores"]["taxon_weighted_comparison_eligible"] is False
    assert result["by_island"]["Flores"]["primary_focal_minus_reference_intro_richness"] is None
    assert result["no_species_names_site_ids_coordinates_or_raw_rows_exported"] is True
    assert result["GEB_scientific_HOLD"]
    assert not result["eBird_used"]
    assert result["confirmatory_systems_admitted"] == 0
    assert "Alpha alba" not in str(result)
    assert "Pico.plot" not in str(result)


def test_invasion_status_and_subplot_collapsing():
    e, o, l = fixture()
    # Introducing a second observation of the same species within the plot
    # changes ordinal cover maximum only, not number of introduced species.
    o.append({**next(x for x in o if x["scientificName"] == "Alien minor"
                     and x["coreid"] == "Pico.2.1"), "coreid": "Pico.2.3",
              "organismQuantity": "9"})
    r = audit_introduced_pressure(e, o, l, expected_plots=8, expected_events=32)
    assert r["by_island"]["Pico"]["introduced_taxon_plot_positives"] == 4
    assert r["by_island"]["Pico"]["primary_focal_minus_reference_intro_richness"] == -1
    assert r["by_island"]["Pico"]["focal_mean_introduced_ordinal_OTV_proxy"] is not None


def test_unmatched_or_duplicate_event_cannot_invent_plot():
    e, o, l = fixture()
    e[1] = {**e[1], "coreid": e[0]["coreid"]}
    try:
        audit_introduced_pressure(e, o, l, expected_plots=8, expected_events=32)
    except ValueError:
        pass
    else:
        raise AssertionError("Repeated source core identifier must fail")


def test_introduction_is_not_causal_claim_or_confirmatory_evidence():
    result = audit_introduced_pressure(*fixture(), expected_plots=8, expected_events=32)
    assert result["source_exposed_retrospective_not_confirmatory"] is True
    assert result["not_invader_causality_or_regional_refugium"] is True
    assert result["not_demographic_rescue_or_natal_dispersal"] is True
    assert result["not_historical_at_risk_island_denominator"] is True
    assert result["other_protected_biological_endpoints_opened"] == 0
