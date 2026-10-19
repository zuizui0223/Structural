#!/usr/bin/env Rscript
# BioTIME v2.0 retrospective burned-pilot only detection transitions.
# 19 frozen pilot studies; 76 holdout study species responses NEVER queried.
# Every endpoint is sampled detection, NOT colonization, extinction, dispersal or q.
suppressPackageStartupMessages(library(data.table))

pilot_detection_summary <- function(raw, pilot_ids, realm_by_id) {
  required <- c("STUDY_ID","YEAR","MONTH","LATITUDE","LONGITUDE","SAMPLE_DESC",
                "newID","valid_name","resolution","ABUNDANCE","BIOMASS")
  if (!all(required %in% names(raw)))
    stop("Official BioTIME source missing prospectively required columns: ",
         paste(setdiff(required,names(raw)),collapse=","))
  if (!length(pilot_ids) || anyDuplicated(pilot_ids)) stop("Invalid frozen pilot identifiers")
  if (!all(pilot_ids %in% names(realm_by_id))) stop("Realm coverage for pilot is incomplete")
  setDT(raw)

  # CRITICAL: row subset by study BEFORE reading any taxonomic or abundance column.
  dt <- raw[as.character(STUDY_ID) %in% pilot_ids, .(
    study=as.character(STUDY_ID),
    year=suppressWarnings(as.integer(YEAR)),
    month=suppressWarnings(as.integer(MONTH)),
    latitude=suppressWarnings(as.numeric(LATITUDE)),
    longitude=suppressWarnings(as.numeric(LONGITUDE)),
    event=as.character(SAMPLE_DESC),
    taxon=as.character(newID),
    valid_name=as.character(valid_name),
    resolution=as.character(resolution),
    abundance=suppressWarnings(as.numeric(ABUNDANCE)),
    biomass=suppressWarnings(as.numeric(BIOMASS))
  )]
  if (!nrow(dt)) stop("No rows in permanently burned pilot")
  input_n <- nrow(dt)
  # Stable geographic proxy and fixed calendar month; neither implies fixed gear/effort.
  dt <- dt[is.finite(latitude) & is.finite(longitude) &
           abs(latitude)<=90 & abs(longitude)<=180 &
           !is.na(year) & year>=1800L & year<=2026L &
           !is.na(month) & month>=1L & month<=12L &
           !is.na(event) & nzchar(trimws(event))]
  if (!nrow(dt)) stop("No valid pilot sampling-event frame")
  dt[,site:=paste0(sprintf("%.5f",latitude),",",sprintf("%.5f",longitude))]
  valid_physical_n <- nrow(dt)
  ev <- unique(dt[,.(study,site,year,month,event)])
  sy <- ev[,.(n_events=.N),by=.(study,site,year,month)]
  year_next <- copy(sy)
  year_next[,year:=year-1L]
  setnames(year_next,"n_events","n_next")
  target_keys <- c("study","site","year","month")
  pair <- merge(sy,year_next,by=target_keys,all=FALSE)
  pair <- pair[n_events>=2L & n_next>=2L]
  if (!nrow(pair)) stop("No predeclared 2-event same-month consecutive-year pairs in pilot")
  pair <- unique(pair,by=target_keys)

  # Author-validated species only. A long-table omitted record is non-detection,
  # not a measured biological absence. Treat biomass-only detected taxa as positive.
  q <- dt[!is.na(taxon) & nzchar(trimws(taxon)) &
          !is.na(valid_name) & nzchar(trimws(valid_name)) &
          !is.na(resolution) & tolower(trimws(resolution))=="species" &
          ((is.finite(abundance) & abundance>0) |
           (is.finite(biomass) & biomass>0)),
          .(study,site,year,month,event,taxon)]
  if (!nrow(q)) stop("No species-resolution positive-detection rows; do not widen domain")
  positive_raw <- nrow(q)
  d_ev <- unique(q)
  rm(q)
  gc(verbose=FALSE)
  d <- d_ev[,.(positive_events=.N),by=.(study,site,year,month,taxon)]
  rm(d_ev); gc(verbose=FALSE)

  # Prior source pool is study × year × month, defined ONLY at t, never using t+1.
  pool <- d[,.(source_sites=.N),by=.(study,year,month,taxon)]
  pool[,source_group:=fifelse(source_sites==1L,"1",
                         fifelse(source_sites==2L,"2",
                         fifelse(source_sites<=4L,"3-4",">=5")))]
  pool_ct <- pool[,.(pool_species=.N),by=.(study,year,month,source_group)]

  # Denominator for 00/01/10/11: all taxa in the t regional pool at EVERY
  # eligible target pair. Expand only four source-count group totals, not
  # every target × species cell.
  risk <- merge(pair[,..target_keys],pool_ct,
                by=c("study","year","month"),all=FALSE,allow.cartesian=TRUE)
  risk_agg <- risk[,.(eligible_species_pair_cells=sum(pool_species),
                      supported_target_pairs=.N),
                   by=.(study,source_group)]
  # Restrict detection outcomes to the fully defined prospective target pairs.
  old <- merge(d,pair[,..target_keys],by=target_keys,all=FALSE)
  old <- merge(old,pool[,.(study,year,month,taxon,source_group)],
               by=c("study","year","month","taxon"),all=FALSE)
  next_det <- copy(d)
  next_det[,year:=year-1L]
  setnames(next_det,"positive_events","positive_events_next")
  new_all <- merge(next_det,pair[,..target_keys],by=target_keys,all=FALSE)
  new_pooled <- merge(new_all,pool[,.(study,year,month,taxon,source_group)],
                       by=c("study","year","month","taxon"),all=FALSE)
  unseen_prior_pool <- nrow(new_all)-nrow(new_pooled)
  if (unseen_prior_pool<0L) stop("New detection source-pool accounting impossible")
  joined_keys <- c(target_keys,"taxon")
  has_new <- unique(new_pooled[,..joined_keys])
  has_new[,present_next:=TRUE]
  has_old <- unique(old[,..joined_keys])
  has_old[,present_old:=TRUE]
  j11 <- merge(old,new_pooled[,c(joined_keys,"positive_events_next"),with=FALSE],
               by=joined_keys,all=FALSE)
  j10 <- merge(old,has_new,by=joined_keys,all.x=TRUE)[is.na(present_next)]
  j01 <- merge(new_pooled,has_old,by=joined_keys,all.x=TRUE)[is.na(present_old)]

  count11 <- j11[,.(n11=.N),by=.(study,source_group)]
  count10 <- j10[,.(n10=.N,n10_2plus=sum(positive_events>=2L)),
                  by=.(study,source_group)]
  count01 <- j01[,.(n01=.N,n01_2plus=sum(positive_events_next>=2L)),
                  by=.(study,source_group)]
  groups <- copy(risk_agg)
  for (other in list(count11,count10,count01))
    groups <- merge(groups,other,by=c("study","source_group"),all.x=TRUE)
  for (name in c("n11","n10","n01","n10_2plus","n01_2plus")) {
    set(groups,which(is.na(groups[[name]])),name,0L)
  }
  groups[,n00:=as.numeric(eligible_species_pair_cells)-n01-n10-n11]
  if (any(groups$n00 < 0) ||
      any(groups[,n00+n01+n10+n11 != eligible_species_pair_cells]))
    stop("Transition accounting identity failed; no ecological interpretation authorized")
  if (any(groups$n01_2plus>groups$n01) || any(groups$n10_2plus>groups$n10))
    stop("Replicated detection counts exceed source detection totals")
  for (name in c("n00","n01","n10","n11","n10_2plus","n01_2plus"))
    set(groups,j=name,value=as.numeric(groups[[name]]))

  study_ids <- data.table(study=as.character(pilot_ids),
                          realm=unname(realm_by_id[pilot_ids]))
  if (anyNA(study_ids$realm)) stop("Cannot assign pilot study realm")
  summed <- groups[,lapply(.SD,sum),
                   by="study",
                   .SDcols=c("eligible_species_pair_cells","n00","n01","n10",
                             "n11","n01_2plus","n10_2plus")]
  study_out <- merge(study_ids,summed,by="study",all.x=TRUE)
  scorecols <- c("eligible_species_pair_cells","n00","n01","n10","n11",
                 "n01_2plus","n10_2plus")
  for (name in scorecols) set(study_out,which(is.na(study_out[[name]])),name,0)
  events_n <- ev[,.(valid_sample_events=.N),by="study"]
  pair_n <- pair[,.(target_site_month_year_pairs=.N,
                    paired_event_min=sum(pmin(n_events,n_next)),
                    paired_event_max=sum(pmax(n_events,n_next))),
                 by="study"]
  det_n <- d[,.(unique_pilot_taxa=uniqueN(taxon),
                species_site_month_year_detections=.N),by="study"]
  raw_n <- dt[,.(valid_physical_rows=.N),by="study"]
  for (f in list(events_n,pair_n,det_n,raw_n))
    study_out <- merge(study_out,f,by="study",all.x=TRUE)
  for (name in setdiff(names(study_out),c("study","realm")))
    set(study_out,which(is.na(study_out[[name]])),name,0)

  study_out[,apparent_new_detection_rate:=
    fifelse(n00+n01>0,n01/(n00+n01),NA_real_)]
  study_out[,apparent_loss_of_detection_rate:=
    fifelse(n10+n11>0,n10/(n10+n11),NA_real_)]
  setorder(study_out,realm,study)
  setorder(groups,study,source_group)
  summary_cols <- c(scorecols,"target_site_month_year_pairs")
  grand <- lapply(summary_cols,function(z)sum(study_out[[z]]))
  names(grand) <- summary_cols
  grand[["unseen_prior_source_next_detections"]] <- as.numeric(unseen_prior_pool)
  grand[["pilot_valid_raw_rows"]] <- as.numeric(valid_physical_n)
  grand[["pilot_positive_species_rows"]] <- as.numeric(positive_raw)
  grand[["pilot_input_records"]] <- as.numeric(input_n)
  realm <- study_out[,lapply(.SD,sum),by=.(realm),.SDcols=scorecols]
  realm[,n_studies:=study_out[,sum(realm==.BY$realm),by=realm]$V1[match(realm,study_out$realm)]]
  # Robust explicit realm count to avoid accidental vector recycling.
  realm[,n_studies:=as.integer(vapply(realm,
     function(r) sum(study_out$realm==r),integer(1)))]
  setorder(realm,realm)

  list(overall=grand,by_study_group=groups,
       per_study=study_out,by_realm=realm,
       data_quality=list(
         site_proxy="fixed 5-decimal coordinate only, not verified permanent site",
         survey_event="SAMPLE_DESC within site-year-month (already curation-defined)",
         sampling_effort="at least two distinct source events in each sampled month-year; not effort standardization",
         taxon="only publisher resolution=species with nonblank ID and positive abundance or biomass",
         zeros="no species record in an otherwise sampled target unit, not estimated ecological absence",
         regional_source="t study-year-month detected species pool; t+1 cannot define denominator",
         01_replicated="species detected in >=2 distinct next-year SAMPLE_DESC events",
         external_new="t+1 detections of species absent from entire prior-year study-month pool excluded from 01/00",
         method_changed="not ruled out; method/gear comparability NOT validated",
         no_true_colonization_or_extinction=TRUE,
         no_directional_movement_or_establishment=TRUE,
         no_claim_of_pristine_fresh_confirmation=TRUE),
       pilot_only=TRUE,holdout_study_species_responses_accessed=0L)
}


