#!/usr/bin/env Rscript
# One-shot confirmatory GIFT response router for the frozen 404-island,
# 596-list surface. Raw/nonfocal rows are never persisted.

args <- commandArgs(trailingOnly=TRUE)
get_arg <- function(flag) {
  i <- match(flag,args)
  if(is.na(i) || i==length(args)) stop(paste("missing",flag))
  args[[i+1]]
}
confirm_lists_path <- get_arg("--confirmatory-lists")
pilot_lists_path <- get_arg("--pilot-lists")
universe_path <- get_arg("--species-universe")
matrix_path <- get_arg("--matrix")
receipt_path <- get_arg("--receipt")

required <- c("GIFT","jsonlite","digest")
missing <- required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing)) stop(paste("missing packages:",paste(missing,collapse=",")))
if(as.character(utils::packageVersion("GIFT"))!="1.3.4") stop("unexpected GIFT package version")

confirm <- utils::read.csv(confirm_lists_path,stringsAsFactors=FALSE,check.names=FALSE)
pilot <- utils::read.csv(pilot_lists_path,stringsAsFactors=FALSE,check.names=FALSE)
universe <- utils::read.csv(universe_path,stringsAsFactors=FALSE,check.names=FALSE)
for(x in list(confirm,pilot)) if(!all(c("entity_ID","list_ID","ref_ID") %in% names(x))) stop("routing schema drift")
if(!all(c("work_ID","work_species") %in% names(universe))) stop("species universe schema drift")
confirm[] <- lapply(confirm,as.character); pilot[] <- lapply(pilot,as.character)
universe$work_ID <- as.character(universe$work_ID);universe$work_species <- as.character(universe$work_species)

if(nrow(confirm)!=596 || length(unique(confirm$list_ID))!=596 || length(unique(confirm$entity_ID))!=404) stop("confirmatory routing count drift")
if(nrow(pilot)!=147 || length(unique(pilot$list_ID))!=147) stop("pilot routing count drift")
if(length(intersect(confirm$list_ID,pilot$list_ID))>0) stop("pilot/confirmatory list overlap")
if(nrow(universe)!=224 || anyDuplicated(universe$work_ID)) stop("focal species universe drift")

route <- setNames(confirm$entity_ID,confirm$list_ID)
pilot_set <- unique(pilot$list_ID)
focal <- universe$work_ID
focal_label <- setNames(universe$work_species,universe$work_ID)
api <- "https://gift.uni-goettingen.de/api/extended/"

