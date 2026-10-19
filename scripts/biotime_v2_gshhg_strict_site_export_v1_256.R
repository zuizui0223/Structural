#!/usr/bin/env Rscript
# Geometry-only export for the 33 conserved BioTIME study networks.
# The original publisher RDS can contain species observations but ONLY these
# six physical survey fields are selected; no biological response is opened.
suppressPackageStartupMessages(library(data.table))
main <- function() {
  args<-commandArgs(trailingOnly=TRUE)
  if (length(args)!=4L)
    stop("Usage: Rscript ... physical.R original.rds v1_255.json v1_256.json sites.csv")
  src<-args[1L];cohort_path<-args[2L];protocol_path<-args[3L];out<-args[4L]
  p<-jsonlite::fromJSON(protocol_path,simplifyVector=FALSE)
  c<-jsonlite::fromJSON(cohort_path,simplifyVector=FALSE)
  if (p$schema!="structural.biotime_gshhg_island_crosswalk_protocol.v1_256" ||
      p$status!="FROZEN_BEFORE_NEW_GEOGRAPHY_ONLY_ISLAND_CROSSWALK" ||
      c$schema!="structural.biotime_v2_conservative_network_cohort.v1_255" ||
      unname(tools::md5sum(src))!=p$biotime_source$rds_md5)
    stop("Frozen source, cohort or geography protocol mismatch")
  realms<-c("Freshwater","Marine","Terrestrial")
  by_realm<-lapply(realms,function(r)
     as.character(unlist(c$selected_study_ids_by_realm[[r]],use.names=FALSE)))
  ids<-as.character(unlist(by_realm,use.names=FALSE))
  if (length(ids)!=33L || anyDuplicated(ids))
    stop("Expected exactly 33 preselected response-blind study network proxies")
  realm_by<-rep(realms,lengths(by_realm));names(realm_by)<-ids
  raw<-readRDS(src)
  needed<-c("STUDY_ID","YEAR","MONTH","LATITUDE","LONGITUDE","SAMPLE_DESC")
  if (!all(needed %in% names(raw)))
    stop("Missing original physical survey key columns")
  setDT(raw)
  dt<-raw[as.character(STUDY_ID) %in% ids,
    .(study=as.character(STUDY_ID),year=suppressWarnings(as.integer(YEAR)),
      month=suppressWarnings(as.integer(MONTH)),
      lat=suppressWarnings(as.numeric(LATITUDE)),
      lon=suppressWarnings(as.numeric(LONGITUDE)),
      event=as.character(SAMPLE_DESC))]
  rm(raw);gc(verbose=FALSE)
  dt<-dt[!is.na(year) & year>=1800 & year<=2026 &
         !is.na(month) & month>=1 & month<=12 &
         is.finite(lat) & is.finite(lon) & abs(lat)<=90 & abs(lon)<=180 &
         !is.na(event) & nzchar(trimws(event))]
  if (!nrow(dt))stop("No valid physical data")
  dt[,site:=paste0(sprintf("%.5f",lat),",",sprintf("%.5f",lon))]
  ev<-unique(dt[,.(study,site,year,month,event)])
  rm(dt);gc(verbose=FALSE)
  sy<-ev[,.(event_n=.N),by=.(study,site,year,month)]
  nxt<-copy(sy)
  nxt[,year:=year-1L]
  setnames(nxt,"event_n","next_event_n")
  pair<-merge(sy,nxt,by=c("study","site","year","month"),all=FALSE)
  pair<-pair[event_n>=2L & next_event_n>=2L]
  if (!nrow(pair))stop("No prospectively frozen strict site/year/month comparisons")
  a<-pair[,.(strict_matched_pair_n=.N,distinct_matched_years=uniqueN(year)),
          by=.(study,site)]
  locations<-tstrsplit(a$site,",",fixed=TRUE)
  a[,latitude:=as.numeric(locations[[1L]])]
  a[,longitude:=as.numeric(locations[[2L]])]
  a[,realm:=unname(realm_by[study])]
  if(anyNA(a$realm)||uniqueN(a$study)!=33L)
    stop("33-response-free study network proxies lack physical support")
  if(any(a[,.(n=.N),by=study]$n<5L))
    stop("One of the prequalified 33 study geometries has fewer than five distinct sites")
  setorder(a,realm,study,site)
  fwrite(a[,.(study,realm,latitude,longitude,strict_matched_pair_n,
              distinct_matched_years)],out)
  print(a[,.(sites=.N,physical_pairs=sum(strict_matched_pair_n)),
          by=.(realm,study)])
  cat("33 network representative study coordinate lists derived from SIX physical columns only. No taxa opened.\n")
}
if (sys.nframe()==0L) main()