main <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  if (length(args)!=5L)
    stop("Usage: Rscript script.R original.rds split.json frozen_protocol.json aggregate.json studies.csv")
  input <- args[1]; split_file <- args[2]; protocol_file <- args[3]
  json_out <- args[4]; csv_out <- args[5]
  protocol <- jsonlite::fromJSON(protocol_file,simplifyVector=FALSE)
  split <- jsonlite::fromJSON(split_file,simplifyVector=FALSE)
  if (protocol$schema!="structural.biotime_pilot_detection_protocol.v1_252" ||
      protocol$status!="FROZEN_BEFORE_PILOT_SPECIES_RESPONSE_ACCESS" ||
      split$schema!="structural.biotime_v2_pilot_confirmatory_split.v1_251" ||
      protocol$pilot_count!=19L || protocol$holdout_count!=76L)
    stop("Mismatch in frozen pilot protocol or disjoint study partition")
  realm_names <- c("Freshwater","Marine","Terrestrial")
  pilot_by_realm <- lapply(realm_names,function(realm)
    unlist(split$realms[[realm]]$pilot,use.names=FALSE))
  holdout <- unlist(lapply(realm_names,function(realm)
    unlist(split$realms[[realm]]$holdout,use.names=FALSE)),use.names=FALSE)
  pilot <- unlist(pilot_by_realm,use.names=FALSE)
  if (length(pilot)!=19L || length(unique(pilot))!=19L ||
      length(holdout)!=76L || length(unique(holdout))!=76L ||
      any(pilot %in% holdout))
    stop("Prospectively frozen 19/76 study partition violated")
  expected_md5 <- protocol$source$rds_md5
  if (unname(tools::md5sum(input))!=expected_md5)
    stop("BioTIME original source MD5 mismatch before response access")
  realm_by_id <- rep(realm_names,lengths(pilot_by_realm))
  names(realm_by_id) <- pilot
  cat("FROZEN BURNED-PILOT ONLY: selecting 19 study IDs. 76 holdout studies forbidden.\n")
  original <- readRDS(input)
  result <- pilot_detection_summary(original,pilot,realm_by_id)
  rm(original); gc(verbose=FALSE)
  if (nrow(result$per_study)!=19L ||
      !identical(sort(as.character(result$per_study$study)),sort(as.character(pilot))))
    stop("Pilot species response touched wrong study population")
  if (result$overall$eligible_species_pair_cells != sum(unlist(
        result$overall[c("n00","n01","n10","n11")])))
    stop("Grand total detection transitions do not reconcile")
  output <- list(
    schema="structural.biotime_burned_pilot_detection.v1_252",
    source_doi=protocol$source$doi,
    source_rds_md5=expected_md5,
    pilot_study_count=19L,
    reserved_holdout_studies=76L,
    holdout_study_species_responses_accessed=0L,
    evidence_class="RETROSPECTIVE_BURNED_PILOT_DESCRIPTIVE_DETECTION_ONLY",
    original_mammal_heldout_accessed=FALSE,
    GEB_scientific_HOLD=TRUE,
    eBird_used=FALSE,
    new_confirmatory_systems_admitted=0L,
    data_quality=result$data_quality,
    overall=result$overall,
    by_realm=result$by_realm,
    by_study_group=result$by_study_group
  )
  jsonlite::write_json(output,json_out,pretty=TRUE,auto_unbox=TRUE,na="null")
  fwrite(result$per_study,csv_out,na="")
  cat("PILOT-ONLY detection transitions:\n")
  print(result$overall)
  cat("No direct animal movement, population extinction, true colonization or external confirmation.\n")
}
if (sys.nframe()==0L) main()
