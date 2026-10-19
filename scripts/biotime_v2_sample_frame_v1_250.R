#!/usr/bin/env Rscript
# Design-exposed retrospective SOURCE FRAME ONLY. No taxa/abundance/biomass
# fields are referenced; original RDS necessarily materialized in memory.
# Do not claim true absence, colonization, migration, fresh confirmation.

args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 3L) stop("Usage: Rscript ...source_frame.R original.rds metadata.csv result.csv")
data_file <- args[1]; metadata_file <- args[2]; out_file <- args[3]
suppressPackageStartupMessages(library(data.table))

meta <- fread(metadata_file, encoding="UTF-8")
required_meta <- c("STUDY_ID","START_YEAR","END_YEAR","NUMBER_LAT_LONG",
                   "NUMBER_OF_SAMPLES","NUMBER_OF_SPECIES","REALM")
if (!all(required_meta %in% names(meta))) stop("Original BioTIME metadata fields changed")
nspan <- as.numeric(meta$END_YEAR) - as.numeric(meta$START_YEAR) + 1
initial <- meta[
  nspan >= 5 & as.numeric(NUMBER_LAT_LONG) >= 10 &
  as.numeric(NUMBER_OF_SAMPLES) >= 100 & as.numeric(NUMBER_OF_SPECIES) >= 10
]
if (nrow(meta) != 708 || nrow(initial) != 226 ||
    uniqueN(meta$STUDY_ID) != 708) stop("Frozen 708/226 metadata screen mismatch")
ids <- as.character(initial$STUDY_ID)

cat("Reading original publisher-MD5-locked BioTIME RDS for physical sample frame only\n")
raw <- readRDS(data_file)
if (!is.data.frame(raw)) stop("Unexpected RDS object class; no fallback data")
required <- c("STUDY_ID","YEAR","LATITUDE","LONGITUDE","SAMPLE_DESC")
if (!all(required %in% names(raw))) stop(paste("Original RDS missing",paste(setdiff(required,names(raw)),collapse=",")))
if (!("MONTH" %in% names(raw))) raw$MONTH <- NA_integer_

# Only physical sampling-event fields may be selected. No species labels or
# values are accessed or counted, despite loaded published source in memory.
setDT(raw)
frame <- raw[as.character(STUDY_ID) %in% ids,
             .(STUDY_ID=as.character(STUDY_ID), YEAR=as.integer(YEAR),
               LATITUDE=as.numeric(LATITUDE),LONGITUDE=as.numeric(LONGITUDE),
               MONTH=as.integer(MONTH),SAMPLE_DESC=as.character(SAMPLE_DESC))]
rm(raw); invisible(gc())
frame <- frame[!is.na(YEAR) & YEAR>=1800 & YEAR<=2026 &
               !is.na(LATITUDE) & !is.na(LONGITUDE) &
               is.finite(LATITUDE) & is.finite(LONGITUDE) &
               abs(LATITUDE)<=90 & abs(LONGITUDE)<=180]
# A coordinate-derived SITE proxy is NOT a confirmed permanent plot identity.
frame[,site_proxy:=paste0(sprintf("%.5f", LATITUDE),",",sprintf("%.5f", LONGITUDE))]
ev <- unique(frame[,.(STUDY_ID,site_proxy,YEAR,MONTH,SAMPLE_DESC)])
rm(frame); invisible(gc())
ev <- ev[!is.na(SAMPLE_DESC) & nzchar(SAMPLE_DESC)]
if (!nrow(ev)) stop("No valid spatially localized sampling event keys")
sy <- ev[,.(n_events=.N,
            month_mask=sum(2^(unique(MONTH[!is.na(MONTH) & MONTH>=1 & MONTH<=12])-1))),
         by=.(STUDY_ID,site_proxy,YEAR)]
rm(ev); invisible(gc())
site <- sy[,.(observed_years=.N,
              consecutive_year_pairs=sum(diff(sort(YEAR))==1),
              total_events=sum(n_events)),
           by=.(STUDY_ID,site_proxy)]
summary <- site[,.(coordinate_sites=.N,
                   sites_at_least_three_observed_years=sum(observed_years>=3),
                   sites_at_least_five_observed_years=sum(observed_years>=5),
                   sites_with_consecutive_years=sum(consecutive_year_pairs>0),
                   total_consecutive_site_year_pairs=sum(consecutive_year_pairs),
                   unique_site_years=sum(observed_years),
                   total_sample_events=sum(total_events)),
                by="STUDY_ID"]

# Opposed pairs of physical time points; still NOT confirmed identical methods.
next_year <- sy[,.(STUDY_ID,site_proxy,YEAR=YEAR-1L,
                    next_mask=month_mask, next_events=n_events)]
pairs <- merge(sy,next_year,by=c("STUDY_ID","site_proxy","YEAR"),all=FALSE)
if (nrow(pairs)) {
  pairs[, same_calendar_month:=bitwAnd(as.integer(month_mask),as.integer(next_mask))>0]
  pair_by_study <- pairs[,.(raw_consecutive_pairs=.N,
                            same_month_consecutive_pairs=sum(same_calendar_month),
                            same_month_pairs_each_visit_2plus=sum(same_calendar_month & n_events>=2 & next_events>=2)),
                         by="STUDY_ID"]
  summary <- merge(summary,pair_by_study,by="STUDY_ID",all.x=TRUE)
}
for (col in c("raw_consecutive_pairs","same_month_consecutive_pairs","same_month_pairs_each_visit_2plus")) {
  if (!(col %in% names(summary))) summary[,(col):=0L]
  set(summary, which(is.na(summary[[col]])),col,0L)
}
summary <- merge(initial[,.(STUDY_ID=as.character(STUDY_ID),REALM,
                           START_YEAR,END_YEAR,NUMBER_LAT_LONG,NUMBER_OF_SAMPLES,
                           NUMBER_OF_SPECIES)],summary,by="STUDY_ID",all.x=TRUE)
for (nm in c("coordinate_sites","sites_at_least_three_observed_years",
             "sites_at_least_five_observed_years","sites_with_consecutive_years",
             "total_consecutive_site_year_pairs","unique_site_years",
             "total_sample_events","raw_consecutive_pairs",
             "same_month_consecutive_pairs","same_month_pairs_each_visit_2plus")) {
  set(summary,which(is.na(summary[[nm]])),nm,0L)
}
if (nrow(summary) != 226 || uniqueN(summary$STUDY_ID)!=226)
  stop("Frozen 226-study physical-frame count mismatch")
setorder(summary,STUDY_ID)
fwrite(summary,out_file,na="")
cat(sprintf("SOURCE FRAME ONLY: %s studies, %s with >=3 observed site-years, %s with same-month next-year site pairs.\n",
    nrow(summary),
    sum(summary$sites_at_least_three_observed_years>0),
    sum(summary$same_month_consecutive_pairs>0)))
cat("No taxon response, sampled absences, 0->1 events, donor movement or model score computed.\n")
