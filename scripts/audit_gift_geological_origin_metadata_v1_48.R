#!/usr/bin/env Rscript
# Audit GIFT environmental metadata for geological-origin candidate variables.
# This script never requests entity-level environmental values.

args <- commandArgs(trailingOnly=TRUE)
get_arg <- function(flag) {
  i <- match(flag,args)
  if(is.na(i) || i==length(args)) stop(paste("missing",flag))
  args[[i+1]]
}
out_all <- get_arg("--output-all")
out_candidates <- get_arg("--output-candidates")
receipt_path <- get_arg("--receipt")

required <- c("GIFT","jsonlite","digest")
missing <- required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing)) stop(paste("missing packages:",paste(missing,collapse=",")))
if(as.character(utils::packageVersion("GIFT"))!="1.3.4") stop("unexpected GIFT package version")

meta <- GIFT::GIFT_env_meta_misc(
  api="https://gift.uni-goettingen.de/api/extended/",
  GIFT_version="3.2"
)
if(!is.data.frame(meta) || !nrow(meta)) stop("empty GIFT environmental metadata")
fields <- intersect(c("dataset","variable","description","unit"),names(meta))
if(!"variable" %in% fields) stop("environmental metadata lacks variable column")
text <- apply(meta[,fields,drop=FALSE],1,function(x) paste(x,collapse=" | "))
hit <- grepl("origin|geolog|volcan|oceanic|continental|atoll|shelf",text,ignore.case=TRUE,perl=TRUE)
cand <- meta[hit,,drop=FALSE]

canon <- function(df) {
  df <- df[,sort(names(df)),drop=FALSE]
  df[] <- lapply(df,function(x) {
    if(is.factor(x)) as.character(x) else x
  })
  if(nrow(df)) {
    keys <- lapply(df,function(x) { y<-as.character(x); y[is.na(y)]<-"<NA>"; enc2utf8(y) })
    df <- df[do.call(order,c(keys,list(na.last=TRUE,method="radix"))),,drop=FALSE]
  }
  rownames(df)<-NULL
  df
}
meta<-canon(meta); cand<-canon(cand)
dir.create(dirname(out_all),recursive=TRUE,showWarnings=FALSE)
utils::write.csv(meta,out_all,row.names=FALSE,quote=TRUE,na="")
utils::write.csv(cand,out_candidates,row.names=FALSE,quote=TRUE,na="")
vars <- if("variable" %in% names(cand)) sort(unique(as.character(cand$variable))) else character()
receipt <- list(
  schema="structural.gift_geological_origin_metadata_result.v1_48",
  status="GIFT_ENVIRONMENTAL_METADATA_ORIGIN_CANDIDATES_FROZEN",
  metadata_rows=nrow(meta),
  candidate_rows=nrow(cand),
  candidate_variables=vars,
  metadata_sha256=digest::digest(file=out_all,algo="sha256",serialize=FALSE),
  candidates_sha256=digest::digest(file=out_candidates,algo="sha256",serialize=FALSE),
  entity_level_environment_values_opened=FALSE,
  species_composition_opened=FALSE,
  counts_as_empirical_evidence=FALSE,
  next_action=if(nrow(cand)>0) "freeze one candidate variable/category mapping in a separate revision before querying values" else "seek a separate response-independent geological-origin source or explicitly mark the adjustment unavailable"
)
jsonlite::write_json(receipt,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
cat(jsonlite::toJSON(receipt,pretty=TRUE,auto_unbox=TRUE,null="null"),"\n")
