#!/usr/bin/env Rscript
# BioTIME v2 response-opaque network independence audit for all 95 pilot/reserved STUDY_IDs.
# Reads only six physical sampling columns from the original MD5-locked public RDS.
suppressPackageStartupMessages(library(data.table))

shared_keys <- function(tab, key) {
  repeated <- duplicated(tab, by=key) |
              duplicated(tab, by=key, fromLast=TRUE)
  small <- tab[repeated]
  if (!nrow(small))
    return(data.table(a=character(0), b=character(0), shared=integer(0)))
  both <- merge(small, small, by=key, allow.cartesian=TRUE,
                suffixes=c("_a", "_b"))[study_a < study_b]
  if (!nrow(both))
    return(data.table(a=character(0), b=character(0), shared=integer(0)))
  both[,.(shared=.N),by=.(a=study_a,b=study_b)]
}

connected_groups <- function(ids, edge) {
  adjacency <- setNames(lapply(ids, function(x) character(0)), ids)
  if (nrow(edge)) for (i in seq_len(nrow(edge))) {
    a <- edge$a[i]; b <- edge$b[i]
    adjacency[[a]] <- c(adjacency[[a]],b)
    adjacency[[b]] <- c(adjacency[[b]],a)
  }
  seen <- character(0)
  components <- list()
  for (id in ids) {
    if (id %in% seen) next
    todo <- id; component <- character(0)
    while (length(todo)) {
      node <- todo[[1L]]; todo <- todo[-1L]
      if (node %in% seen) next
      seen <- c(seen,node); component <- c(component,node)
      todo <- c(todo,setdiff(adjacency[[node]],seen))
    }
    components[[length(components)+1L]] <- sort(unique(component))
  }
  components
}

