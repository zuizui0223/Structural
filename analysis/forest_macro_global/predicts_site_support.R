#!/usr/bin/env Rscript
# Global forest macroecology: original PREDICTS public site-level support audit.
# This AUDITS, does not model ecology. It does not open the 4.3M taxon records,
# does not invent an independent set of forest sites, and does not redistribute
# the NHM's CC non-commercial underlying location records.
#
# Input = predictsr::GetSitelevelSummaries(c(2016,2022)) (2016+2022 extracts).
# Source: NHM PREDICTS Data Portal; data license CC noncommercial.
suppressPackageStartupMessages(library(predictsr))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Usage: Rscript predicts_global_forest_support.R OUTDIR")
outdir <- args[[1]]; dir.create(outdir, recursive=TRUE, showWarnings=FALSE)

norm <- function(x) {
  v <- tolower(trimws(as.character(x)))
  v[is.na(v)] <- ""
  gsub("[[:space:]]+", " ", v)
}
col <- function(d, n) if (n %in% names(d)) as.character(d[[n]]) else rep(NA_character_,nrow(d))
tab <- function(d, filename) write.csv(d,file.path(outdir,filename),row.names=FALSE,na="")
nuniq <- function(x) length(unique(x[!is.na(x) & x!=""]))
year_of <- function(x) {
  y <- suppressWarnings(as.integer(substr(as.character(x),1,4)))
  y[y<1900 | y>2100] <- NA_integer_
  y
}
is_forest_text <- function(x) {
  # Explicit actual local habitat terms, not biome designation alone.
  grepl("forest|woodland|mangrove|laurel", norm(x))
}
first_nonempty <- function(x) {
  v <- x[!is.na(x)&x!=""]
  if(length(v)) v[[1]] else ""
}
make_report <- function(d) {
  required <- c("Source_ID","Study_number","Site_number",
    "Predominant_land_use","Habitat_as_described","Biome","Realm",
    "Country","Latitude","Longitude","Sampling_method","Sample_midpoint")
  missing <- setdiff(required,names(d))
  if(length(missing)) stop(paste("PREDICTS site summary schema missing:",paste(missing,collapse=", ")))
  if(nrow(d) == 0L) stop("Source PREDICTS site summary empty")
  rawkey <- paste(col(d,"Source_ID"),col(d,"Study_number"),
    col(d,"Block"),col(d,"Site_number"),sep="|")
  skey <- if ("SSBS" %in% names(d)) as.character(d[["SSBS"]]) else rawkey
  study <- if ("SS" %in% names(d)) as.character(d[["SS"]]) else
    paste(col(d,"Source_ID"),col(d,"Study_number"),sep="|")
  if (any(is.na(skey)|skey=="")) stop("Source original SSBS/site key missing; cannot establish grain")
  if (any(is.na(study)|study=="")) stop("Source original study identity missing")
  if (nuniq(skey) < .95*nrow(d)) stop("PREDICTS site summary contains too many repeated site identities; grain audit STOP")
  method <- norm(col(d,"Sampling_method"))
  taxon <- norm(col(d,"Study_common_taxon"))
  landuse <- norm(col(d,"Predominant_land_use"))
  intensity <- norm(col(d,"Use_intensity"))
  biome <- norm(col(d,"Biome"))
  hab <- norm(col(d,"Habitat_as_described"))
  realm <- as.character(col(d,"Realm"))
  country <- as.character(col(d,"Country"))
  yr <- year_of(col(d,"Sample_midpoint"))
  lat <- suppressWarnings(as.numeric(col(d,"Latitude")))
  lon <- suppressWarnings(as.numeric(col(d,"Longitude")))
  coord <- is.finite(lat) & is.finite(lon) & abs(lat)<=90 & abs(lon)<=180
  # Biome ≠ plot vegetation. Report an explicit-local-habitat frame and
  # a broader support ceiling in parallel, never call one the other.
  forest_biome <- grepl("forest|taiga|woodland",biome)
  explicit_forest <- is_forest_text(hab)
  vegetated_land <- grepl("^primary vegetation|^secondary vegetation|^plantation forest",landuse)
  strict <- forest_biome & explicit_forest & vegetated_land
  broad <- forest_biome & vegetated_land
  controls <- strict & grepl("^primary vegetation",landuse) &
    grepl("minimal|light",intensity)
  # Reference vs altered forest only within exact original study and method/taxon.
  plot_class <- ifelse(grepl("^primary vegetation",landuse),"primary",
    ifelse(grepl("^secondary vegetation",landuse),"secondary",
      ifelse(grepl("^plantation forest",landuse),"plantation","other")))
  stratum <- paste(study,method,taxon,sep="|")
  forest <- data.frame(study=study,skey=skey,stratum=stratum,
    country=country,realm=realm,biome=as.character(col(d,"Biome")),
    method=method,taxon=taxon,landuse=plot_class,strict=strict,
    broad=broad,reference=controls,coord=coord,year=yr,
    stringsAsFactors=FALSE)
  forest <- forest[!duplicated(forest$skey),,drop=FALSE]
  if(!nrow(forest)) stop("All site-level records were discarded by duplicate checking")
  f <- forest[forest$strict,,drop=FALSE]
  group <- unique(f$stratum)
  has_ref <- sapply(group,function(s) sum(f$stratum==s & f$reference)>=2)
  has_other <- sapply(group,function(s) sum(f$stratum==s & f$landuse %in% c("secondary","plantation"))>=2)
  paired <- group[has_ref & has_other]
  f$paired_study_taxon_method <- f$stratum %in% paired
  # Non-secret compact coverage outputs. No coordinates or source site IDs.
  summarize_group <- function(indices, groupname){
    v <- forest[indices,,drop=FALSE]
    if (!nrow(v)) return(data.frame(group=groupname,sites=0L,
      studies=0L,countries=0L,years=0L,methods=0L,
      coord_valid=0L,year_2018_or_later=0L,year_2019_or_later=0L,
      stringsAsFactors=FALSE))
    data.frame(group=groupname,sites=nuniq(v$skey),
      studies=nuniq(v$study),countries=nuniq(v$country),years=nuniq(as.character(v$year)),
      methods=nuniq(v$method),coord_valid=sum(v$coord),
      year_2018_or_later=sum(!is.na(v$year)&v$year>=2018),
      year_2019_or_later=sum(!is.na(v$year)&v$year>=2019),
      stringsAsFactors=FALSE)
  }
  overall <- do.call(rbind,list(
    summarize_group(rep(TRUE,nrow(forest)),"all_PREDICTS_site_level"),
    summarize_group(forest$broad,"broad_biome_landuse_ceiling"),
    summarize_group(forest$strict,"explicit_site_forest"),
    summarize_group(forest$reference,"explicit_forest_primary_minimal_or_light"),
    summarize_group(forest$skey %in% f$skey[f$paired_study_taxon_method],
      "explicit_forest_within_study_reference_vs_altered"),
    summarize_group(forest$strict & forest$coord & !is.na(forest$year) & forest$year>=2019,
      "explicit_forest_observed_2019_or_later")
  ))
  tab(overall,"global_source_support.csv")
  do_group <- function(x,colname) {
    x <- x[x$strict,,drop=FALSE]
    if(!nrow(x)) return(data.frame())
    split_data <- split(x,ifelse(is.na(x[[colname]])|x[[colname]]=="","(missing)",x[[colname]]))
    do.call(rbind,lapply(names(split_data),function(n){
      z<-split_data[[n]]
      data.frame(group=n,original_study_sites=nuniq(z$skey),
        independent_studies=nuniq(z$study),countries=nuniq(z$country),
        have_valid_coordinates=sum(z$coord),
        study_method_taxon_reference_contrasts=nuniq(z$stratum[z$paired_study_taxon_method]),
        year_2019_or_later=sum(!is.na(z$year)&z$year>=2019),
        stringsAsFactors=FALSE)
    }))
  }
  by_biome<-do_group(forest,"biome")
  by_realm<-do_group(forest,"realm")
  by_country<-do_group(forest,"country")
  if(nrow(by_biome)) tab(by_biome,"support_by_biome.csv")
  if(nrow(by_realm)) tab(by_realm,"support_by_realm.csv")
  if(nrow(by_country)) tab(by_country,"support_by_country.csv")
  methods <- sort(table(f$method),decreasing=TRUE)
  tab(data.frame(method=names(methods),strict_forest_site_rows=as.integer(methods)),
      "sampling_method_coverage.csv")
  tax <- sort(table(f$taxon),decreasing=TRUE)
  tab(data.frame(common_taxon=names(tax),strict_forest_site_rows=as.integer(tax)),
      "taxonomic_coverage.csv")
  coord_method <- sort(table(norm(col(d,"Coordinates_method"))),decreasing=TRUE)
  tab(data.frame(original_source_coordinates_method=names(coord_method),
      original_site_level_rows=as.integer(coord_method)),
      "coordinate_method_coverage.csv")
  # Important: spatial location methods including centroids/georeferencing
  # are NOT declared 10m precise by this data source.
  # Sample date and land-use counts exposed for validity checks.
  lu <- sort(table(landuse),decreasing=TRUE)
  tab(data.frame(original_land_use=names(lu),site_rows=as.integer(lu)),
      "source_landuse_vocabulary.csv")
  db <- list(schema="structural.forest_macro_PREDICTS_public_site_support.v1",
    source="NHM PREDICTS original public 2016+2022 site summaries via predictsr",
    release=c(2016,2022),
    n_original_source_site_summary_rows=nrow(d),
    n_original_source_columns=ncol(d),
    source_fields=names(d),
    original_site_key="SSBS if provided, else original Source_ID|Study_number|Block|Site_number",
    original_site_distinct_n=nuniq(skey),
    original_site_key_duplicate_row_count=nrow(d)-nuniq(skey),
    n_study_method_taxon_strata_with_min2_reference_min2_altered=length(paired),
    forest_eligibility_rule="Forest-like Biome AND explicit forest/woodland/mangrove/laurel original local Habitat_as_described AND source original primary/secondary vegetation or plantation forest",
    forest_biome_is_not_site_forest=TRUE,
    spatial_precision_gates_NOT_PASSED=TRUE,
    original_2020_canopy_height_is_not_contemporaneous_with_historic_samples=TRUE,
    original_source_biological_4million_records_read=FALSE,
    counts_for_forest_and_biome_are_deduplicated_by_original_source_site_key=TRUE,
    original_source_site_records_are_not_all_independent_forest_studies=TRUE,
    no_global_ecological_effect_or_validation_claim=TRUE,
    source_reference_code="https://github.com/Biodiversity-Futures-Lab/predictsr",
    original_source_data_license="2016 CC BY-NC-SA 4.0, 2022 CC NC (non-commercial)",
    global_report=overall)
  writeLines(jsonlite::toJSON(db,pretty=TRUE,auto_unbox=TRUE,null="null"),
             file.path(outdir,"quality_manifest.json"))
  if(sum(forest$strict)>0 && length(paired)==0)
    message("Scientific result: explicit forest sites exist but no within-study matched primary/altered contrasts under strict definition.")
  db
}
if (identical(Sys.getenv("FOREST_MACRO_SYNTHETIC_ONLY"),"1")) {
  # Run a small known-truth test before the real original site download.
  demo <- data.frame(Source_ID=c(rep("A",5),rep("B",4)),
    Study_number=1,Site_number=seq_len(9),Block="",
    Habitat_as_described=c(rep("forest",8),"grassland"),
    Predominant_land_use=c("Primary vegetation","Primary vegetation",
      "Secondary vegetation","Secondary vegetation","Plantation forest",
      "Primary vegetation","Primary vegetation","Secondary vegetation","Secondary vegetation"),
    Biome="Tropical & Subtropical Moist Broadleaf Forests",
    Realm=c(rep("Neotropic",5),rep("Afrotropic",4)),
    Country=c(rep("A_country",5),rep("B_country",4)),
    Sampling_method="pitfall",Study_common_taxon="Invertebrates",
    Latitude=0,Longitude=10,Sample_midpoint="2015-01-01",
    Use_intensity="Minimal use",stringsAsFactors=FALSE)
  x <- make_report(demo)
  stopifnot(nrow(x$global_report)==6L,
    x$n_study_method_taxon_strata_with_min2_reference_min2_altered==1L)
  cat("PASS: explicit forest vs biome, original study×method×taxon, and held-out 2015 year synthetic audit\n")
  quit(status=0)
}
cat("Requesting official original PREDICTS site-level 2016/2022 releases only.\n")
data <- predictsr::GetSitelevelSummaries(extract=c(2016,2022))
if(!is.data.frame(data)) stop("NHM PREDICTS API did not supply a data.frame")
report <- make_report(data)
cat("ORIGINAL SOURCE rows:",report$n_original_source_site_summary_rows,
    "distinct site keys:",report$original_site_distinct_n,
    "strict matched original study strata:",report$n_study_method_taxon_strata_with_min2_reference_min2_altered,"\n")
print(report$global_report,row.names=FALSE)
