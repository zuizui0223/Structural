#!/usr/bin/env Rscript
# BioTIME 2.0: physical study-site-month-year response-opaque support only.
# Do not reference ANY taxon, abundance, biomass or species occurrence column.
suppressPackageStartupMessages(library(data.table))

audit_reserved_physical <- function(raw, reserved_ids, realm_by_id) {
  cols <- c("STUDY_ID","YEAR","MONTH","LATITUDE","LONGITUDE","SAMPLE_DESC")
  if (!all(cols %in% names(raw)))
    stop("Official original physical sample columns incomplete; stop before response")
  if (!length(reserved_ids) || anyDuplicated(reserved_ids) ||
      !all(reserved_ids %in% names(realm_by_id)))
    stop("Reserved study list or realm provenance invalid")
  setDT(raw)
  # Only STUDY_ID controls i, and only strictly physical fields are selected by j.
  p <- raw[as.character(STUDY_ID) %in% reserved_ids,
    .(study=as.character(STUDY_ID),
      year=suppressWarnings(as.integer(YEAR)),
      month=suppressWarnings(as.integer(MONTH)),
      latitude=suppressWarnings(as.numeric(LATITUDE)),
      longitude=suppressWarnings(as.numeric(LONGITUDE)),
      event=as.character(SAMPLE_DESC))]
  p <- p[is.finite(latitude) & is.finite(longitude) &
         abs(latitude)<=90 & abs(longitude)<=180 &
         !is.na(year) & year>=1800L & year<=2026L &
         !is.na(month) & month>=1L & month<=12L &
         !is.na(event) & nzchar(trimws(event))]
  if (!nrow(p)) stop("Original reserved physical fields yield no valid event")
  p[,site:=paste0(sprintf("%.5f",latitude),",",sprintf("%.5f",longitude))]
  events <- unique(p[,.(study,site,year,month,event)])
  sy <- events[,.(n_events=.N),by=.(study,site,year,month)]
  site <- unique(sy[,.(study,site,year)])[,.(observed_years=.N),by=.(study,site)]
  ss <- site[,.(coordinate_sites=.N,
                 sites_at_least_3_years=sum(observed_years>=3L)),
             by="study"]
  right <- copy(sy)
  right[,year:=year-1L]
  setnames(right,"n_events","n_events_next")
  pa <- merge(sy,right,by=c("study","site","year","month"),all=FALSE)
  pair <- pa[n_events>=2L & n_events_next>=2L]
  pn <- pair[,.(strict_month_consecutive_pairs=.N,
                 unique_prior_years_in_eligible_pairs=uniqueN(year),
                 unique_sites_in_eligible_pairs=uniqueN(site)),
             by="study"]
  ss <- merge(ss,pn,by="study",all.x=TRUE)
  study <- data.table(study=reserved_ids,realm=unname(realm_by_id[reserved_ids]))
  ss <- merge(study,ss,by="study",all.x=TRUE)
  nums <- setdiff(names(ss),c("study","realm"))
  for (n in nums) set(ss,which(is.na(ss[[n]])),n,0L)
  ss[,physical_candidate:=(strict_month_consecutive_pairs>=10 &
                            sites_at_least_3_years>=5 &
                            unique_prior_years_in_eligible_pairs>=2)]
  setorder(ss,realm,study)

  by_realm <- ss[,.(reserved_studies=.N,
                     some_strict_pair=sum(strict_month_consecutive_pairs>0),
                     protocol_qualified_studies=sum(physical_candidate),
                     total_strict_month_pairs=sum(strict_month_consecutive_pairs)),
                by=.(realm)]
  setorder(by_realm,realm)
  totals <- list(reserved_studies=as.integer(nrow(ss)),
                 physical_studies_with_some_pair=as.integer(sum(ss$strict_month_consecutive_pairs>0L)),
                 physical_qualified_studies=as.integer(sum(ss$physical_candidate)),
                 strict_month_consecutive_pairs=as.numeric(sum(ss$strict_month_consecutive_pairs)),
                 site_at_least_three_years_across_studies=as.numeric(sum(ss$sites_at_least_3_years)))
  list(totals=totals,by_realm=by_realm,per_study=ss,
       source_read_columns=cols,
       source_taxon_abundance_response_accesses=0L,
       evidence_class="PHYSICAL_SITE_MONTH_YEAR_SUPPORT_ONLY",
       future_study_species_status="SEALED_NOT_OPENED")
}

main <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  if (length(args)!=5L) stop("Usage: Rscript physical.R source.rds split.json protocol.json summary.json studies.csv")
  src<-args[1]; split_file<-args[2]; protocol_file<-args[3]; json_out<-args[4]; csv_out<-args[5]
  proto<-jsonlite::fromJSON(protocol_file,simplifyVector=FALSE)
  split<-jsonlite::fromJSON(split_file,simplifyVector=FALSE)
  if (proto$schema!="structural.biotime_physical_holdout_gate.v1_253" ||
      proto$status!="RESPONSE_FREE_GATE_SPECIFIED_BEFORE_ANY_RESERVED_STUDY_SPECIES_VALUES" ||
      split$schema!="structural.biotime_v2_pilot_confirmatory_split.v1_251" ||
      proto$reserved_studies!=76L)
    stop("Frozen physical support gate or 19/76 disjoint split changed")
  realms <- c("Freshwater","Marine","Terrestrial")
  hold_by_realm <- lapply(realms,function(realm)
    as.character(unlist(split$realms[[realm]]$holdout,use.names=FALSE)))
  pilot <- as.character(unlist(lapply(realms,function(realm)
    split$realms[[realm]]$pilot),use.names=FALSE))
  hold <- as.character(unlist(hold_by_realm,use.names=FALSE))
  if (length(hold)!=76L || length(unique(hold))!=76L ||
      length(pilot)!=19L || any(hold %in% pilot))
    stop("Frozen disjoint study split invalid")
  if (unname(tools::md5sum(src))!=proto$source$expected_md5)
    stop("Original BioTIME RDS publisher checksum mismatch; fail closed")
  realm_by_id <- rep(realms,lengths(hold_by_realm))
  names(realm_by_id) <- hold
  print("Accessing only six physical sample columns in the reserved 76 studies; never taxon data.")
  raw <- readRDS(src)
  result <- audit_reserved_physical(raw,hold,realm_by_id)
  rm(raw);gc(verbose=FALSE)
  if (result$totals$reserved_studies!=76L ||
      any(!result$per_study$study %in% hold))
    stop("Physical reserved study result violates frozen identity")
  j <- list(schema="structural.biotime_v2_reserved_physical_support.v1_253",
            source_doi=proto$source$doi,source_rds_md5=proto$source$expected_md5,
            status="RESPONSE_OPAQUE_PHYSICAL_SUPPORT_AUDITED",
            new_confirmatory_study_species_endpoints_accessed=0L,
            original_mammal_holdout_accessed=FALSE,
            eBird_used=FALSE,GEB_scientific_HOLD=TRUE,
            qualifying_minimums=proto$study_quality_gate,
            totals=result$totals,by_realm=result$by_realm,
            source_read_columns=result$source_read_columns,
            next_action="Freeze calibration-only and geometry predictive estimands before ANY reserved taxa output")
  jsonlite::write_json(j,json_out,pretty=TRUE,auto_unbox=TRUE)
  fwrite(result$per_study,csv_out)
  print(result$totals)
  cat("No 76-study species/biomass/abundance fields queried; physical protocol only.\n")
}
if (sys.nframe()==0L) main()
