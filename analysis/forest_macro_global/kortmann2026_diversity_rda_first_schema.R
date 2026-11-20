#!/usr/bin/env Rscript
# Exact Kortmann 2026 diversity_satellite.rda FIRST source schema ONLY.
# R's load() materializes an original response-bearing object IN MEMORY.
# NO original biological value, sample ID, factor level or full R code emitted.

allowed <- c(
  "triplet","treatment","site","siteid","plot","plotid","patch","patchid",
  "sample","sampleid","year","date","period","round","samplinglength",
  "sampling_length","samplingdate","sampling_date","trapdays","duration",
  "effort","foresttype","forest_type","forest","management","disturbance",
  "canopy","openness","sampling_length_days","offset"
)

inspect_one <- function(f) {
  stopifnot(is.character(f), length(f)==1L,
            identical(basename(f),"diversity_satellite.rda"),
            file.exists(f))
  e <- new.env(parent=baseenv())
  keys <- tryCatch(load(f, envir=e), error=function(err) {
    stop("SOURCE_RDA_DESERIALIZATION_FAILED", call.=FALSE)
  })
  if (length(keys) < 1L || length(keys)>16L ||
      anyDuplicated(keys)>0L) {
    stop("SOURCE_RDA_ORIGINAL_OBJECT_COUNT_UNSAFE", call.=FALSE)
  }
  cat("RDA_SCHEMA_V1\t",length(keys),"\n",sep="")
  for (i in seq_along(keys)) {
    x <- get(keys[[i]], envir=e, inherits=FALSE)
    typ <- if (is.data.frame(x)) "data.frame" else
      if (is.matrix(x)) "matrix" else
      if (is.list(x)) "list" else "other"
    nr <- if (typ %in% c("data.frame","matrix")) nrow(x) else 0L
    nc <- if (typ %in% c("data.frame","matrix")) ncol(x) else 0L
    if (length(nr)!=1L || length(nc)!=1L ||
        !is.finite(nr) || !is.finite(nc) ||
        nr<0 || nr>2000000 || nc<0 || nc>100000) {
      stop("SOURCE_RDA_DIMS_UNSAFE", call.=FALSE)
    }
    # Column NAMES only, and ONLY pre-registered exact method-role names
    # ever leave the ephemeral job; biological values are not touched.
    raw_names <- if (typ %in% c("data.frame","matrix")) colnames(x) else NULL
    if (length(raw_names)>100000L) {
      stop("SOURCE_RDA_COLUMN_NAME_COUNT_UNSAFE", call.=FALSE)
    }
    safe <- sort(unique(tolower(raw_names[tolower(raw_names) %in% allowed])))
    if (any(grepl("[^a-z0-9_]",safe))) {
      stop("SOURCE_RDA_ALLOWED_ROLE_NAME_UNSAFE", call.=FALSE)
    }
    cat("OBJECT\t",i,"\t",typ,"\t",nr,"\t",nc,"\t",
        length(raw_names),"\t",paste(safe,collapse=","),"\n",sep="")
  }
  cat("BIOLOGICAL_VALUE_EXPORTS\t0\n")
  cat("SOURCE_RDA_DESERIALIZED_RESPONSE_BEARING_OBJECT\tTRUE\n")
}

args <- commandArgs(trailingOnly=TRUE)
if (length(args)==1L && identical(args[[1]],"--synthetic")) {
  tmp <- tempfile(fileext=".rda")
  fake <- data.frame(
    triplet=c("PRIVATE_ORIGINAL_SAMPLE_ID_A","PRIVATE_ORIGINAL_SAMPLE_ID_B"),
    treatment=c("PRIVATE_TREATMENT_1","PRIVATE_TREATMENT_2"),
    richness=c(999999,888888), stringsAsFactors=FALSE
  )
  save(fake,file=tmp)
  # The basename guard ensures no accidental use of arbitrary original files.
  dest <- file.path(tempdir(),"diversity_satellite.rda")
  file.copy(tmp,dest,overwrite=TRUE)
  inspect_one(dest)
  unlink(c(tmp,dest))
} else if (length(args)==1L) {
  inspect_one(args[[1]])
} else {
  stop("USAGE_SOURCE_RDA_SCHEMA_ONLY",call.=FALSE)
}
