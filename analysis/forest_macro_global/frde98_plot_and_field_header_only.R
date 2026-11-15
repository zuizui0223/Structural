#!/usr/bin/env Rscript
# Source-only Cours 2026 original RData metadata audit. Reads ONLY:
# plot/region/site original row identifiers, original table COLUMN NAMES and
# their classes. Never inspects biological/environmental numeric cell values.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=2L) stop("NEED_ORIGINAL_RDATA_AND_PRIVATE_TSV")
data_path <- args[[1L]]
target <- args[[2L]]
ctx <- new.env(parent=baseenv())
obj_names <- load(data_path,envir=ctx)
if (length(obj_names)!=3L) stop("SOURCE_STOP_ORIGINAL_THREE_CONTEXT_OBJECT_COUNT")
sources <- lapply(obj_names,function(n) get(n,envir=ctx,inherits=FALSE))
size <- vapply(sources,nrow,integer(1L))
if (any(sort(size)!=c(15L,27L,56L))) stop("SOURCE_STOP_ORIGINAL_56_27_15_CONTEXT_GRAIN_DRIFT")
if (!all(vapply(sources,is.data.frame,logical(1L)))) stop("SOURCE_STOP_NON_TABULAR_FOREST_CONTEXT")
if (!all(vapply(sources,ncol,integer(1L))==82L)) stop("SOURCE_STOP_ORIGINAL_82_SOURCE_FIELDS_DRIFT")

resource_pattern <- "(?i)(wood|dead|trem|tree|snag|cav|dbh|diam|volum|decay|fung|injur|expos|substrat)"
disturbance_pattern <- "(?i)(salv|declin|mortal|drought|burn|cut|harvest)"
guild_pattern <- "(?i)(beetl|species|guild|xyl|mycet|abun|rao|fric|fdis|feve|rich|shannon|flori|hill)"
effort_pattern <- "(?i)(trap|effort|method|survey|month|year|duration)"
context_pattern <- "(?i)(^plot$|^site$|^region$|^forest$|coord|lat|lon|alt|elev)"
patterns <- list(resource=resource_pattern,disturbance=disturbance_pattern,
                 response=guild_pattern,effort=effort_pattern,context=context_pattern)
clean_names <- function(x) {
    # Publish only source HEADER labels from a fixed matching vocabulary.
    # Never show individual site/plot/species record values or source taxa.
    y <- x[grepl("^[A-Za-z_][A-Za-z0-9_ .+-]{0,45}$",x)]
    y <- gsub("[^A-Za-z0-9_.+-]","_",y)
    paste(unique(head(y,40L)),collapse=",")
}
keys <- character()
lines <- c(paste(c("slot","rows","columns","distinct_plot","distinct_site",
   "distinct_region","distinct_composite","missing_ID_rows","duplicate_composite",
   "numeric_columns","resource_col_count","disturbance_col_count",
   "response_col_count","effort_col_count","context_col_count",
   "resource_header_names","disturbance_header_names","response_header_names",
   "effort_header_names","context_header_names"),collapse="\t"))
for (i in seq_along(sources)) {
    x <- sources[[i]]
    # The previous source-only schema audit normalized the three field names
    # before displaying them. Locate author columns by CASE-INSENSITIVE exact
    # normalized field names; never choose from values or match on row content.
    normalized_fields <- tolower(gsub("[^A-Za-z0-9]","",names(x)))
    author_field_order <- c("region","site","plot")
    field_index <- match(author_field_order, normalized_fields)
    if (anyNA(field_index) || any(duplicated(field_index)) ||
        any(vapply(author_field_order,function(k) sum(normalized_fields==k)!=1L,logical(1L)))) {
        stop("SOURCE_STOP_REQUIRED_REGION_SITE_PLOT_NAME_NOT_UNIQUE_AFTER_CASE_NORMALIZATION")
    }
    ids <- lapply(x[field_index],as.character)
    names(ids) <- author_field_order
    blank <- vapply(seq_len(nrow(x)),function(k) {
        any(vapply(ids,function(v) is.na(v[k]) || !nzchar(trimws(v[k])),logical(1L)))
    },logical(1L))
    curkey <- paste(ids$region,ids$site,ids$plot,sep="|")
    keys <- c(keys, curkey)
    cnt <- vapply(patterns,function(p) sum(grepl(p,names(x),perl=TRUE)),integer(1L))
    fieldnames <- vapply(patterns,function(p) clean_names(names(x)[grepl(p,names(x),perl=TRUE)]),character(1L))
    lines <- c(lines,paste(c(paste0("obj",i),nrow(x),ncol(x),
        length(unique(ids$plot)),length(unique(ids$site)),length(unique(ids$region)),
        length(unique(curkey)),sum(blank),sum(duplicated(curkey)),
        sum(vapply(x,is.numeric,logical(1L))),unname(cnt),unname(fieldnames)),
        collapse="\t"))
}
writeLines(lines,target,useBytes=TRUE)
cat("SOURCE_COURS_98_PLOT_IDENTIFIER_AND_FIELD_HEADERS_ONLY_AUDITED\n")
cat("SOURCE_COMPOSITE_CONTEXT_KEYS_ACROSS_ALL_98_DISTINCT=",length(unique(keys)),"\n",sep="")
