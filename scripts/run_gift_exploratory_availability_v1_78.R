#!/usr/bin/env Rscript
# Nonconfirmatory GIFT endpoint-available response surface after terminal fresh failure.

args <- commandArgs(trailingOnly=TRUE)
get_arg <- function(flag) {
  i <- match(flag,args)
  if(is.na(i) || i==length(args)) stop(paste("missing",flag))
  args[[i+1]]
}
confirm_path <- get_arg("--confirmatory-lists")
universe_path <- get_arg("--species-universe")
matrix_path <- get_arg("--matrix")
availability_path <- get_arg("--availability")
receipt_path <- get_arg("--receipt")

required <- c("GIFT","jsonlite","digest")
missing <- required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing)) stop(paste("missing packages:",paste(missing,collapse=",")))
if(as.character(utils::packageVersion("GIFT"))!="1.3.4") stop("unexpected GIFT package version")

confirm <- utils::read.csv(confirm_path,stringsAsFactors=FALSE,check.names=FALSE)
universe <- utils::read.csv(universe_path,stringsAsFactors=FALSE,check.names=FALSE)
confirm[] <- lapply(confirm,as.character)
universe$work_ID <- as.character(universe$work_ID); universe$work_species <- as.character(universe$work_species)
if(nrow(confirm)!=596 || length(unique(confirm$list_ID))!=596 || length(unique(confirm$entity_ID))!=404) stop("routing count drift")
if(nrow(universe)!=224 || anyDuplicated(universe$work_ID)) stop("species universe drift")

taxonomy <- GIFT::GIFT_taxonomy(api="https://gift.uni-goettingen.de/api/extended/",GIFT_version="3.2")
raw <- GIFT::GIFT_checklists_raw(
  list_ID=as.numeric(confirm$list_ID),
  namesmatched=FALSE,
  taxon_name="Angiospermae",
  floristic_group="native",
  taxonomy=taxonomy,
  GIFT_version="3.2",
  api="https://gift.uni-goettingen.de/api/extended/"
)
needed <- c("list_ID","entity_ID","work_ID","work_species","questionable","native","quest_native")
if(!all(needed %in% names(raw))) stop("response schema missing required columns")
for(nm in c("list_ID","entity_ID","work_ID","work_species")) raw[[nm]] <- as.character(raw[[nm]])
if(any(!raw$list_ID %in% confirm$list_ID)) stop("unknown list_ID returned")

returned_lists <- sort(unique(raw$list_ID),method="radix")
unavailable <- setdiff(confirm$list_ID,returned_lists)
route <- setNames(confirm$entity_ID,confirm$list_ID)
expected_entity <- unname(route[raw$list_ID])
if(any(is.na(expected_entity)) || any(raw$entity_ID!=expected_entity)) stop("list/entity mapping drift")

native <- suppressWarnings(as.numeric(raw$native))
questionable <- suppressWarnings(as.numeric(raw$questionable))
quest_native <- suppressWarnings(as.numeric(raw$quest_native))
accepted <- !is.na(native) & !is.na(questionable) & !is.na(quest_native) &
            native==1 & questionable==0 & quest_native==0
acc <- raw[accepted,,drop=FALSE]

entities <- sort(unique(confirm$entity_ID),method="radix")
avail <- data.frame(entity_ID=entities,total_frozen_lists=0L,available_lists=0L,
                    unavailable_lists=0L,accepted_native_rows=0L,retained=FALSE,
                    stringsAsFactors=FALSE)
for(i in seq_along(entities)) {
  eid <- entities[i]
  lids <- confirm$list_ID[confirm$entity_ID==eid]
  avail$total_frozen_lists[i] <- length(lids)
  avail$available_lists[i] <- sum(lids %in% returned_lists)
  avail$unavailable_lists[i] <- sum(!lids %in% returned_lists)
  avail$accepted_native_rows[i] <- sum(acc$entity_ID==eid)
  avail$retained[i] <- avail$available_lists[i]>0 && avail$accepted_native_rows[i]>0
}
retained_entities <- avail$entity_ID[avail$retained]
if(!length(retained_entities)) stop("no retained endpoint-available entities")

focal <- universe$work_ID[order(as.numeric(universe$work_ID))]
focal_label <- setNames(universe$work_species,universe$work_ID)
focal_rows <- raw[raw$work_ID %in% focal,,drop=FALSE]
if(nrow(focal_rows)) {
  expected <- unname(focal_label[focal_rows$work_ID])
  if(any(is.na(expected)) || any(focal_rows$work_species!=expected)) stop("focal label drift")
}
acc_focal <- acc[acc$work_ID %in% focal & acc$entity_ID %in% retained_entities,,drop=FALSE]
presence <- setNames(vector("list",length(retained_entities)),retained_entities)
for(eid in retained_entities) presence[[eid]] <- unique(acc_focal$work_ID[acc_focal$entity_ID==eid])

parts <- vector("list",length(retained_entities))
for(i in seq_along(retained_entities)) {
  eid <- retained_entities[i]
  parts[[i]] <- data.frame(entity_ID=eid,work_ID=focal,
                           y=as.integer(focal %in% presence[[eid]]),
                           stringsAsFactors=FALSE)
}
mat <- do.call(rbind,parts)
if(nrow(mat)!=length(retained_entities)*224L || !all(mat$y %in% c(0L,1L))) stop("matrix drift")

dir.create(dirname(matrix_path),recursive=TRUE,showWarnings=FALSE)
utils::write.csv(mat,matrix_path,row.names=FALSE,quote=TRUE,na="")
utils::write.csv(avail,availability_path,row.names=FALSE,quote=TRUE,na="")
receipt <- list(
  schema="structural.gift_exploratory_availability_response_result.v1_78",
  status="NONCONFIRMATORY_ENDPOINT_AVAILABLE_RESPONSE_FROZEN",
  frozen_list_IDs=596L,
  returned_nonempty_list_IDs=length(returned_lists),
  unavailable_list_IDs=length(unavailable),
  retained_entities=length(retained_entities),
  excluded_entities=404L-length(retained_entities),
  focal_species=224L,
  matrix_rows=nrow(mat),
  matrix_positive=sum(mat$y==1L),
  matrix_negative=sum(mat$y==0L),
  matrix_sha256=digest::digest(file=matrix_path,algo="sha256",serialize=FALSE),
  availability_sha256=digest::digest(file=availability_path,algo="sha256",serialize=FALSE),
  raw_species_rows_persisted=FALSE,
  fresh_status_restored=FALSE,
  counts_as_fresh_confirmation=FALSE,
  counts_as_primary_confirmatory_evidence=FALSE,
  rerun_authorized=FALSE
)
jsonlite::write_json(receipt,receipt_path,pretty=TRUE,auto_unbox=TRUE,null="null")
cat(jsonlite::toJSON(receipt,pretty=TRUE,auto_unbox=TRUE,null="null"),"\n")
