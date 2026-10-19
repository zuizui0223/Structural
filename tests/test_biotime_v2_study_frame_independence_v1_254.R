#!/usr/bin/env Rscript
# Synthetic fixture only. Proves the response-blind geographic network gate
# recognizes pilot/reserved shared sampling frames without opening fake species.
suppressPackageStartupMessages(library(data.table))
source("scripts/biotime_v2_study_frame_independence_v1_254.R",local=TRUE)
items <- list(); i<-0L
add <- function(study,site,year,month,event) {
  i<<-i+1L
  items[[i]]<<-data.table(
    STUDY_ID=study,YEAR=as.integer(year),MONTH=as.integer(month),
    LATITUDE=as.numeric(site),LONGITUDE=17.5,
    SAMPLE_DESC=paste(study,site,year,month,event,sep="-"),
    newID="MUST_NOT_READ_SEALED_TAXON",
    ABUNDANCE=9999,BIOMASS=9999
  )
}
for (site in 1:5) for (year in 2020:2022) for (event in 1:2) {
  add("P",site,year,7,event)
  add("H1",site,year,7,event)
  add("H3",site+20,year,7,event)
}
for (site in 1:5) for (year in 2024:2026) for (event in 1:2)
  add("H2",site,year,7,event)
data<-rbindlist(items)
realms<-c(P="Marine",H1="Marine",H2="Marine",H3="Freshwater")
result <- audit_frame_independence(data,"P",c("H1","H2","H3"),
                                   c("H1","H2","H3"),realms)
s<-result$report$results
stopifnot(
  s$all_studies==4L,
  s$original_burned_pilot_studies==1L,
  s$reserved_studies==3L,
  s$near_duplicate_frame_pairs==1L,
  s$shared_geography_pairs==3L,
  s$near_duplicate_cross_split_pairs==1L,
  s$shared_geography_cross_split_pairs==2L,
  s$near_duplicate_within_reserved_pairs==0L,
  s$shared_geography_within_reserved_pairs==1L,
  s$reserved_operator_min5_sites_count==3L,
  s$independent_qualifying_network_components_upper_bound==3L,
  all(result$study$active_strict_sites==5L),
  !any(grepl("MUST_NOT_READ_SEALED_TAXON",
      jsonlite::toJSON(result,auto_unbox=TRUE)))
)
r<-result$overlap[a=="H1" & b=="P"]
stopifnot(nrow(r)==1L,r$shared_sites==5L,r$shared_frames==15L,
          r$frame_jaccard==1,r$near_duplicate_frame)
r2<-result$overlap[a=="H1" & b=="H2"]
stopifnot(nrow(r2)==1L,r2$shared_sites==5L,r2$shared_frames==0L,
          r2$shared_geography,!r2$near_duplicate_frame)
stopifnot(nrow(result$overlap[a=="H3" | b=="H3"])==0)
cat("PASS synthetic shared-frame and pilot/reserved geometry dependency; no taxon fields accessed.\n")
