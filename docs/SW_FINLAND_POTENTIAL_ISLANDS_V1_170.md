# SW Finland supplementary source-count projection v1.170

The v1.169 direct inversion returned 0 exact-source species because all 587
archived Historical_total_log values were unresolved under the frozen raw
log10(x+1) inversion. This is consistent with the source paper's statement that
numeric modelling variables were subsequently zero-mean/unit-variance
standardized.

v1.170 therefore activates the already predeclared supplementary
Potential_islands fallback without opening the recent row-level outcome.

The public Ecography supplement contains a 587-species table whose first two
columns are species and Potential_islands. The workflow converts the PDF to temporary bbox XHTML and uses word coordinates to read only the first two species-table columns. It persists only species, Potential_islands, and
historical_source_count = 471 - Potential_islands.

The adjacent published Num_colonized, Prop_colonized and Random_effect values are outside the parsed x-coordinate band: their values are not decoded by the Structural parser, written to the safe lookup/receipt, or used in eligibility.

The extraction must return exactly 587 unique species and pass four frozen
sentinel values. Otherwise it stops and uploads no safe lookup.

This remains t0/source-state work and contributes zero ecological evidence.