audit_frame_independence <- function(raw, pilot_ids, reserved_ids,
                                     qualified_ids, realm_by_id) {
  needed <- c("STUDY_ID","YEAR","MONTH","LATITUDE","LONGITUDE","SAMPLE_DESC")
  if (!all(needed %in% names(raw))) stop("BioTIME original six physical columns changed")
  ids <- c(as.character(pilot_ids),as.character(reserved_ids))
  if (anyDuplicated(ids) || length(qualified_ids) > length(reserved_ids) ||
      !all(qualified_ids %in% reserved_ids) ||
      !all(ids %in% names(realm_by_id)))
    stop("Invalid frozen 19/76 pilot/holdout and 47 physical candidate ID membership")
  setDT(raw)
  physical <- raw[as.character(STUDY_ID) %in% ids,
                  .(study=as.character(STUDY_ID),
                    year=suppressWarnings(as.integer(YEAR)),
                    month=suppressWarnings(as.integer(MONTH)),
                    latitude=suppressWarnings(as.numeric(LATITUDE)),
                    longitude=suppressWarnings(as.numeric(LONGITUDE)),
                    event=as.character(SAMPLE_DESC))]
  physical <- physical[
    !is.na(year) & year>=1800L & year<=2026L &
    !is.na(month) & month>=1L & month<=12L &
    is.finite(latitude) & is.finite(longitude) &
    abs(latitude)<=90 & abs(longitude)<=180 &
    !is.na(event) & nzchar(trimws(event))
  ]
  if (!nrow(physical)) stop("No physical events in frozen 95-study frame")
  physical[,site:=paste0(sprintf("%.5f", latitude),",",sprintf("%.5f", longitude))]
  events <- unique(physical[,.(study,site,year,month,event)])
  rm(physical); gc(verbose=FALSE)

  frames <- unique(events[,.(study,site,year,month)])
  sites <- unique(frames[,.(study,site)])
  ns <- sites[,.(site_count=.N),by=study]
  nf <- frames[,.(frame_count=.N),by=study]
  studies <- data.table(study=ids,
                         split=ifelse(ids %in% pilot_ids,"burned_pilot","reserved"),
                         realm=unname(realm_by_id[ids]))
  studies <- merge(studies,ns,by="study",all.x=TRUE)
  studies <- merge(studies,nf,by="study",all.x=TRUE)
  for (col in c("site_count","frame_count"))
    set(studies,which(is.na(studies[[col]])),col,0L)
  studies[,physical_v253_eligible:=study %in% qualified_ids]

  # Reconstruct the strict two-event month/year target frame, independently of taxa.
  sy <- events[,.(n_events=.N),by=.(study,site,year,month)]
  newer <- copy(sy)
  newer[,year:=year-1L]
  setnames(newer,"n_events","next_n_events")
  pair <- merge(sy,newer,by=c("study","site","year","month"),all=FALSE)
  pair <- pair[n_events>=2L & next_n_events>=2L]
  active_sites <- unique(pair[,.(study,site)])[,
    .(active_strict_sites=.N),by=study]
  studies <- merge(studies,active_sites,by="study",all.x=TRUE)
  set(studies,which(is.na(studies$active_strict_sites)),
      "active_strict_sites",0L)
  studies[,operator_geography_eligible:=
            physical_v253_eligible & active_strict_sites>=5L]

  # Count exact shared sites & matched site/year/month observations.
  s <- shared_keys(sites,"site")
  f <- shared_keys(frames,c("site","year","month"))
  names(s)[names(s)=="shared"] <- "shared_sites"
  names(f)[names(f)=="shared"] <- "shared_frames"
  pair_ids <- CJ(a=sort(ids),b=sort(ids),sorted=TRUE)[a<b]
  pair_ids <- merge(pair_ids,s,by=c("a","b"),all.x=TRUE)
  pair_ids <- merge(pair_ids,f,by=c("a","b"),all.x=TRUE)
  pair_ids[is.na(shared_sites),shared_sites:=0L]
  pair_ids[is.na(shared_frames),shared_frames:=0L]

  a_counts <- studies[,.(a=study, sites_a=site_count, frames_a=frame_count,
                         split_a=split, realm_a=realm)]
  b_counts <- studies[,.(b=study, sites_b=site_count, frames_b=frame_count,
                         split_b=split, realm_b=realm)]
  pair_ids <- merge(pair_ids,a_counts,by="a",all.x=TRUE)
  pair_ids <- merge(pair_ids,b_counts,by="b",all.x=TRUE)
  pair_ids[,site_containment:=
    fifelse(pmin(sites_a,sites_b)>0,
            shared_sites/pmin(sites_a,sites_b),0)]
  pair_ids[,frame_containment:=
    fifelse(pmin(frames_a,frames_b)>0,
            shared_frames/pmin(frames_a,frames_b),0)]
  pair_ids[,frame_jaccard:=
    fifelse(frames_a+frames_b-shared_frames>0,
            shared_frames/(frames_a+frames_b-shared_frames),0)]
  pair_ids[,near_duplicate_frame:=
     shared_frames>=10L & frame_containment>=.8 & site_containment>=.8]
  pair_ids[,shared_geography:=
     shared_sites>=5L & site_containment>=.8]
  pair_ids[,cross_split:=split_a!=split_b]
  pair_ids[,both_reserved:=split_a=="reserved" & split_b=="reserved"]
  pair_ids[,either_qualified:=(a %in% qualified_ids | b %in% qualified_ids)]
  flagged <- pair_ids[shared_sites>0L | shared_frames>0L]
  setorder(flagged,a,b)

  hard <- pair_ids[near_duplicate_frame,.(a,b)]
  soft <- pair_ids[shared_geography,.(a,b)]
  hard_groups <- connected_groups(ids,hard)
  soft_groups <- connected_groups(ids,soft)
  qual_groups <- Filter(function(g) any(g %in% qualified_ids),hard_groups)
  effective_qualified_components <- length(qual_groups)
  pilot_reserved_hard <- pair_ids[cross_split & near_duplicate_frame]
  pilot_reserved_soft <- pair_ids[cross_split & shared_geography]
  reserved_hard <- pair_ids[both_reserved & near_duplicate_frame]
  reserved_soft <- pair_ids[both_reserved & shared_geography]
  summary <- list(
    all_studies=length(ids),
    original_burned_pilot_studies=length(pilot_ids),
    reserved_studies=length(reserved_ids),
    v253_reserved_physically_qualified=length(qualified_ids),
    reserved_operator_min5_sites_count=sum(studies$operator_geography_eligible),
    all_study_pairs=nrow(pair_ids),
    study_pairs_with_shared_site_or_frame=nrow(flagged),
    near_duplicate_frame_pairs=nrow(hard),
    shared_geography_pairs=nrow(soft),
    near_duplicate_cross_split_pairs=nrow(pilot_reserved_hard),
    shared_geography_cross_split_pairs=nrow(pilot_reserved_soft),
    near_duplicate_within_reserved_pairs=nrow(reserved_hard),
    shared_geography_within_reserved_pairs=nrow(reserved_soft),
    independent_qualifying_network_components_upper_bound=effective_qualified_components,
    distinct_hard_network_component_count=length(hard_groups),
    distinct_geography_component_count=length(soft_groups)
  )
  result <- list(
    schema="structural.biotime_study_frame_independence.v1_254",
    evidence_class="RESPONSE_COLUMN_OPAQUE_CROSS_STUDY_SAMPLING_NETWORK_CHECK",
    results=summary,
    hard_network_components=unname(hard_groups[vapply(hard_groups,length,integer(1))>1L]),
    shared_geography_components=unname(soft_groups[vapply(soft_groups,length,integer(1))>1L]),
    cross_split_near_duplicates=pilot_reserved_hard[,.(a,b,shared_sites,shared_frames)],
    cross_split_shared_geography=pilot_reserved_soft[,.(a,b,shared_sites,shared_frames)],
    forbidden_taxon_response_columns_accessed=FALSE,
    any_reserved_taxon_response_opened=FALSE
  )
  list(report=result,study=studies,overlap=flagged)
}

