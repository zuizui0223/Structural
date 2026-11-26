# Sihlwald branch-bundle beetles x deadwood: original EnviDat455 source result and scientific boundary (2026-11-24)

## Source verified (not a new ecological beetle effect)

- Original Haeler, Stillhard, Hindenlang Clerc, Pellissier & Lachat (2023 dataset; 2024 JAE DOI 10.1111/1365-2664.14554) original dataset DOI 10.16904/envidat.455, public official EnviDat https://www.envidat.ch/metadata/data-from-dead-wood-distributed-in-different-sized-habitat-patches-enhances-dive .
- Official publisher CKAN package_show one-query source gate [GitHub Actions #45312517170](https://github.com/zuizui0223/Structural/actions/runs/45312517170) technically SUCCESS, anonymous metadata-only artifact **14883827493**, ZIP SHA256 **29b4563e5e29dfba5ea11f6286ede51fbf0d362e5c3065b626feba8e6992afb7**. Dataset active and public, license **CC BY-SA**, version 1.0 and DOI recorded in official data record. Four original author CSV resource IDs and source file sizes:
  - Saproxylic beetle species×bundle abundance matrix, source UUID 1873211d-631c-493e-a998-103395d5de43, **23120 B**.
  - All beetle community species matrix, UUID 30938085-43a4-43f0-bdde-2f57dd557064, **34872 B**.
  - Forest and environmental variables, UUID 66dbaff5-2b06-4e82-9f92-9e40d298f938, **158262 B**.
  - Variable description, UUID 8113973a-149d-4514-8b03-11201870881c, **3005 B**.
  No organism/wood value or source physical ID was opened by metadata gate.
- After separate fixed first-row/actual file header gate, [GitHub Actions #45316362935](https://github.com/zuizui0223/Structural/actions/runs/45316362935) technically SUCCESS but original source SCIENTIFIC/ACCESS status **SOURCE_ORIGINAL_FILE_REDIRECT_DOMAIN_STOP**. Original official resource download URL redirected to a host not whitelisted by the first-row reader, and the reader STOPPED **before reading original file body**. The source original first-row headers, site ID crosswalk and beetle values remain **UNREAD**. This is not an HTTP401 denial, and is NOT a new ecological null. Aggregate-only artifact #14884474607, SHA256 2a42cded628c40651fa2e050be2b3eeabc5fab1b2fe21ce43cdeeae13c4109ca.

## Original physical experiment versus monitoring cohort: verified paper distinction, ID crosswalk still unresolved

The publisher EnviDat dataset description names **69 forest inventory monitoring plots** over 2016–2019. Original JAE Methods DOI 10.1111/1365-2664.14554 explicitly say the actual branch-bundle experiment selected **62 original plots** by stratified random sampling from a network of **503 permanent forest inventory plots**, along local deadwood amount and isolation gradients, and deployed four fresh beech branch bundle patch sizes **1,3,6,12** at different trees in each plot. Branches were field-exposed Dec 2016–Feb 2018 and emerged beetles monitored ex-situ in 2018. Its 12-branch bundles were split into two emergence tubes but remain one source field bundle/patch. So original **experimental physical inference unit is 62 plots nested in ONE Sihlwald forest**; neither 69 catalogue plots nor four nested bundles nor extra tube splits count as independent forests. Source native PlotID×bundle ID still requires exact publisher file key audit; do not assume 62 subset keys or join by row order.

Original authors already studied patch size vs beetle richness/abundance and did community ordinations by branch patch size. Forest resource isolation, amount and light/temperature are relevant but source native fields and comparable original sampled zeros have NOT been verified; a new predictive hold-PLOT species-composition increment would be RETROSPECTIVE within ONE forest, not macroecological regional transport nor time-staggered historic source-pool test.

## Next necessary original source gate

A separately frozen [publisher redirect hostname diagnostic](FOREST_HAELER2023_ENVIDAT455_PUBLISHER_REDIRECT_DIAGNOSTIC_20261124.md) sends one official original file request with redirects DISABLED, reads only 3xx Location scheme/hostname, **0 source body bytes**, and stores no signed URLs, keys, dates or site data. It has a queued Github Actions job #45316759111; status should be checked anew, and a publisher-authenticated storage host explicit erratum is required BEFORE retrying the four original first-row reads. Never bypass a real publisher 401 or login.

Next: only if original four source headers and ID/effort/zero register pass, freeze ONE new out-of-plot species mix predictor beyond baseline patch size/current local wood. Because one Sihlwald is not a regional network, it cannot by itself support the primary structural spatiotemporal resource continuity×independent species source-pool H_ST test; the latter still requires independently replicated programs.

Historical PREDICTS, Finland, German BELongDead, Chiu, Ecuador, Traylor, Ramberg, DATASAPROX source/biotic results and BALA/GEB/mammal protected analyses unchanged. No new original organism ecological effect coefficient/p or taxa rows read. No eBird/TinyFish. Structural PR #469 Draft/unmerged.
