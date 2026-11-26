#!/usr/bin/env Rscript
# Original CC-BY Cours RData: object/column SCHEMA ONLY. Never inspect data values.
filter_names <- function(x) {
  if (length(x) == 0L) return(character(0))
  pat <- "(site|plot|forest|stand|region|type|year|time|effort|sample|trap|beetle|species|taxon|abund|guild|rich|dead|wood|host|tree|decay|diam|volume|microhab|trem|mort|salvag|declin|disturb|climat|altit|elev|cover|area|density|fung)"
  out <- unique(x[grepl(pat, x, ignore.case=TRUE)])
  head(out, 140L)
}
if ("--test" %in% commandArgs(trailingOnly=TRUE)) {
  stopifnot(identical(filter_names(c("Site_ID","Species_Count","Value")),
                      c("Site_ID","Species_Count")))
  cat("COURS_ORIGINAL_RDATA_SCHEMA_ONLY_SYNTHETIC_PASS\n")
  quit(save="no")
}
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) stop("Source file and output file arguments required")
infile <- args[[1L]]
outfile <- args[[2L]]
if (!requireNamespace("jsonlite", quietly=TRUE)) stop("jsonlite needed")
env <- new.env(parent=baseenv())
obj_names <- load(infile, envir=env)
if (length(obj_names) > 150L) stop("Source object count exceeds safe schema cap")
safe_obj_names <- function(n) {
  if (grepl("^[A-Za-z_.][A-Za-z0-9_.]*$",n)) n else "NON_STANDARD_SOURCE_OBJECT_NAME"
}
summary <- lapply(obj_names, function(n) {
  o <- get(n, envir=env, inherits=FALSE)
  original_class <- class(o)
  if (length(original_class)>5L) original_class <- head(original_class,5L)
  row_dim <- if (is.data.frame(o)||is.matrix(o)) nrow(o) else NULL
  col_dim <- if (is.data.frame(o)||is.matrix(o)) ncol(o) else NULL
  cols <- if (is.data.frame(o)||is.matrix(o)) colnames(o) else NULL
  if (length(cols)>1000L) {
    generic_cols <- character(0)
    excessive <- TRUE
  } else {
    generic_cols <- filter_names(cols)
    excessive <- FALSE
  }
  list(
    safe_object_name=safe_obj_names(n),
    source_R_class=as.character(original_class),
    source_object_dimensional_row_count=row_dim,
    source_object_column_count=col_dim,
    semantic_method_field_names_only=as.character(generic_cols),
    source_column_names_over_1000_count_cap=excessive,
    source_object_numeric_contents_accessed=FALSE,
    sample_identifiers_or_taxa_rows_read=0L
  )
})
out <- list(
  schema="structural.cours2026_original_RData_schema_only.v1",
  original_RData_loaded_schema_not_values=TRUE,
  original_RData_model_fits=0L,
  original_beetle_abundance_or_response_cells_read=0L,
  data_object_count=length(obj_names),
  data_objects=summary,
  status="SOURCE_RDATA_OBJECT_CLASSES_AND_METHOD_FIELDS_ONLY"
)
jsonlite::write_json(out, outfile, pretty=TRUE, auto_unbox=TRUE)
cat("SOURCE_RDATA_SCHEMA_ONLY", length(obj_names), "\n")
