# Structural v1.248 — Can higher-order donor failure explain the ultrarare island-mammal result?

**Evidence status: response-free applicability audit plus exact known-truth mathematics. No new ecological effect.**

## The biological question and a necessary separation

The earlier 529-species held-out mammal result shows an occupancy-state-dependent predictive signal from geography-derived graph paths. A separate four-donor example demonstrates that, given appropriately overlapping donor sets, higher-order joint source failures could alter recipient-specific potential source loss even after individual and pairwise source behavior match.

**These findings are not the same mechanism.** The current cross-sectional pilot has no repeated donor-state viability histories or measured donor-to-recipient movement/establishment. The higher-order model is not an empirical explanation of the 529-species static prediction result.

## 1. Count the donor order using the existing response-free pilot freeze

Read only development/global_mammals_ultrarare_source_leverage_freeze_v1_122.json, whose population records 529 pilot-defined ultrarare mammal species with 877 mapped pilot positives. Frozen source-count distribution:

| Pilot occupied island count | Species | Fraction of 529 |
|---:|---:|---:|
| 1 | 317 | 59.92% |
| 2 | 116 | 21.93% |
| 3 | 56 | 10.59% |
| 4 | 40 | 7.56% |

Thus **433/529 = 81.85%** have at most two **mapped pilot** source islands. Their records cannot contain a triple-donor cofailure term among those mapped pilot sources. Only **96/529 = 18.15%** have at least three such endpoints, a **necessary but not sufficient** requirement. The exact four-distinct-donor example requires at least four mapped sources and can be contemplated for **at most 40/529 = 7.56%**, before physical eligibility, repeated temporal samples, detection and movement are checked.

Each species has 4,126 held-out island geometry targets. The 433 species account for **1,786,558 of 2,182,654 geometrical species-by-target cells**, but this count is **not** a number of observed occurrences, biological movement events or a reanalysis of held-out predictions.

All counts are conditional on **pilot-derived mapped occupancy**, not total living world populations. An unobserved but biologically real donor might exist outside the sampled pilot; the data cannot rule that out.

**Critical conclusion:** The 529-species global predictive result **cannot be interpreted as evidence that simultaneous loss of three or more observed donor populations is its general driver**. Strong prediction from one mapped source can arise from geography and source location alone. Do not reopen previously consumed mammal held-out labels to search for a favourable 3–4-donor subgroup.

## 2. The current graph cannot instantiate the example's hard-reachability pattern

By frozen code scripts/build_global_mammals_reference_operator_v1_40.py and development/global_mammals_graph_semantics_audit_v1_185.json, the geography-built undirected kNN graph is made connected **within each of 12 bioregions**. Edges are island-centroid constructions, **not measured dispersal routes**.

If a donor is defined **only** as reachable whenever some graph path exists, every recipient inside a given region reaches exactly the same mapped source islands in that region. Recipients from different regions have disjoint sets. Therefore the original illustrative overlap pattern A={1,2,3}, B={1,2,4} is **not obtainable as binary reachability within this graph**. This is a structural proof from graph construction, not a fresh empirical graph-score test.

Crucially, this does **not** make all spatial configuration signals impossible. Original C uses **weighted graph-path distances and source pressure**, not a simple reachable/not reachable indicator. Recipient-specific *effective* movement and establishment probabilities could vary within a connected region. They have not been directly measured here.

## 3. Geographically applicable exact mechanism with all four donors reachable

Retain the originally frozen four-source joint-state distributions in PR #454. For the same four potentially reachable donors, q_ij is the probability that donor j, conditional on being available, supplies at least one successfully establishing colonist to recipient i in a fixed future interval. All probabilities are fixed between donor-dependence worlds; donor successes are conditionally independent given availability. This is a specified toy process, not an inferred dispersal mechanism.

Under these assumptions, the no-establishment probability in world s=±1 is exactly:

**Q_i(s) = product_j(1 − q_ij/2) + (s/16) q_i1 q_i2 (q_i3 − q_i4).**

