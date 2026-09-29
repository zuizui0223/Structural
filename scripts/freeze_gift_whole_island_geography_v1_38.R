#!/usr/bin/env Rscript
# Freeze non-overlapping GIFT whole-island geography using a deterministic
# response-independent complete-geography rule. No species composition opens.

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
out_excluded <- get_arg("--output-excluded")
receipt_path <- get_arg("--receipt")

required <- c("GIFT","jsonlite","digest")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly=TRUE)]
if(length(missing)) stop(paste("missing R packages:",paste(missing,collapse=",")))
if(as.character(utils::packageVersion("GIFT"))!="1.3.4") stop("unexpected GIFT package version")

entities <- utils::read.csv(entities_path, stringsAsFactors=FALSE, check.names=FALSE)
lists <- utils::read.csv(lists_path, stringsAsFactors=FALSE, check.names=FALSE)
if(nrow(entities)!=1460) stop("whole-island entity count drift")
if(anyDuplicated(as.character(entities$entity_ID))) stop("duplicate entity_ID before overlap resolution")
ids <- as.numeric(as.character(entities$entity_ID))
if(any(is.na(ids))) stop("nonnumeric entity_ID")

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
if(anyDuplicated(as.character(geo$entity_ID))) stop("GIFT geography duplicated entity_ID")

geo$entity_ID <- as.character(geo$entity_ID)
for(nm in c("longitude","latitude","area")) geo[[nm]] <- suppressWarnings(as.numeric(geo[[nm]]))
geo_ids <- as.character(keep)
returned <- geo$entity_ID %in% geo_ids
geo <- geo[returned,,drop=FALSE]

valid <- is.finite(geo$longitude) & is.finite(geo$latitude) & is.finite(geo$area) &
         geo$longitude >= -180 & geo$longitude <= 180 &
         geo$latitude >= -90 & geo$latitude <= 90 & geo$area > 0
valid_ids <- sort(unique(geo$entity_ID[valid]))
invalid_ids <- sort(unique(geo$entity_ID[!valid]))
missing_ids <- sort(setdiff(geo_ids, geo$entity_ID))
excluded <- data.frame(
  entity_ID=c(missing_ids,invalid_ids),
  reason=c(rep("not_returned_by_GIFT_env",length(missing_ids)),
           rep("invalid_or_incomplete_longitude_latitude_area",length(invalid_ids))),
  stringsAsFactors=FALSE
)
if(anyDuplicated(excluded$entity_ID)) stop("excluded entity duplicated")

geo <- geo[geo$entity_ID %in% valid_ids,c("entity_ID","geo_entity","longitude","latitude","area"),drop=FALSE]
geo <- geo[order(as.numeric(geo$entity_ID)),,drop=FALSE]
if(!nrow(geo)) stop("no complete safe geography remains")
retained_lists <- lists[as.character(lists$entity_ID) %in% geo$entity_ID,,drop=FALSE]
retained_lists <- retained_lists[order(as.numeric(retained_lists$entity_ID),as.numeric(retained_lists$list_ID)),,drop=FALSE]

dir.create(dirname(out_geo),recursive=TRUE,showWarnings=FALSE)
utils::write.csv(geo,out_geo,row.names=FALSE,quote=TRUE,na="")
utils::write.csv(retained_lists,out_lists,row.names=FALSE,quote=TRUE,na="")
utils::write.csv(excluded,out_excluded,row.names=FALSE,quote=TRUE,na="")

receipt <- list(
  schema="structural.gift_whole_island_geography_result.v1_38",
  status="COMPLETE_SAFE_WHOLE_ISLAND_GEOGRAPHY_FROZEN",
  input_whole_island_entities=nrow(entities),
  nonoverlap_entity_ID_count=length(keep),
  retained_complete_geography_entities=nrow(geo),
  excluded_overlap_entities=nrow(entities)-length(keep),
  excluded_missing_geography_entities=nrow(excluded),
  excluded_not_returned_entities=length(missing_ids),
  excluded_invalid_geography_entities=length(invalid_ids),
  retained_list_rows=nrow(retained_lists),
  geography_sha256=digest::digest(file=out_geo,algo="sha256",serialize=FALSE),
  retained_lists_sha256=digest::digest(file=out_lists,algo="sha256",serialize=FALSE),
  excluded_manifest_sha256=digest::digest(file=out_excluded,algo="sha256",serialize=FALSE),
  species_composition_opened=FALSE,
  species_richness_computed=FALSE,
  source_features_computed=FALSE,
  counts_as_empirical_evidence=FALSE,
  species_response_authorized=FALSE
)
jsonlite::write_json(receipt,receipt_path,pretty=TRUE,auto_unbox=TRUE)
cat(jsonlite::toJSON(receipt,pretty=TRUE,auto_unbox=TRUE),"
")
