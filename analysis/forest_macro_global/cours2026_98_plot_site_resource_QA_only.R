#!/usr/bin/env Rscript
# Only original NONRESPONSE field plot/site/environment source QA.
# Never read beetle Abund fields or compute an ecology effect.
source_objects <- c("data_analy_Pyr_export","data_analy_Bav_export","data_analy_CVL_export")
source_rows <- c(56L,27L,15L)
source_fields <- c(
  "plot","site","Region","salvaged","class_decline_ARCHI","prop_decline",
  "TreMs_div","FDis_TreMs","FDis_DW_diam","FDis_DW_decay",
  "CWM_DW_diam","CWM_DW_decay","CWM_DW_type_substrate",
  "Abund_TreMs_Fon","Abund_TreMs_Injur","Abund_TreMs_Rot_Hole","Abund_TreMs_Saprox"
)
safe_missing <- function(v) {
  if (is.numeric(v)) sum(is.na(v) | !is.finite(v)) else sum(is.na(v) | trimws(as.character(v))=="")
}
if ("--test" %in% commandArgs(trailingOnly=TRUE)) {
  stopifnot(safe_missing(c(NA_real_,3,Inf))==2L)
  stopifnot(safe_missing(c("A","","B"))==1L)
  stopifnot(!any(grepl("^Abund(_|$)",source_fields)))
  cat("COURS2026_SOURCE_NONRESPONSE_ONLY_SOURCE_FIELD_GATES_PASS\n")
  quit(save="no")
}
a <- commandArgs(trailingOnly=TRUE)
if (length(a)!=2L) stop("Source RData and safe output needed")
if (!requireNamespace("jsonlite",quietly=TRUE)) stop("jsonlite missing")
env <- new.env(parent=baseenv())
loaded <- load(a[[1L]],envir=env)
if (!setequal(loaded,source_objects) || length(loaded)!=3L) stop("ORIGINAL_SOURCE_OBJECT_ROSTER_STOP")
res <- list()
schema <- NULL
for (i in seq_along(source_objects)) {
  name <- source_objects[[i]]
  frame <- get(name, envir=env, inherits=FALSE)
  if (!is.data.frame(frame) || nrow(frame)!=source_rows[[i]] || ncol(frame)!=82L)
    stop("ORIGINAL_SOURCE_ANALYSIS_FRAME_SHAPE_STOP")
  if (is.null(schema)) schema <- names(frame)
  if (!identical(schema,names(frame))) stop("SOURCE_CROSS_CONTEXT_FIELDS_DIFFER_STOP")
  if (!all(source_fields %in% names(frame))) stop("SOURCE_PRESPEC_NONRESPONSE_FIELDS_MISSING_STOP")
  site <- as.character(frame[["site"]])
  plot <- as.character(frame[["plot"]])
  region <- as.character(frame[["Region"]])
  nmissing_source_keys <- sum(is.na(site)|trimws(site)=="")+
                          sum(is.na(plot)|trimws(plot)=="")
  valid_idx <- !(is.na(site)|trimws(site)==""|is.na(plot)|trimws(plot)=="")
  key <- paste(site[valid_idx],plot[valid_idx],sep="::")
  site_tab <- table(site[!is.na(site)&trimws(site)!=""])
  b <- frame[["salvaged"]]
  r <- list(
    original_context=c("Pyr","Bav","CVL")[[i]],
    source_rows=nrow(frame),
    original_dataframe_columns=ncol(frame),
    source_site_key_distinct=length(site_tab),
    source_region_key_distinct=length(unique(region[!is.na(region)&trimws(region)!=""])),
    source_plot_key_distinct=length(unique(plot[!is.na(plot)&trimws(plot)!=""])),
    source_composite_site_plot_duplicates=length(key)-length(unique(key)),
    missing_source_site_or_plot_key_cells=as.integer(nmissing_source_keys),
    source_site_plot_count_min=if(length(site_tab)) as.integer(min(site_tab)) else NULL,
    source_site_plot_count_max=if(length(site_tab)) as.integer(max(site_tab)) else NULL,
    source_salvaged_unique_nonmissing_categories=length(unique(as.character(b[!is.na(b)]))),
    original_nonresponse_source_field_missing_counts=as.list(
      setNames(vapply(source_fields, function(n) as.integer(safe_missing(frame[[n]])),integer(1)),source_fields)),
    raw_original_site_plot_region_or_beetle_values_exported=FALSE,
    beetle_response_cells_read=0L
  )
  res[[i]] <- r
}
out <- list(schema="structural.cours2026_original_98plot_site_resource_nonresponse_QA.v1",
            status="SOURCE_ORIGINAL_98ROW_SITE_AND_RESOURCE_QA_ONLY",
            original_source_row_total=sum(source_rows),
            original_context_n=3L,
            original_beetle_species_or_guild_response_cells_read=0L,
            original_new_predictive_scientific_score_count=0L,
            source_site_and_environment_QA=res)
jsonlite::write_json(out,a[[2L]],pretty=TRUE,auto_unbox=TRUE)
cat("COURS2026_SOURCE_ONLY_SITE_HIERARCHY",length(res),sum(source_rows),"\n")
