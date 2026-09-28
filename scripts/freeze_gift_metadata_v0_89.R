#!/usr/bin/env Rscript

# Freeze GIFT native-angiosperm island checklist metadata without species lists.

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag) {
  pos <- match(flag, args)
  if (is.na(pos) || pos == length(args)) stop(paste("missing", flag))
  args[[pos + 1]]
}

out_csv <- get_arg("--output-metadata")
receipt_path <- get_arg("--receipt")

required <- c("GIFT", "jsonlite", "digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing) > 0) stop(paste("missing R packages:", paste(missing, collapse = ", ")))

pkg_version <- as.character(utils::packageVersion("GIFT"))
if (pkg_version != "1.3.4") {
  stop(paste("unexpected GIFT package version:", pkg_version))
}

res <- GIFT::GIFT_checklists(
  taxon_name = "Angiospermae",
  complete_taxon = TRUE,
  floristic_group = "native",
  complete_floristic = TRUE,
  geo_type = "Island",
  suit_geo = TRUE,
  remove_overlap = FALSE,
  list_set_only = TRUE,
  GIFT_version = "3.2",
  api = "https://gift.uni-goettingen.de/api/extended/"
)

if (!is.list(res) || is.null(res$lists) || !is.data.frame(res$lists)) {
  stop("GIFT metadata-only response did not contain a lists data.frame")
}
if (!is.null(res$checklists) && NROW(res$checklists) > 0) {
  stop("species composition was returned despite list_set_only=TRUE")
}

meta <- res$lists
if (NROW(meta) < 1 || NCOL(meta) < 1) stop("GIFT metadata selection is empty")

# Fail closed if a species-composition surface appears in the metadata object.
forbidden_species_columns <- c(
  "species", "work_species", "work_ID", "orig_ID", "genus_ID",
  "questionable", "quest_native", "naturalized", "endemic_list",
  "cons_status"
)
bad <- intersect(names(meta), forbidden_species_columns)
if (length(bad) > 0) {
  stop(paste("species-composition columns reached metadata surface:", paste(bad, collapse = ",")))
}

# Canonicalize without deriving any biological response summary.
meta <- meta[, sort(names(meta)), drop = FALSE]
meta[] <- lapply(meta, function(x) {
  if (inherits(x, "POSIXt")) return(format(x, tz = "UTC", usetz = TRUE))
  if (is.factor(x)) return(as.character(x))
  x
})

sort_keys <- lapply(meta, function(x) {
  y <- as.character(x)
  y[is.na(y)] <- "<NA>"
  enc2utf8(y)
})
ord_args <- c(sort_keys, list(na.last = TRUE, method = "radix"))
ord <- do.call(order, ord_args)
meta <- meta[ord, , drop = FALSE]
rownames(meta) <- NULL

dir.create(dirname(out_csv), recursive = TRUE, showWarnings = FALSE)
utils::write.table(
  meta,
  file = out_csv,
  sep = ",",
  quote = TRUE,
  qmethod = "double",
  na = "NA",
  row.names = FALSE,
  col.names = TRUE,
  fileEncoding = "UTF-8",
  eol = "\n"
)

sha <- digest::digest(file = out_csv, algo = "sha256", serialize = FALSE)
entity_classes <- if ("entity_class" %in% names(meta)) {
  as.list(sort(table(as.character(meta$entity_class)), decreasing = FALSE))
} else {
  list()
}

receipt <- list(
  schema = "structural.gift_metadata_freeze_result.v0_89",
  status = "metadata_only_native_angiosperm_island_selection_frozen",
  candidate_id = "gift_native_angiosperm_islands_v3_2",
  GIFT_package_version = pkg_version,
  GIFT_database_version_requested = "3.2",
  query = list(
    taxon_name = "Angiospermae",
    complete_taxon = TRUE,
    floristic_group = "native",
    complete_floristic = TRUE,
    geo_type = "Island",
    suit_geo = TRUE,
    remove_overlap = FALSE,
    list_set_only = TRUE
  ),
  metadata_rows = NROW(meta),
  metadata_columns = names(meta),
  entity_class_counts = entity_classes,
  canonical_metadata_sha256 = sha,
  species_composition_requested = FALSE,
  species_composition_rows_returned = if (is.null(res$checklists)) 0L else NROW(res$checklists),
  derived_species_richness_computed = FALSE,
  source_pool_features_computed = FALSE,
  C_minus_R3_computed = FALSE,
  counts_as_empirical_evidence = FALSE,
  pilot_response_authorized = FALSE,
  confirmatory_response_authorized = FALSE,
  next_action = "commit this metadata freeze, then define island/archipelago eligibility without requesting species composition"
)

dir.create(dirname(receipt_path), recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(receipt, receipt_path, pretty = TRUE, auto_unbox = TRUE, null = "null")
cat(jsonlite::toJSON(receipt, pretty = TRUE, auto_unbox = TRUE, null = "null"), "\n")
