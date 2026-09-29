#!/usr/bin/env Rscript
# One-shot GIFT pilot species response for the frozen 99-island / 147-list route.
# Confirmatory list IDs are used only as a forbidden-set audit and are never queried.

args <- commandArgs(trailingOnly=TRUE)
get_arg <- function(flag) {
  i <- match(flag,args)
  if(is.na(i) || i==length(args)) stop(paste("missing",flag))
  args[[i+1]]
}
pilot_lists_path <- get_arg("--pilot-lists")
confirm_lists_path <- get_arg("--confirmatory-lists")
universe_path <- get_arg("--species-universe")
matrix_path <- get_arg("--pilot-matrix")
receipt_path <- get_arg("--receipt")

required <- c("GIFT","jsonlite","digest")
missing <- required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing)) stop(paste("missing packages:",paste(missing,collapse=",")))
if(as.character(utils::packageVersion("GIFT"))!="1.3.4") stop("unexpected GIFT package version")

pilot <- utils::read.csv(pilot_lists_path,stringsAsFactors=FALSE,check.names=FALSE)
confirm <- utils::read.csv(confirm_lists_path,stringsAsFactors=FALSE,check.names=FALSE)
required_route <- c("entity_ID","list_ID","ref_ID")
if(!all(required_route %in% names(pilot)) || !all(required_route %in% names(confirm))) {
  stop("routing schema drift")
}
pilot[] <- lapply(pilot,as.character)
confirm[] <- lapply(confirm,as.character)
if(nrow(pilot)!=147 || length(unique(pilot$list_ID))!=147) stop("pilot list count drift")
if(length(unique(pilot$entity_ID))!=99) stop("pilot entity count drift")
if(nrow(confirm)!=596 || length(unique(confirm$list_ID))!=596) stop("confirmatory list count drift")
if(length(unique(confirm$entity_ID))!=404) stop("confirmatory entity count drift")
if(length(intersect(pilot$list_ID,confirm$list_ID))>0) stop("pilot/confirmatory list_ID overlap")
if(length(intersect(pilot$entity_ID,confirm$entity_ID))>0) stop("pilot/confirmatory entity overlap")

route <- setNames(pilot$entity_ID,pilot$list_ID)
confirm_set <- unique(confirm$list_ID)
api <- "https://gift.uni-goettingen.de/api/extended/"
api_started <- FALSE
species_rows_received <- FALSE
raw_parts <- list()
failure <- NULL

