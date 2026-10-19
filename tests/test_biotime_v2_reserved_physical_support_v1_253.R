#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(data.table))
source("scripts/biotime_v2_reserved_physical_support_v1_253.R",local=TRUE)
z <- list(); k<-0L
add <- function(study,site,year,month,event,secret="sealed_response") {
  k <<- k+1L
  z[[k]] <<- data.table(
    STUDY_ID=study,LATITUDE=as.numeric(site),LONGITUDE=10.25,
    YEAR=year,MONTH=month,SAMPLE_DESC=paste(study,site,year,month,event,sep="-"),
    newID=secret, ABUNDANCE=9999)
}
for (site in 1:2) for (year in 2020:2022) for (event in 1:2)
  add("H1",site,year,7,event)
for (event in 1:2) {
  add("H2",3,2020,7,event)
  add("H2",3,2021,8,event)
}
for (site in 1:2) for (year in 2020:2021) for (event in 1:2)
  add("P",site,year,7,event,secret="prohibited pilot response")
d <- rbindlist(z)
result <- audit_reserved_physical(d,c("H1","H2"),c(H1="Terrestrial",H2="Marine"))
x <- result$per_study
stopifnot(
 nrow(x)==2L,
 x[study=="H1"]$strict_month_consecutive_pairs==4L,
 x[study=="H1"]$sites_at_least_3_years==2L,
 x[study=="H1"]$unique_prior_years_in_eligible_pairs==2L,
 x[study=="H2"]$strict_month_consecutive_pairs==0L,
 x[study=="H2"]$unique_prior_years_in_eligible_pairs==0L,
 result$totals$strict_month_consecutive_pairs==4L,
 result$totals$physical_studies_with_some_pair==1L,
 !any(grepl("sealed_response|prohibited pilot",jsonlite::toJSON(result)))
)
cat("PASS: pre-response strict-month holdout physical support, no taxon/count output.\n")
