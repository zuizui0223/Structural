"""Response-blind qualification audits for M3 genetic and M4 environmental mechanism lanes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


M3 = "M3_historical_colonization_legacy"
M4 = "M4_environmental_proxy"


@dataclass(frozen=True)
class GeneticPopulation:
    population_id: str
    block: str
    role: str
    sample_n: int

    def __post_init__(self) -> None:
        if not self.population_id.strip():
            raise ValueError("population_id must be non-empty")
        if not self.block.strip():
            raise ValueError("block must be non-empty")
        if self.role not in {"focal", "source", "both"}:
            raise ValueError("role must be focal/source/both")
        if isinstance(self.sample_n, bool) or not isinstance(self.sample_n, int):
            raise ValueError("sample_n must be integer")
        if self.sample_n < 0:
            raise ValueError("sample_n must be >=0")


@dataclass(frozen=True)
class GeneticSourcePair:
    focal_population: str
    source_population: str
    comparison_class: str

    def __post_init__(self) -> None:
        if not self.focal_population.strip() or not self.source_population.strip():
            raise ValueError("genetic pair population ids must be non-empty")
        if self.focal_population == self.source_population:
            raise ValueError("genetic pair may not compare a population to itself")
        if self.comparison_class not in {"graph_connected", "alternative"}:
            raise ValueError(
                "comparison_class must be graph_connected or alternative"
            )


@dataclass(frozen=True)
class GeneticFocalAudit:
    focal_population: str
    block: str
    sample_n: int
    eligible_graph_connected_sources: int
    eligible_alternative_sources: int
    qualified: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class GeneticQualificationAudit:
    total_populations: int
    focal_population_count: int
    source_population_count: int
    eligible_source_population_count: int
    eligible_focal_population_count: int
    eligible_focal_blocks: int
    focal_audits: tuple[GeneticFocalAudit, ...]
    qualified: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EnvironmentPredictorAudit:
    predictor: str
    nonmissing_rows: int
    nonmissing_fraction: float
    unique_values: int
    qualified: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EnvironmentQualificationAudit:
    total_rows: int
    unique_units: int
    blocks: int
    blocks_with_minimum_complete_rows: int
    predictor_audits: tuple[EnvironmentPredictorAudit, ...]
    qualified: bool
    reasons: tuple[str, ...]


def audit_genetic_sampling_design(
    populations: Iterable[GeneticPopulation],
    pairs: Iterable[GeneticSourcePair],
    *,
    minimum_sample_n_focal: int,
    minimum_sample_n_source: int,
    minimum_eligible_focal_populations: int,
    minimum_eligible_source_populations: int,
    minimum_focal_blocks: int,
    minimum_graph_connected_sources_per_focal: int,
    minimum_alternative_sources_per_focal: int,
) -> GeneticQualificationAudit:
    minima = {
        "minimum_sample_n_focal": minimum_sample_n_focal,
        "minimum_sample_n_source": minimum_sample_n_source,
        "minimum_eligible_focal_populations": minimum_eligible_focal_populations,
        "minimum_eligible_source_populations": minimum_eligible_source_populations,
        "minimum_focal_blocks": minimum_focal_blocks,
        "minimum_graph_connected_sources_per_focal":
            minimum_graph_connected_sources_per_focal,
        "minimum_alternative_sources_per_focal":
            minimum_alternative_sources_per_focal,
    }
    for label, value in minima.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{label} must be integer >=1")

    pops = tuple(populations)
    pair_rows = tuple(pairs)
    by_id: dict[str, GeneticPopulation] = {}
    for pop in pops:
        if pop.population_id in by_id:
            raise ValueError(f"duplicate population_id: {pop.population_id}")
        by_id[pop.population_id] = pop

    focal_ids = {
        pop.population_id
        for pop in pops
        if pop.role in {"focal", "both"}
    }
    source_ids = {
        pop.population_id
        for pop in pops
        if pop.role in {"source", "both"}
    }
    if not focal_ids:
        raise ValueError("genetic design contains no focal populations")
    if not source_ids:
        raise ValueError("genetic design contains no source populations")

    seen_pairs: set[tuple[str, str, str]] = set()
    connected: dict[str, set[str]] = {pid: set() for pid in focal_ids}
    alternative: dict[str, set[str]] = {pid: set() for pid in focal_ids}
    for pair in pair_rows:
        key = (
            pair.focal_population,
            pair.source_population,
            pair.comparison_class,
        )
        if key in seen_pairs:
            raise ValueError(f"duplicate genetic source pair: {key}")
        seen_pairs.add(key)
        if pair.focal_population not in focal_ids:
            raise ValueError(
                f"pair focal is not declared focal population: "
                f"{pair.focal_population}"
            )
        if pair.source_population not in source_ids:
            raise ValueError(
                f"pair source is not declared source population: "
                f"{pair.source_population}"
            )
        target = (
            connected
            if pair.comparison_class == "graph_connected"
            else alternative
        )
        target[pair.focal_population].add(pair.source_population)

    eligible_source_ids = {
        pid
        for pid in source_ids
        if by_id[pid].sample_n >= minimum_sample_n_source
    }

    focal_audits: list[GeneticFocalAudit] = []
    for pid in sorted(focal_ids):
        pop = by_id[pid]
        connected_ok = connected[pid] & eligible_source_ids
        alternative_ok = alternative[pid] & eligible_source_ids
        reasons: list[str] = []
        if pop.sample_n < minimum_sample_n_focal:
            reasons.append("insufficient_focal_sample_n")
        if len(connected_ok) < minimum_graph_connected_sources_per_focal:
            reasons.append("insufficient_graph_connected_sources")
        if len(alternative_ok) < minimum_alternative_sources_per_focal:
            reasons.append("insufficient_alternative_sources")
        focal_audits.append(
            GeneticFocalAudit(
                focal_population=pid,
                block=pop.block,
                sample_n=pop.sample_n,
                eligible_graph_connected_sources=len(connected_ok),
                eligible_alternative_sources=len(alternative_ok),
                qualified=not reasons,
                reasons=tuple(reasons),
            )
        )

    eligible_focals = [row for row in focal_audits if row.qualified]
    blocks = {row.block for row in eligible_focals}
    reasons: list[str] = []
    if len(eligible_focals) < minimum_eligible_focal_populations:
        reasons.append("insufficient_eligible_focal_populations")
    if len(eligible_source_ids) < minimum_eligible_source_populations:
        reasons.append("insufficient_eligible_source_populations")
    if len(blocks) < minimum_focal_blocks:
        reasons.append("insufficient_eligible_focal_blocks")

    return GeneticQualificationAudit(
        total_populations=len(pops),
        focal_population_count=len(focal_ids),
        source_population_count=len(source_ids),
        eligible_source_population_count=len(eligible_source_ids),
        eligible_focal_population_count=len(eligible_focals),
        eligible_focal_blocks=len(blocks),
        focal_audits=tuple(focal_audits),
        qualified=not reasons,
        reasons=tuple(reasons),
    )


def audit_environment_predictor_support(
    rows: Iterable[dict[str, object]],
    *,
    predictors: Iterable[str],
    minimum_units: int,
    minimum_blocks: int,
    minimum_nonmissing_fraction: float,
    minimum_unique_values: int,
    minimum_complete_rows_per_block: int,
    minimum_blocks_with_complete_rows: int,
) -> EnvironmentQualificationAudit:
    predictor_names = tuple(predictors)
    if not predictor_names:
        raise ValueError("at least one enriched environment predictor is required")
    if len(predictor_names) != len(set(predictor_names)):
        raise ValueError("enriched environment predictors contain duplicates")
    for name in predictor_names:
        if not name.strip():
            raise ValueError("environment predictor names must be non-empty")

    integer_minima = {
        "minimum_units": minimum_units,
        "minimum_blocks": minimum_blocks,
        "minimum_unique_values": minimum_unique_values,
        "minimum_complete_rows_per_block": minimum_complete_rows_per_block,
        "minimum_blocks_with_complete_rows": minimum_blocks_with_complete_rows,
    }
    for label, value in integer_minima.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{label} must be integer >=1")
    if (
        isinstance(minimum_nonmissing_fraction, bool)
        or not isinstance(minimum_nonmissing_fraction, (int, float))
        or not (0 < float(minimum_nonmissing_fraction) <= 1)
    ):
        raise ValueError("minimum_nonmissing_fraction must be in (0,1]")

    data = tuple(rows)
    if not data:
        raise ValueError("environment predictor table is empty")

    seen_units: set[str] = set()
    block_counts_complete: dict[str, int] = {}
    values: dict[str, list[float]] = {name: [] for name in predictor_names}
    blocks: set[str] = set()

    for row in data:
        unit = str(row.get("unit_id") or "").strip()
        block = str(row.get("block") or "").strip()
        if not unit:
            raise ValueError("environment row has empty unit_id")
        if not block:
            raise ValueError("environment row has empty block")
        if unit in seen_units:
            raise ValueError(f"duplicate environment unit_id: {unit}")
        seen_units.add(unit)
        blocks.add(block)

        complete = True
        for name in predictor_names:
            raw = row.get(name)
            if raw is None:
                complete = False
                continue
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise ValueError(
                    f"environment predictor {name} must be numeric or missing"
                )
            value = float(raw)
            if value != value or value in {float("inf"), float("-inf")}:
                complete = False
                continue
            values[name].append(value)
        if complete:
            block_counts_complete[block] = block_counts_complete.get(block, 0) + 1

    predictor_audits: list[EnvironmentPredictorAudit] = []
    for name in predictor_names:
        nonmissing = len(values[name])
        fraction = nonmissing / len(data)
        unique = len(set(values[name]))
        reasons: list[str] = []
        if fraction < minimum_nonmissing_fraction:
            reasons.append("insufficient_nonmissing_fraction")
        if unique < minimum_unique_values:
            reasons.append("insufficient_unique_values")
        predictor_audits.append(
            EnvironmentPredictorAudit(
                predictor=name,
                nonmissing_rows=nonmissing,
                nonmissing_fraction=fraction,
                unique_values=unique,
                qualified=not reasons,
                reasons=tuple(reasons),
            )
        )

    blocks_complete = sum(
        count >= minimum_complete_rows_per_block
        for count in block_counts_complete.values()
    )
    reasons: list[str] = []
    if len(data) < minimum_units:
        reasons.append("insufficient_units")
    if len(blocks) < minimum_blocks:
        reasons.append("insufficient_blocks")
    if blocks_complete < minimum_blocks_with_complete_rows:
        reasons.append("insufficient_blocks_with_complete_environment_rows")
    if any(not row.qualified for row in predictor_audits):
        reasons.append("one_or_more_environment_predictors_fail_support")

    return EnvironmentQualificationAudit(
        total_rows=len(data),
        unique_units=len(seen_units),
        blocks=len(blocks),
        blocks_with_minimum_complete_rows=blocks_complete,
        predictor_audits=tuple(predictor_audits),
        qualified=not reasons,
        reasons=tuple(reasons),
    )