taxonomy <- tryCatch(
  GIFT::GIFT_taxonomy(api=api,GIFT_version="3.2"),
  error=function(e) { failure <<- paste("taxonomy metadata query failed:",conditionMessage(e)); NULL }
)
if(is.null(taxonomy)) {
  result <- list(
    schema="structural.gift_pilot_response_result.v1_54",
    status="HOLD_PRE_SPECIES_API_METADATA_FAILURE",
    reason=failure,
    pilot_response_consumed=FALSE,
    confirmatory_species_composition_opened=FALSE,
    counts_as_fresh_confirmation=FALSE
  )
  dir.create(dirname(receipt_path),recursive=TRUE,showWarnings=FALSE)
  jsonlite::write_json(result,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
  quit(status=2)
}

for(i in seq_len(nrow(pilot))) {
  lid <- pilot$list_ID[i]
  api_started <- TRUE
  part <- tryCatch(
    GIFT::GIFT_checklists_raw(
      list_ID=as.numeric(lid),
      namesmatched=FALSE,
      taxon_name="Angiospermae",
      floristic_group="native",
      taxonomy=taxonomy,
      GIFT_version="3.2",
      api=api
    ),
    error=function(e) { failure <<- paste("pilot checklist query failed for list_ID",lid,":",conditionMessage(e)); NULL }
  )
  if(is.null(part)) break
  if(nrow(part)>0) species_rows_received <- TRUE
  raw_parts[[length(raw_parts)+1L]] <- part
}
if(!is.null(failure)) {
  result <- list(
    schema="structural.gift_pilot_response_result.v1_54",
    status="TERMINAL_PILOT_API_FAILURE_AFTER_REQUEST_STARTED",
    reason=failure,
    api_request_started=api_started,
    species_rows_received_before_failure=species_rows_received,
    pilot_response_consumed=TRUE,
    confirmatory_species_composition_opened=FALSE,
    counts_as_fresh_confirmation=FALSE
  )
  dir.create(dirname(receipt_path),recursive=TRUE,showWarnings=FALSE)
  jsonlite::write_json(result,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
  quit(status=2)
}

raw <- if(length(raw_parts)) do.call(rbind,raw_parts) else data.frame()
if(nrow(raw)==0) stop("pilot query returned zero species rows")
species_rows_received <- TRUE
needed <- c("ref_ID","list_ID","entity_ID","work_ID","work_species","questionable","native","quest_native")
if(!all(needed %in% names(raw))) stop("GIFT response schema missing required columns")

for(nm in c("ref_ID","list_ID","entity_ID","work_ID","work_species")) raw[[nm]] <- as.character(raw[[nm]])
returned_lists <- unique(raw$list_ID)
if(any(!returned_lists %in% pilot$list_ID)) stop("unknown/nonpilot list_ID returned")
if(any(returned_lists %in% confirm_set)) stop("confirmatory list_ID returned during pilot")
if(!setequal(returned_lists,pilot$list_ID)) stop("one or more frozen pilot list_IDs returned no species rows")

expected_entity <- unname(route[raw$list_ID])
if(any(is.na(expected_entity)) || any(raw$entity_ID != expected_entity)) stop("returned list_ID/entity_ID mapping drift")

wid_num <- suppressWarnings(as.numeric(raw$work_ID))
if(any(!is.finite(wid_num)) || any(wid_num<=0) || any(wid_num != floor(wid_num))) stop("invalid work_ID")
if(any(is.na(raw$work_species)) || any(trimws(raw$work_species)=="")) stop("blank work_species")
label_count <- tapply(raw$work_species,raw$work_ID,function(x) length(unique(x)))
if(any(label_count != 1L)) stop("multiple work_species labels for one work_ID")

as01 <- function(x) {
  z <- suppressWarnings(as.numeric(x))
  z
}
native <- as01(raw$native)
questionable <- as01(raw$questionable)
quest_native <- as01(raw$quest_native)
accepted <- !is.na(native) & !is.na(questionable) & !is.na(quest_native) &
            native==1 & questionable==0 & quest_native==0
accepted_rows <- raw[accepted,,drop=FALSE]
if(nrow(accepted_rows)==0) stop("no high-confidence native rows in pilot")

pilot_entities <- sort(unique(pilot$entity_ID),method="radix")
presence_by_entity <- setNames(vector("list",length(pilot_entities)),pilot_entities)
for(eid in pilot_entities) {
  presence_by_entity[[eid]] <- unique(accepted_rows$work_ID[accepted_rows$entity_ID==eid])
}
candidate_ids <- sort(unique(accepted_rows$work_ID),method="radix")
presence_count <- vapply(candidate_ids,function(wid) {
  sum(vapply(presence_by_entity,function(v) wid %in% v,logical(1)))
},integer(1))
absence_count <- length(pilot_entities)-presence_count
eligible <- presence_count>=5L & absence_count>=5L
focal_ids <- candidate_ids[eligible]
if(length(focal_ids)==0) stop("zero eligible pilot species after frozen 5/5 rule")

id_to_label <- tapply(raw$work_species,raw$work_ID,function(x) unique(x)[1])
ord <- order(as.numeric(focal_ids))
focal_ids <- focal_ids[ord]
presence_count <- presence_count[eligible][ord]
absence_count <- absence_count[eligible][ord]

universe <- data.frame(
  work_ID=focal_ids,
  work_species=unname(id_to_label[focal_ids]),
  pilot_presence_count=presence_count,
  pilot_absence_count=absence_count,
  stringsAsFactors=FALSE
)
matrix_rows <- vector("list",length(pilot_entities))
for(i in seq_along(pilot_entities)) {
  eid <- pilot_entities[i]
  ys <- as.integer(focal_ids %in% presence_by_entity[[eid]])
  matrix_rows[[i]] <- data.frame(entity_ID=eid,work_ID=focal_ids,y=ys,stringsAsFactors=FALSE)
}
mat <- do.call(rbind,matrix_rows)
if(nrow(mat)!=(99L*nrow(universe))) stop("pilot matrix row count drift")
if(!all(mat$y %in% c(0L,1L))) stop("pilot matrix target domain drift")

dir.create(dirname(universe_path),recursive=TRUE,showWarnings=FALSE)
utils::write.csv(universe,universe_path,row.names=FALSE,quote=TRUE,na="")
utils::write.csv(mat,matrix_path,row.names=FALSE,quote=TRUE,na="")

result <- list(
  schema="structural.gift_pilot_response_result.v1_54",
  status="PRISTINE_PLANT_PILOT_RESPONSE_CONSUMED_AND_SPECIES_UNIVERSE_FROZEN",
  pilot_entities=99L,
  pilot_list_IDs_requested=147L,
  confirmatory_list_IDs_requested=0L,
  raw_species_rows_received=nrow(raw),
  accepted_high_confidence_native_rows=nrow(accepted_rows),
  candidate_pilot_species=length(candidate_ids),
  focal_species=nrow(universe),
  species_threshold_m=5L,
  pilot_matrix_rows=nrow(mat),
  pilot_matrix_positive=sum(mat$y==1L),
  pilot_matrix_negative=sum(mat$y==0L),
  species_universe_sha256=digest::digest(file=universe_path,algo="sha256",serialize=FALSE),
  pilot_matrix_sha256=digest::digest(file=matrix_path,algo="sha256",serialize=FALSE),
  pilot_response_consumed=TRUE,
  confirmatory_species_composition_opened=FALSE,
  confirmatory_response_authorized=FALSE,
  counts_as_fresh_confirmation=FALSE,
  fresh_system_denominator_contribution=0L,
  next_action="freeze cross-fitted R3/C pilot features, fit fixed lambda=1 models, and freeze all 404-island confirmatory predictions before any confirmatory list_ID is requested"
)
jsonlite::write_json(result,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
cat(jsonlite::toJSON(result,pretty=TRUE,auto_unbox=TRUE,null="null"),"\n")
