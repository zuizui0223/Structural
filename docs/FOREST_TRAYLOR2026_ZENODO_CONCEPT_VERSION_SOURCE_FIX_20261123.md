# Traylor 2026 original Zenodo concept versus version DOI: response-blind correction

The first frozen metadata gate to user-cited Zenodo concept DOI 10.5281/zenodo.19206036 stopped at SOURCE_PUBLISHER_ID_OR_DOI_MISMATCH_STOP and read ZERO original source files/biology. Subsequent **source metadata-only original author Zenodo API** run (GitHub Actions #45078398775) revealed a legitimate *concept DOI / version DOI distinction*:

- Original article cites **concept DOI 10.5281/zenodo.19206036** and public route /api/records/19206036.
- The official Zenodo API resolves that concept to **version record ID 19206037** and **version DOI 10.5281/zenodo.19206037**.
- Official returned conceptrecid=19206036, conceptdoi=10.5281/zenodo.19206036, public access=open, license id=cc-by-4.0; title **Data from: Native and non-native ambrosia beetles compete for deadwood resources**.

**One narrowly scoped correction (pre-original-data opening):** accept only the exact pair (returned record 19206037, version DOI 10.5281/zenodo.19206037) AND (concept record 19206036, concept DOI 10.5281/zenodo.19206036). Any other ID/DOI/status => SOURCE STOP. Permit one exact publisher official metadata file list response; NO data file downloads, species/wood source rows, effect calculation or external paper scoring.

This is an identifier repair, not cherry-picked file version based on results. Original study Traylor et al. 2026 DOI 10.1098/rspb.2026.1825 includes 356 experimental deadwood objects from 4 original field studies with sampled beetle records, but the existing paper already analyzed resource overlap, competition, native share and leave-study-out sensitivity. Only a prospectively separate **out-of-study predictive** question with source opportunity/effort and valid field-study codebook could add new Structural evidence.

Prior Ramberg2026 scientific zero-catch STOP, Korhonen2024 original file access HTTP401, Finland, Ecuador, PREDICTS, BALA/GEB/mammal sealed states unchanged. No eBird/TinyFish; Draft PR #469.