The two worlds have identical marginal source availability, every pairwise availability, and the entire distribution of how many sources are available. Their sole difference in the recipient endpoint is:

**Q_i(+1) − Q_i(−1) = q_i1 q_i2 (q_i3 − q_i4) / 8.**

Three conditional predictions follow:

1. **Vanishing residual:** If donors 3 and 4 have equal effective delivery probabilities to the recipient, the hidden higher-order contrast is exactly zero in this construction.
2. **Geographic sign reversal:** If donor 3 is more effective at recipient A, but donor 4 more effective at B, the residual has opposite signs. The hard A/B reachability pattern is unnecessary: all four sources may have nonzero probabilities to every recipient.
3. **Weak core donors:** If either donor 1 or donor 2 has very low effective delivery probability, the residual is small even if donors 3 and 4 differ strongly.

Example of two **hypothetical** receiving islands with donor-specific success probabilities ordered as (q1,q2,q3,q4):

| Recipient | Hypothetical probabilities | Q(+1) | Q(−1) | Signed difference |
|---|---|---:|---:|---:|
| A | (0.5,0.5,0.8,0.2) | 0.313125 | 0.294375 | +0.01875 |
| B | (0.5,0.5,0.2,0.8) | 0.294375 | 0.313125 | −0.01875 |

With all four q=0.5, both worlds have **Q=0.75^4=0.31640625** at each recipient: no residual. No empirical q or colonization probabilities have been estimated.

The original v1.247 three-source attenuation q^3/8 is the hard-exclusion special case (q4=0 for one receiver). The all-four-weighted formulation bridges the mathematics to potentially distance-dependent permeability without pretending graph distance is measured colonization.

## 4. Research implications, not premature conservation rankings

This resolves a conceptual mistake: **connectivity-as-proximity, effective dispersal, and joint availability of populations are three separate processes.** The global prediction gain may represent geographical smoothness and source location without any measured immigration.

Previously published work has already shown that assumed landscape-network edges can overpredict realised movement and metapopulation persistence (Fletcher et al. 2011, PNAS, DOI 10.1073/pnas.1107549108).

The strongest current island-biogeographic finding remains **occupancy-dependent role inversion in mapped source information**, not a detected demographic higher-order failure effect. The independent BALA temporal source-loss test did not support additional heldout prediction from lost-source leverage. Balanced source co-coverage in v1.181 likewise did not establish individual source irreplaceability.

Do not imply a monotone effect of island rarity or any universal value of q. Calibrating q_ij requires independently observed recipient-specific movement **and successful establishment**, with suitable sampling and detection denominators.

## 5. Fresh empirical discrimination, before response access

For a new species-by-archipelago time series, freeze the island frame and directed donor-to-recipient eligibility independently of future targets; measure repeated donor viability with detection, observed source-to-recipient movements, recipient habitat/environment and subsequent establishment or survival. Compare to a strong reference containing donor count, marginal and pairwise donor-state dependence, shared environmental events, distance, recipient resources and measured effective delivery probabilities. Add a triple/higher-order donor-state term only when sufficient independent repeated donor states exist. Freeze entire-network/time-block holdouts and estimability gates before target access.

**Do not reopen** the 529 mammal heldout, BALA, Helgeland, Hopson, Gawecka, eBird or consumed validation as fresh. Helgeland has natal movements but no validated reproductive join; Hopson's sample redetection is not verified colonization; Gawecka's sampled detection order is not verified movement order.

## Reproducibility and evidence class

Run: python scripts/higher_order_geometry_applicability_v1_248.py --out /tmp/structural_v1_248.json

The script reads only the committed v1.122 pilot+geometry count spectrum and v1.185 graph-semantics audit; no held-out biological labels. Tests independently enumerate all sixteen source states over the 256-vector exact q grid (512 world-specific evaluations) and check the connected-component access theorem. No new empirical score, cause, source identity ranking or confirmatory system is claimed. **GEB SCIENTIFIC HOLD unchanged.**
