#!/usr/bin/env Rscript
# Resolve non-overlapping whole-island GIFT geography without species access.

args <- commandArgs(trailingOnly=TRUE)
get_arg <- function(flag) {
  i <- match(flag,args)
  if (is.na(i) || i==length(args)) stop(paste("missing",flag))
  args[[i+1]]
}
entities_path <- get_arg("--entities")
lists_path <- get_arg("--lists")
out_geo <- get_arg("--output-geography")
out_lists <- get_arg("--output-lists")
receipt_path <- get_arg("--receipt")

required <- c("GIFT","jsonlite","digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly=TRUE)]
if(length(missing)) stop(paste("missing R packages:",paste(missing,collapse=",")))
if(as.character(utils::packageVersion("GIFT"))!="1.3.4") stop("unexpected GIFT package version")

entities <- utils::read.csv(entities_path, stringsAsFactors=FALSE, check.names=FALSE)
lists <- utils::read.csv(lists_path, stringsAsFactors=FALSE, check.names=FALSE)
if(!all(c("entity_ID","geo_entity") %in% names(entities))) stop("whole-island entity schema drift")
if(!all(c("entity_ID","list_ID","ref_ID") %in% names(lists))) stop("whole-island list schema drift")
if(anyDuplicated(as.character(entities$entity_ID))) stop("entity_ID duplicated before overlap resolution")

ids <- as.numeric(as.character(entities$entity_ID))
if(any(is.na(ids))) stop("entity_ID is not numeric for GIFT query")

keep <- GIFT::GIFT_no_overlap(
  entity_IDs=ids,
  area_threshold_island=0,
  area_threshold_mainland=100,
  overlap_threshold=0.1,
  geoentities_overlap=NULL,
  GIFT_version="3.2",
  api="https://gift.uni-goettingen.de/api/extended/"
)
keep <- sort(unique(as.numeric(keep)))
if(!length(keep)) stop("overlap resolution removed all whole islands")

geo <- GIFT::GIFT_env(
  entity_ID=keep,
  miscellaneous=c("longitude","latitude","area"),
  rasterlayer=NULL,
  GIFT_version="3.2",
  api="https://gift.uni-goettingen.de/api/extended/"
)
required_geo <- c("entity_ID","longitude","latitude","area")
if(!all(required_geo %in% names(geo))) stop("GIFT geography columns missing")
geo <- geo[,c("entity_ID","geo_entity","longitude","latitude","area"),drop=FALSE]
geo$entity_ID <- as.character(geo$entity_ID)
if(anyDuplicated(geo$entity_ID)) stop("GIFT geography duplicated entity_ID")
if(nrow(geo)!=length(keep)) stop("GIFT geography did not return every retained entity")
for(nm in c("longitude","latitude","area")) {
  geo[[nm]] <- as.numeric(geo[[nm]])
  if(any(!is.finite(geo[[nm]]))) stop(paste("nonfinite geography:",nm))
}
if(any(geo$longitude < -180 | geo$longitude > 180)) stop("longitude out of range")
if(any(geo$latitude < -90 | geo$latitude > 90)) stop("latitude out of range")
if(any(geo$area <= 0)) stop("area must be positive")

geo <- geo[order(as.numeric(geo$entity_ID)),,drop=FALSE]
retained_lists <- lists[as.character(lists$entity_ID) %in% geo$entity_ID,,drop=FALSE]
retained_lists <- retained_lists[order(as.numeric(retained_lists$entity_ID),as.numeric(retained_lists$list_ID)),,drop=FALSE]

dir.create(dirname(out_geo),recursive=TRUE,showWarnings=FALSE)
utils::write.csv(geo,out_geo,row.names=FALSE,quote=TRUE,na="")
utils::write.csv(retained_lists,out_lists,row.names=FALSE,quote=TRUE,na="")
receipt <- list(
  schema="structural.gift_whole_island_geography_result.v1_32",
  status="nonoverlapping_whole_island_geography_frozen",
  input_whole_island_entities=nrow(entities),
  retained_nonoverlapping_entities=nrow(geo),
  excluded_overlap_entities=nrow(entities)-nrow(geo),
  retained_list_rows=nrow(retained_lists),
  longitude_missing=0L, latitude_missing=0L, area_missing=0L,
  geography_sha256=digest::digest(file=out_geo,algo="sha256",serialize=FALSE),
  retained_lists_sha256=digest::digest(file=out_lists,algo="sha256",serialize=FALSE),
  species_composition_opened=FALSE,
  species_richness_computed=FALSE,
  source_features_computed=FALSE,
  counts_as_empirical_evidence=FALSE,
  species_response_authorized=FALSE
)
jsonlite::write_json(receipt,receipt_path,pretty=TRUE,auto_unbox=TRUE)
