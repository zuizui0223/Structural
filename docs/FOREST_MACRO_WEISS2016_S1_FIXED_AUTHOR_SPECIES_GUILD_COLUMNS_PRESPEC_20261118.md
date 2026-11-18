# Weiss S1 author-header positional resolution, before species/guild data opening (2026-11-18)

## Frozen antecedent and failure

Original Weiss et al. 2016 PLOS S1 DOC DOI 10.1371/journal.pone.0149506.s001 authenticated 488,960 bytes SHA256 `f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de`. Independently verified OLE→HTML 1 table, 513 rows×9 cells [Actions #44244425857](https://github.com/zuizui0223/Structural/actions/runs/44244425857). First attempt to read original species/guild values [#44245048275](https://github.com/zuizui0223/Structural/actions/runs/44245048275) stopped *before any source data row* because generic `species` matched multiple author headers. A distinct original **header-row-only** [#44245421428](https://github.com/zuizui0223/Structural/actions/runs/44245421428) validated source fields; the pipeline CI later failed on a wrong assertion key only, while the source-only 9-column flags artifact #14401436394 was successfully archived. The actual fixed original nine-column flags by position:
1. **species** (first source column);
2. no prespecified tokens;
3. **family**;
4. no prespecified tokens;
5. **lowland**;
6. **status**;
7. **trophic + guild**;
8. **red + list + status**;
9. **species** (but not the first position).

Thus the initial failed broad selector was specifically ambiguous because **both columns 1 and 9** contain a `species` header token, while only column 7 contains `trophic` + `guild`. No original species row was read, no guild assignment examined, and Gloor Carpathian matrices remain completely unopened. No attempt to choose among different positions based on coverage or favorable ecology is allowed.

## Single, exact author-source parser correction

1. **Fix ORIGINAL taxon columns BEFORE source value access**: original species identity is **1-based source column 1** (required header lexical token `species`), and original trophic guild is **1-based source column 7** (required header lexical tokens **both** `trophic` AND `guild`). Require literal author table shape **513×9**, no span/nested table. Position 9 must remain a DISTINCT source `species`-related column and must NOT be used as the taxon key. No scanning all nine columns for best species validity, no changing parser based on apparent taxa.
2. Reuse the previously frozen six exact guild codes **m,n,p,s,x,z** and exactly the same predeclared binomial grammar, duplicate/conflict handling, missingness and anonymized ledger SHA procedure from [earlier ontology protocol](FOREST_MACRO_WEISS2016_S1_SPECIES_GUILD_ONTOLOGY_EXTRACTION_PRESPEC_20261118.md). Only the *header selector* is changed. Treat invalid binomials or guilds as unclassified, never infer from genus, family, taxonomy alias, original site or nearby code; do not change codes to Franzén's five groups.
3. Output only species-label source validity counts, six-guild histogram, duplicate/invalid counts, unlabelled genus count and SHA256 of in-memory sorted `binomial\tcode` pairs. No raw species names, guild-by-taxon table, original DOC/HTML, PLOS supplemental tables or Gloor taxa counts to leave runner.
4. A successful SOURCE integrity check permits **one separately frozen Gloor original beetle-header-name-only coverage** check after source taxonomy ledger is SHA-verified again. Gloor abundance rows remain untouched; any eventual prediction demands independent stand-level sampling effort and a strong baseline, and original trophic categories must remain fixed.
5. Keep Dryad Weiss own original XLS and unrelated Franzén XLSX **HTTP401 closed**. No extra PLOS mirror/DOI variant, eBird, TinyFish, previous Finland/Chiu/Piccini/BELongDead/PREDICTS/NEON/BALA/GEB re-analysis or PR merge. Draft PR #469 only.

This corrects a source-header ambiguity before original guild information is observed. It is not an ecological endpoint change.
