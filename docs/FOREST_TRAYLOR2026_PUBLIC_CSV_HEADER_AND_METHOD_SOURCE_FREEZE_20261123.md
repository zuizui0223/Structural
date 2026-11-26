# Traylor 2026: original 356 deadwood objects, CSV first-header/author-method codebook gate

## Original source authenticated (no organism values opened yet)
Official Zenodo concept DOI 10.5281/zenodo.19206036 resolves to original version **10.5281/zenodo.19206037** (record 19206037). Official API license CC BY 4.0 and open access, source title Data from: Native and non-native ambrosia beetles compete for deadwood resources. The frozen first attempt requiring id 19206036 as a version failed; separate source metadata proof corrected the concept-version ID *before* any original files were downloaded.

Original official three files:
- `ambrosia per deadwood object data.csv` (40,282 B; MD5 586df99f7faded8796d26d4143058883)
- `ambrosia beetle competition script.R` (20,797 B; MD5 05dccb112e503f6436e9fd4641079c8b)
- `READ ME.txt` (1,752 B; MD5 c12653c9488fd7b9254ec4a086ce218b)

Original article Traylor et al. (2026), DOI 10.1098/rspb.2026.1825. Author reports **4 original field studies, 356 deadwood objects, 141 with ambrosia beetles emerging, 23 tree taxa**. The original paper ALREADY tested co-occurrence, native/non-native abundance competition, volume/type/time effects and leave-study-out sensitivity. These are prior art, not Structural discoveries.

## One METHOD-ONLY source gate (not an ecological test)
1. Fetch official published concept record API and resolve *only* exact concept 19206036+version 19206037 pair, CC BY and three-file checksums. Retrieve each publisher-listed official file once, check MD5 and size. No mirrors, alternate file versions or user authentication.
2. Parse exactly **the first line of CSV** to obtain original author field names/delimiter/column count, NOT a single source deadwood object record, species abundance, native proportion, ecological summary or p-value. Output only narrow generic names for study/site/object/tree/wood volume/exposure/month/native/nonnative/abundance/presence keys, plus unidentified header count. Avoid raw species labels or source IDs.
3. Parse original small README and R source as METHOD TEXT ONLY (no R script execution). Record source method import names and generic variable references by whitelist; do not execute models or copy original code. Keep source bytes private in a transient runner; archive only aggregate metadata receipt.
4. If original CSV has no per-object key/study identity and no explicit recorded-zero vs missing sample opportunity grammar, scientific HOLD. A zero count is not necessarily a true absence unless the experiment declares that object was sampled.
5. Do not freeze or fit an ecological contrast until original study/site/sample hierarchy, observed sampled zeros and source response/taxon definition are established. After admission, prospectively fixed **new** leave-study-out predictive ability is the candidate, not replication of authors' GLMM/AIC.
6. Keep previous Cours 3-context object schema result (Pyr56/Bav27/CVL15), prior Ramberg 150-stump zero-catch STOP, Korhonen README HTTP401 and other historical forest/island original scores untouched.

No eBird/TinyFish. PR #469 Draft, main not merged.
