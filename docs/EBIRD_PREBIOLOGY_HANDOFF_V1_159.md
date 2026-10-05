# eBird prebiology handoff v1.159

The only unresolved external input for the eBird source-loss candidate is the official checklist-level Sampling Event Data (SED) file.

v1.159 turns the entire response-independent preparation into one command.

## One command after SED download

```bash
python scripts/run_ebird_prebiology_handoff_v1_159.py \
  /path/to/official_sampling_event_data.txt.gz \
  /path/to/USGS_Global_Islands.gpkg \
  --output-dir /path/to/ebird_v159
```

The runner:

1. hashes the untouched official SED and USGS island geometry;
2. runs the v1.157 acquisition handoff and its v1.156 same-byte checklist-support chain;
3. requires the same SED and geometry hashes afterward;
4. uses only the frozen island-year survey-support CSV to run v1.158;
5. freezes the eligible non-overlapping three-wave windows and deterministic burned-pilot/confirmatory partition;
6. verifies that species identity, detections, nondetections, annual occupancy, source-loss events and t2 outcomes all remain unopened.

## What success means

Success means only that the **sampling design exists before biology is opened**.

It does not mean:

- that enough species show source-loss events;
- that persistence/loss classes are estimable;
- that source leverage varies enough to fit the model;
- that source leverage predicts anything.

Those questions belong to the burned-pilot biological gate, which must be frozen separately after the exact v1.159 design is committed.

## Current external action

Obtain the official eBird Basic Dataset **Sampling Event Data** file through the logged-in eBird data-request workflow. Keep the file unchanged.

The Dryad observed-species archive remains closed until v1.159 succeeds and a new species-response firewall is committed.