main <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  if (length(args)!=6L)
    stop("Usage: script source.rds split.json physical_freeze.json protocol.json report.json pair.csv study.csv")
  src<-args[1L];split_path<-args[2L];physical_path<-args[3L]
  protocol_path<-args[4L]; out_json<-args[5L]; out_csv<-args[6L]
  # The pipeline writes a per-study physical summary using filename derived from report.
  out_study<-sub("\\.json$","_studies.csv",out_json)
  contract <- jsonlite::fromJSON(protocol_path,simplifyVector=FALSE)
  split <- jsonlite::fromJSON(split_path,simplifyVector=FALSE)
  phys <- jsonlite::fromJSON(physical_path,simplifyVector=FALSE)
  if (contract$schema!="structural.biotime_study_frame_independence_protocol.v1_254" ||
      contract$status!="FROZEN_BEFORE_REPLAYING_THE_95_STUDY_PHYSICAL_NETWORKS" ||
      split$schema!="structural.biotime_v2_pilot_confirmatory_split.v1_251" ||
      phys$schema!="structural.biotime2_reserved_physical_support_freeze.v1_253")
    stop("Study independence protocol/provenance mismatch; fail closed")
  if (unname(tools::md5sum(src))!=contract$source$rds_md5)
    stop("Public original BioTIME dataset MD5 changed")
  realm_names <- c("Freshwater","Marine","Terrestrial")
  pilot_by_realm <- lapply(realm_names,function(x)
    unlist(split$realms[[x]]$pilot,use.names=FALSE))
  reserve_by_realm <- lapply(realm_names,function(x)
    unlist(split$realms[[x]]$holdout,use.names=FALSE))
  pilot <- as.character(unlist(pilot_by_realm,use.names=FALSE))
  reserve <- as.character(unlist(reserve_by_realm,use.names=FALSE))
  qual <- as.character(unlist(phys$eligible_by_realm,use.names=FALSE))
  if (length(pilot)!=19L || length(reserve)!=76L || length(qual)!=47L ||
      anyDuplicated(c(pilot,reserve)) || !all(qual %in% reserve))
    stop("19/76/47 physical cohort mismatch")
  realm_by <- rep(realm_names,lengths(pilot_by_realm)+lengths(reserve_by_realm))
  names(realm_by) <- unlist(lapply(seq_along(realm_names),function(i)
    c(pilot_by_realm[[i]],reserve_by_realm[[i]])),use.names=FALSE)
  # Only the six physical columns are extracted in the function.
  raw <- readRDS(src)
  a <- audit_frame_independence(raw,pilot,reserve,qual,realm_by)
  rm(raw);gc(verbose=FALSE)
  if(a$report$results$all_studies!=95L ||
     a$report$results$reserved_studies!=76L ||
     a$report$results$v253_reserved_physically_qualified!=47L ||
     a$report$any_reserved_taxon_response_opened)
    stop("Response-opaque study network scope mismatch")
  a$report$source_doi<-contract$source$doi
  a$report$rds_md5<-contract$source$rds_md5
  a$report$study_frame_input_columns<-contract$allowed_rds_columns
  a$report$GEB_scientific_HOLD<-TRUE
  a$report$eBird_used<-FALSE
  a$report$number_of_fresh_confirmatory_systems<-0L
  jsonlite::write_json(a$report,out_json,pretty=TRUE,auto_unbox=TRUE,na="null")
  fwrite(a$overlap,out_csv,na="")
  fwrite(a$study,out_study,na="")
  print(a$report$results)
  cat("NETWORK-IDENTITY ONLY: no reserved-study biological rows or effects scored.\n")
}
if (sys.nframe()==0L) main()
