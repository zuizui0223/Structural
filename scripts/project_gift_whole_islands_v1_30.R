#!/usr/bin/env Rscript
# Project metadata-only GIFT output to one row per whole-island entity.
# No species composition is accepted by this stage.

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag) {
  pos <- match(flag, args)
  if (is.na(pos) || pos == length(args)) stop(paste("missing", flag))
  args[[pos + 1]]
}
input <- get_arg("--input")
out_entities <- get_arg("--output-entities")
out_lists <- get_arg("--output-lists")
receipt_path <- get_arg("--receipt")

meta <- utils::read.csv(input, stringsAsFactors = FALSE, check.names = FALSE)
required <- c(
  "entity_ID", "geo_entity", "entity_class", "list_ID", "ref_ID",
  "suit_geo", "taxon_name"
)
missing <- setdiff(required, names(meta))
if (length(missing)) stop(paste("required metadata columns missing:", paste(missing, collapse=",")))

# Fail closed if a species-composition surface somehow entered this artifact.
forbidden <- c(
  "species", "work_species", "work_ID", "genus_ID", "questionable",
  "native", "quest_native", "naturalized", "endemic_ref",
  "endemic_list", "cons_status"
)
bad <- intersect(names(meta), forbidden)
if (length(bad)) stop(paste("species-response columns reached metadata stage:", paste(bad, collapse=",")))

whole <- meta[meta$entity_class == "Island", , drop=FALSE]
if (!nrow(whole)) stop("no whole-island entities remain")
if (any(is.na(whole$entity_ID)) || any(is.na(whole$list_ID))) stop("missing response routing identifier")
if (any(as.character(whole$suit_geo) %in% c("0","FALSE","False","false"))) stop("suit_geo=FALSE survived source query")

whole$entity_ID <- as.character(whole$entity_ID)
whole$list_ID <- as.character(whole$list_ID)
whole$ref_ID <- as.character(whole$ref_ID)

# Preserve every eligible list for future union semantics, but never treat lists
# as independent islands.
lists <- unique(whole[, c("entity_ID","list_ID","ref_ID"), drop=FALSE])
lists <- lists[order(lists$entity_ID, lists$list_ID, lists$ref_ID), , drop=FALSE]

split_lists <- split(lists$list_ID, lists$entity_ID)
split_refs <- split(lists$ref_ID, lists$entity_ID)
entity_names <- tapply(whole$geo_entity, whole$entity_ID, function(x) sort(unique(x))[1])
entities <- data.frame(
  entity_ID = sort(unique(whole$entity_ID)),
  stringsAsFactors = FALSE
)
entities$geo_entity <- unname(entity_names[entities$entity_ID])
entities$n_list_ID <- vapply(entities$entity_ID, function(id) length(unique(split_lists[[id]])), integer(1))
entities$n_ref_ID <- vapply(entities$entity_ID, function(id) length(unique(split_refs[[id]])), integer(1))

dir.create(dirname(out_entities), recursive=TRUE, showWarnings=FALSE)
utils::write.csv(entities, out_entities, row.names=FALSE, quote=TRUE, na="")
utils::write.csv(lists, out_lists, row.names=FALSE, quote=TRUE, na="")

receipt <- list(
  schema="structural.gift_whole_island_projection_result.v1_30",
  status="whole_island_entities_projected_from_metadata_only",
  metadata_rows=nrow(meta),
  metadata_entity_class_counts=as.list(table(meta$entity_class)),
  primary_whole_island_list_rows=nrow(lists),
  primary_whole_island_entities=nrow(entities),
  entities_with_multiple_lists=sum(entities$n_list_ID > 1),
  entities_with_multiple_references=sum(entities$n_ref_ID > 1),
  island_groups_excluded=sum(meta$entity_class == "Island Group"),
  island_parts_excluded=sum(meta$entity_class == "Island Part"),
  species_composition_opened=FALSE,
  species_response_authorized=FALSE,
  counts_as_empirical_evidence=FALSE
)
jsonlite::write_json(receipt, receipt_path, pretty=TRUE, auto_unbox=TRUE)