# Response-independent API preflight before the first confirmatory checklist request.
taxonomy <- tryCatch(
  GIFT::GIFT_taxonomy(api=api,GIFT_version="3.2"),
  error=function(e) NULL
)
if(is.null(taxonomy)) {
  result <- list(
    schema="structural.gift_confirmatory_response_result.v1_61",
    status="HOLD_PRE_CONFIRMATORY_API_METADATA_FAILURE",
    confirmatory_response_consumed=FALSE,
    confirmatory_list_requests_started=FALSE,
    counts_as_fresh_confirmation=FALSE,
    fresh_system_denominator_contribution=0L
  )
  dir.create(dirname(receipt_path),recursive=TRUE,showWarnings=FALSE)
  jsonlite::write_json(result,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
  quit(status=2)
}

raw_parts <- list()
started <- FALSE
failure <- NULL
for(i in seq_len(nrow(confirm))) {
  lid <- confirm$list_ID[i]
  started <- TRUE
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
    error=function(e) { failure <<- paste("confirmatory query failed for list_ID",lid,":",conditionMessage(e)); NULL }
  )
  if(is.null(part)) break
  if(nrow(part)==0) { failure <- paste("confirmatory list_ID returned zero species rows:",lid); break }
  raw_parts[[length(raw_parts)+1L]] <- part
}
if(!is.null(failure)) {
  result <- list(
    schema="structural.gift_confirmatory_response_result.v1_61",
    status="TERMINAL_CONFIRMATORY_API_FAILURE_AFTER_ACCESS_STARTED",
    reason=failure,
    confirmatory_response_consumed=started,
    confirmatory_list_requests_started=started,
    counts_as_fresh_confirmation=FALSE,
    fresh_system_denominator_contribution=0L,
    rerun_authorized=FALSE
  )
  dir.create(dirname(receipt_path),recursive=TRUE,showWarnings=FALSE)
  jsonlite::write_json(result,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
  quit(status=2)
}

raw <- do.call(rbind,raw_parts)
needed <- c("ref_ID","list_ID","entity_ID","work_ID","work_species","questionable","native","quest_native")
if(!all(needed %in% names(raw))) stop("confirmatory response schema missing required columns")
for(nm in c("ref_ID","list_ID","entity_ID","work_ID","work_species")) raw[[nm]] <- as.character(raw[[nm]])

returned_lists <- unique(raw$list_ID)
if(any(returned_lists %in% pilot_set)) stop("pilot list_ID appeared in confirmatory response")
if(any(!returned_lists %in% confirm$list_ID)) stop("unknown list_ID appeared in confirmatory response")
if(!setequal(returned_lists,confirm$list_ID)) stop("not every frozen confirmatory list_ID returned species rows")
expected_entity <- unname(route[raw$list_ID])
if(any(is.na(expected_entity)) || any(raw$entity_ID != expected_entity)) stop("confirmatory list_ID/entity_ID mapping drift")

wid_num <- suppressWarnings(as.numeric(raw$work_ID))
if(any(!is.finite(wid_num)) || any(wid_num<=0) || any(wid_num!=floor(wid_num))) stop("invalid work_ID in confirmatory response")
native <- suppressWarnings(as.numeric(raw$native))
questionable <- suppressWarnings(as.numeric(raw$questionable))
quest_native <- suppressWarnings(as.numeric(raw$quest_native))
accepted <- !is.na(native) & !is.na(questionable) & !is.na(quest_native) &
            native==1 & questionable==0 & quest_native==0
accepted_rows <- raw[accepted,,drop=FALSE]

entities <- sort(unique(confirm$entity_ID),method="radix")
accepted_entity_counts <- table(factor(accepted_rows$entity_ID,levels=entities))
if(any(accepted_entity_counts==0)) stop("confirmatory entity has zero accepted high-confidence native rows")

focal_seen <- raw$work_ID %in% focal
if(any(focal_seen)) {
  focal_rows <- raw[focal_seen,,drop=FALSE]
  expected_label <- unname(focal_label[focal_rows$work_ID])
  if(any(is.na(expected_label)) || any(focal_rows$work_species != expected_label)) stop("focal work_ID/work_species label drift")
}
nonfocal_rows <- sum(!focal_seen)

accepted_focal <- accepted_rows[accepted_rows$work_ID %in% focal,,drop=FALSE]
presence_by_entity <- setNames(vector("list",length(entities)),entities)
for(eid in entities) presence_by_entity[[eid]] <- unique(accepted_focal$work_ID[accepted_focal$entity_ID==eid])

focal <- focal[order(as.numeric(focal))]
matrix_parts <- vector("list",length(entities))
for(i in seq_along(entities)) {
  eid <- entities[i]
  matrix_parts[[i]] <- data.frame(
    entity_ID=eid,
    work_ID=focal,
    y=as.integer(focal %in% presence_by_entity[[eid]]),
    stringsAsFactors=FALSE
  )
}
mat <- do.call(rbind,matrix_parts)
if(nrow(mat)!=404L*224L || !all(mat$y %in% c(0L,1L))) stop("confirmatory matrix drift")

dir.create(dirname(matrix_path),recursive=TRUE,showWarnings=FALSE)
utils::write.csv(mat,matrix_path,row.names=FALSE,quote=TRUE,na="")
result <- list(
  schema="structural.gift_confirmatory_response_result.v1_61",
  status="CONFIRMATORY_RESPONSE_CONSUMED_FOCAL_MATRIX_FROZEN",
  confirmatory_entities=404L,
  confirmatory_list_IDs_requested=596L,
  pilot_list_IDs_requested=0L,
  raw_species_rows_received=nrow(raw),
  nonfocal_species_rows_received=nonfocal_rows,
  accepted_high_confidence_native_rows=nrow(accepted_rows),
  focal_species=224L,
  matrix_rows=nrow(mat),
  matrix_positive=sum(mat$y==1L),
  matrix_negative=sum(mat$y==0L),
  matrix_sha256=digest::digest(file=matrix_path,algo="sha256",serialize=FALSE),
  raw_species_rows_persisted=FALSE,
  nonfocal_rows_persisted=FALSE,
  confirmatory_response_consumed=TRUE,
  confirmatory_scoring_authorized=TRUE,
  counts_as_fresh_confirmation=FALSE,
  fresh_system_denominator_contribution=0L,
  rerun_authorized=FALSE
)
jsonlite::write_json(result,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
cat(jsonlite::toJSON(result,pretty=TRUE,auto_unbox=TRUE,null="null"),"\n")
