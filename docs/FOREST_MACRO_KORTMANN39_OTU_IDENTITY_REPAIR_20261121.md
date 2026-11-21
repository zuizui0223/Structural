# Kortmann 39-triplet OTU identity: repair before the first source opening

## Observed failure and exposure ledger

The original frozen protocol remains [the 2026-11-21 preopen specification](FOREST_MACRO_KORTMANN39_OTU_SAMPLE_IDENTITY_PREOPEN_20261121.md). This note records implementation repairs, not a change to its source population or a biodiversity result.

At parent commit `9f43c7f10d5adf89370ce738a81ea67e3c8eaa1a`, both [push run 44847628977](https://github.com/zuizui0223/Structural/actions/runs/44847628977) and [PR run 44847631534](https://github.com/zuizui0223/Structural/actions/runs/44847631534) failed in the synthetic gate. Their original OTU deserialization steps were **skipped**. The push job was `136671128293`; the PR job was `136671138098`. Neither run provides an original OTU identity result.

The faulty fixture removed patch 1 and the last round of patches 2 through 13. Two of those missing rounds belonged to the excluded triplet, leaving **692 retained and 10 excluded** records. The fixed synthetic construction removes the last round of patches **4 through 15**, leaving **690 retained and 12 excluded** records. It also reproduces the already observed 117 retained patches, 105 with six records, 12 with five, and 230 records in each of the three anonymous treatment classes. The observed original source result is unchanged.

## Repairs and fixed limits

1. Recheck the entire already frozen method population, including patch-level record distribution, global treatment consistency, excluded-patch record counts and nonblank method identifiers. Do not accept just the coarse 39/690 totals.
2. Reject automatic `1..702` sample indices in any order. Require the same explicit one-to-one sample identity rules as the preopen specification. Synthetic cases cover direct, permuted and transposed matches; duplicate or missing IDs; ambiguous candidate keys; and private-label output suppression through the actual R-to-Python report boundary.
3. Access dimension labels only on a candidate axis of exactly 702 entries. Noncandidate axes are not accessed. A square 702-by-702 container is held before either axis label accessor, and unsupported objects are not traversed. Only ordinary atomic matrices and plain data frames are admitted; list matrices and unknown classes yield schema HOLD. Plain data frames use the direct `row.names()` accessor because `rownames()` also evaluates the opposite axis through `dimnames.data.frame`. In the anonymous output, a zero label count on a noncandidate axis means **not inspected**, not that the original axis has no names. Zero dimensions for `list`/`other` mean no admitted two-dimensional shape. Shapes beyond the frozen limits are omitted and yield `SOURCE_OTU_OBJECT_SCHEMA_HOLD`; the independent `loaded_otu_object_count` metric preserves how many objects were deserialized.
4. Validate method structure before OTU loading. Persist fixed phase markers immediately before and after `load()`. The wrapper records an attempted/unknown exposure state before launching R, retains the completed deserialization state even if later parsing or shape validation fails, and cannot convert an uncertain exposure back to a claim of unopened evidence. Operational failures remain failures; a scientific HOLD is a completed source gate.
5. Execute the original gate **once locally, after a code-only commit is fixed**, and disable the workflow's original step unconditionally. PRs, dispatches, reruns and later pushes cannot reopen this OTU source through this workflow. Record the immutable source-code commit, script hashes, runtime and execution status beside the anonymous receipt. Do not retry an original opening if its exposure is uncertain. This execution-host change is fixed before opening and changes no scientific admission criterion.

## Execution routing fixed before source access

The current PR's accumulated diff makes ordinary synchronization rerun old source workflows, including live PREDICTS response scoring. Those workflows are outside this audit's sealed scope. Therefore the code-only freeze and the later receipt commits explicitly use `[skip ci]`; the target workflow's live step is disabled in the freeze. All required code verification is performed locally, with networking disabled for tests. No required test is represented as a CI pass, and no merge is planned.

A normal, metadata-only request through the existing authoritative publisher validator succeeded from the local environment; it did not request the original ZIP. The single original command will use the unchanged publisher transport and exact integrity checks, with no proxy workaround, alternate data host or relaxed allowlist. If transport fails before R, record that failure. Do not substitute another data source.

The planned receipt location is `outcome/kortmann39_otu_identity_20261121/receipt.json`. Its adjacent execution record will identify the code-only freeze commit; the receipt will be committed separately afterward, so the source result cannot determine the executed code.

## Timing and effort: primary-text evidence and unresolved crosswalk

The [author paper, sections 2.1, 2.3 and 2.5](https://elib.dlr.de/220269/1/Kortmann_et_al_2025.pdf) describes one Malaise trap per patch, operation from early May through late July 2022, roughly biweekly bottle exchange with varying interval lengths, and six nominal rounds per patch. Its statistical model includes sampling date and an offset for sampling length. The design distinguishes undisturbed reference, disturbed unmanaged, and disturbed cleared/salvage-logged patches.

Those statements do **not** certify a per-bottle date join, the units or transformation of the stored `offset`, or a crosswalk from the serialized treatment values to the paper's categories. The paper's figure letters are not a data codebook. The [prior bounded schema audit](https://github.com/zuizui0223/Structural/actions/runs/44763897159) and [textual author-code audit](https://github.com/zuizui0223/Structural/actions/runs/44762827154) did not establish those joins. The absence of recognized fields is limited to the previous whitelist; it does not prove that no author metadata exists. Supplementary methods were not retrieved in this review.

Even an identity PASS would leave seasonal coverage, effective trap duration and source treatment-code semantics **HOLD**. Before any biological operator, require authoritative sample IDs linked to interval start/end, interruptions or malfunctions, date convention, exposure units and offset transform, plus the treatment-code crosswalk. A total of 702 rows or finite offsets cannot replace these records. The 39-triplet cohort cannot be changed in response to OTU values, and missing rounds cannot be imputed as biological zero.

## Validation and result

The original failed CI and an offline R rerun both reproduce the pre-repair `SOURCE_39_COMPLETE_POPULATION_DRIFT`. The corrected fixture also exposed the old noncandidate-axis access, and a trace on the actual base-R data-frame accessor reproduced `NONCANDIDATE_AXIS_ACCESS` before its repair. Unknown-class and list-matrix fixtures failed before their admission guard was fixed.

After repair, the full repository's normal offline test command passed **1545 tests**, with **6 Shapely-dependent tests skipped**. The root verification reported two warnings: an existing third-party pytest API deprecation and an intentional duplicate-ZIP-member warning in a tamper-detection test. The target Python regressions passed **7 tests**, and the actual R 4.5.0-to-Python synthetic gate passed, including artificial RData save/load phase recording. An independent reviewer re-ran the target checks offline and verified all three review fixes. `git diff --check` passed.

The single original result is not yet known at this code freeze. No original OTU counts, taxon labels, alpha/beta measures or ecological effects are authorized by this repair. The original 40-triplet gate stays HOLD, and PR #469 stays draft and unmerged.
