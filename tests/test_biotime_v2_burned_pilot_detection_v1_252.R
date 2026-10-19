#!/usr/bin/env Rscript
# Source-free fixture; tests the actual transition accountant, not reported flags.
suppressPackageStartupMessages(library(data.table))
source("scripts/biotime_v2_burned_pilot_detection_v1_252.R", local=TRUE)
obs <- list()
i <- 0L
add <- function(study, site, year, month, event, taxon, abundance=1) {
  i <<- i + 1L
  obs[[i]] <<- data.table(
    STUDY_ID=study, YEAR=year, MONTH=month, LATITUDE=as.numeric(site),
    LONGITUDE=10, SAMPLE_DESC=paste(site,year,month,event,sep="-"),
    newID=taxon,valid_name=taxon,resolution="species",
    ABUNDANCE=abundance,BIOMASS=NA_real_)
}
for (site in 1:3) for (year in 2020:2021) for (event in 1:2) {
  add("P",site,year,7,event,"background")
  if (year==2020 && site==1) add("P",site,year,7,event,"A")
  if (year==2021 && site==2) add("P",site,year,7,event,"A")
  if (year==2020 && site %in% c(1,2)) add("P",site,year,7,event,"B")
  if (year==2021 && site==1) add("P",site,year,7,event,"B")
  if (year==2021 && site==3) add("P",site,year,7,event,"new")
}
# "H" must not appear in pilot result, including the new taxon.
add("H",99,2020,7,1,"secret_taxon")
raw <- rbindlist(obs)
result <- pilot_detection_summary(raw, pilot_ids="P", realm_by_id=c(P="Terrestrial"))
group <- result$by_study_group
look <- function(grp, col) {
  x <- group[study=="P" & source_group==grp][[col]]
  if (!length(x)) stop(paste("Missing",grp,col))
  as.integer(x)
}
stopifnot(
  nrow(result$per_study)==1L,
  result$per_study$study=="P",
  look("1","n10")==1L,
  look("1","n01")==1L,
  look("1","n00")==1L,
  look("1","n11")==0L,
  look("1","n01_2plus")==1L,
  look("2","n11")==1L,
  look("2","n10")==1L,
  look("2","n00")==1L,
  look("3-4","n11")==3L,
  result$overall$target_site_month_year_pairs==3L,
  result$overall$n00==2L,
  result$overall$n01==1L,
  result$overall$n10==2L,
  result$overall$n11==4L,
  result$overall$eligible_species_pair_cells==9L,
  result$overall$unseen_prior_source_next_detections==1L,
  !any(grepl("secret",toJSON(result)))
)
cat("PASS pilot turnover synthetic: exact 9-cell transition accounting, replicated 01, 1 external new detection, no holdout leakage.\n")
