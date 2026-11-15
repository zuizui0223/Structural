#!/usr/bin/env Rscript
# SOURCE-ONLY original RData object metadata. NEVER evaluate original author Rmd
# or read individual tree/plot/beetle outcome values.
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) stop("NEED_PRIVATE_RDATA_AND_METADATA_TSV")
input <- args[[1L]]
output <- args[[2L]]
e <- new.env(parent=baseenv())
objs <- load(input, envir=e)
if (length(objs) < 1L || length(objs) > 200L) stop("SOURCE_OBJECT_COUNT_OUT_OF_RANGE")

whitelist <- c(
  "plot", "plotid", "site", "siteid", "stand", "standid", "forest", "forestid",
  "foresttype", "context", "region", "regionid", "location", "year",
  "samplingyear", "samplingdate", "date", "trap", "trapid", "traptype",
  "ntraps", "effort", "management", "salvage", "salvagelogging", "decline",
  "mortality", "deadwood", "deadwoodvolume", "standingdeadwood",
  "lyingdeadwood", "decay", "decaystage", "dbh", "diameter",
  "basalarea", "tree", "treespecies", "treem", "trems", "microhabitat",
  "substrate", "subtype", "treatment", "elevation", "altitude",
  "guild", "feedingguild", "trait", "traitguild", "beetle",
  "abundance", "speciesrichness", "species", "taxon"
)
norm <- function(x) tolower(gsub("[^A-Za-z0-9]", "", x))
cleanclass <- function(x) {
  y <- gsub("[^A-Za-z0-9_.+-]", "", paste(class(x), collapse="+"))
  substr(y, 1L, 80L)
}
find_generic <- function(x) {
  n <- names(x)
  if (is.null(n)) return("")
  good <- unique(norm(n)[norm(n) %in% whitelist])
  if (length(good) > 50L) good <- good[seq_len(50L)]
  paste(good, collapse=",")
}
fmt <- function(x) {
  d <- dim(x)
  if (is.null(d) || length(d) < 2L) return(c("NA","NA"))
  as.character(d[1:2])
}
safe_row <- function(slot,x) {
  d <- fmt(x)
  paste(slot,cleanclass(x),d[[1L]],d[[2L]],find_generic(x),sep="\t")
}
rows <- c("object_slot\tclass\trows\tcolumns\tgeneric_fields")
# Object names may carry original taxon/source identifiers. We do not export
# any names or slot-to-original-name mappings.
for (i in seq_along(objs)) {
  x <- get(objs[[i]], envir=e, inherits=FALSE)
  rows <- c(rows, safe_row(paste0("obj",i), x))
  if (is.list(x) && !is.data.frame(x)) {
    lim <- min(length(x), 24L)
    if (lim > 0L) {
      for (j in seq_len(lim)) {
        rows <- c(rows,safe_row(paste0("obj",i,"_child",j),x[[j]]))
      }
    }
  }
}
writeLines(rows,output,useBytes=TRUE)
cat("R_SOURCE_ONLY_OBJECT_CLASS_SHAPES_AND_GENERIC_HEADERS_PASS\n")
