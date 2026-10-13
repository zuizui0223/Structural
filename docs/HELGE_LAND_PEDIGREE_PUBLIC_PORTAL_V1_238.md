# v1.238 — exact same published Dryad 2025 bytes, public portal routes

v1.237 confirmed five Dryad file IDs, original file names, lengths and SHA-256 digests for immutable version **354268**, but its advertised API `/api/v2/files/{id}/download` returned **HTTP 401** without API-account credentials. This is a technical STOP, not a biological mismatch.

Dryad's public website serves file downloads through `/downloads/file_stream/{id}` (modern portal) and historically `/stash/downloads/file_stream/{id}`. Version v1.238 precommits BOTH known public-portal URL templates, pinned IDs, all five sizes and SHA digests **before fetching anything**. One source version and one hash per filename: accepting alternate bytes, versions or source categories is impossible. If neither public web path exposes the exact body, output a technical access STOP rather than improvising an ID matching policy.

With matching bytes this gate decodes **only each tabular file's header** and the author README's variable dictionary. It does not parse a single parental/recruit outcome row. The study is already published (Saatoglu et al. 2025 JAE DOI 10.1111/1365-2656.70049), in the same Helgeland archipelago used for 2021/2026 studies; none of the prior fitness main effects is new to Structural.

Next conditional step, only if v1.238 succeeds: declare an internally linked pedigree record grain, then measure *descriptively* parental natal-island contribution to recorded offspring recipient islands without counting two parents as two offspring; do not infer offspring recruitment island from a mere **last observed** island or biological population rescue.
