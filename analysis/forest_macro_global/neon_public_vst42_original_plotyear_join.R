#!/usr/bin/env Rscript
# Forest macro: public, independently preserved RELEASE-2026 NEON woody
# structure plot/event metadata joined to public neonDivData 0.3.1 sampling
# metadata. NO beetle/plant biodiversity outcomes or tree-height regression.
#
# Pin public derived vegetation source at its completed 2026 release, not a
# mutable main/HEAD, and never fetch current restricted official NEON data API.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))

SOURCE_VST_REPO="tgilbert14/NEON-Vegetation-Structure-Explorer"
SOURCE_VST_COMMIT="3391e702e7be80a3f049c905782661f043be8db8"
OFFICIAL_SHA="d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461"

year <- function(x) {
  y<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  y[!(y%in%2019:2023)]<-NA_integer_
  y
}
source_forest <- function(x) {
  x<-tolower(gsub("[[:space:]_/-]+","",trimws(as.character(x))))
  x[is.na(x)]<-""
  x%in%c("evergreenforest","deciduousforest","mixedforest")
}
official_forest <- function(x) {
  vapply(strsplit(as.character(x),"|",fixed=TRUE),function(t){
     t<-trimws(t);t<-t[nzchar(t)]
     length(t)>0 && all(t%in%c("Evergreen Forest","Deciduous Forest","Mixed Forest"))
  },logical(1))
}
valid_plot <- function(x) !is.na(x)&nzchar(trimws(as.character(x)))
st <- function(d,keys){
  if(!all(keys%in%names(d)))
     stop(paste("SCIENTIFIC_STOP_PUBLISHED_SOURCE_META_SCHEMA",paste(setdiff(keys,names(d)),collapse=",")))
  d[,keys,drop=FALSE]
}
biodiversity_source_plotyears <- function(b,p,official) {
  keys_b<-c("siteID","plotID","observation_datetime","nlcdClass","trappingDays","trapConditionFlag","unique_sample_id","trapID")
  keys_p<-c("siteID","plotID","observation_datetime","nlcdClass","sample_area_m2","unique_sample_id")
  b<-st(b,keys_b);p<-st(p,keys_p)
  b$year<-year(b$observation_datetime)
  p$year<-year(p$observation_datetime)
  sites<-as.character(official$site_id[official_forest(official$dominant_nlcd_classes)])
  if(length(sites)<8)stop("SCIENTIFIC_STOP_NEON_OFFICIAL_FOREST_SITE_DENOMINATOR")
  b<-b[!is.na(b$year)&b$siteID%in%sites&source_forest(b$nlcdClass),,drop=FALSE]
  p<-p[!is.na(p$year)&p$siteID%in%sites&source_forest(p$nlcdClass),,drop=FALSE]
  bdays<-suppressWarnings(as.numeric(as.character(b$trappingDays)))
  flag<-as.character(b$trapConditionFlag)
  bb<-b[is.finite(bdays)&bdays>0&valid_plot(b$plotID)&
         valid_plot(b$unique_sample_id)&valid_plot(b$trapID)&
         (is.na(flag)|!nzchar(trimws(flag))),,drop=FALSE]
  pa<-suppressWarnings(as.numeric(as.character(p$sample_area_m2)))
  pp<-p[is.finite(pa)&abs(pa-1)<1e-9&valid_plot(p$plotID)&
        valid_plot(p$unique_sample_id),,drop=FALSE]
  makekey<-function(d)paste(d$siteID,d$plotID,d$year,sep="|")
  allowed<-intersect(unique(makekey(bb)),unique(makekey(pp)))
  originalsiteyears<-intersect(
    unique(paste(b$siteID,b$year,sep="|")),
    unique(paste(p$siteID,p$year,sep="|")))
  valid_sites<-intersect(unique(sub("\\|[^|]+\\|[0-9]{4}$","",allowed)),
        unique(sub("\\|[0-9]{4}$","",originalsiteyears)))
  if(length(valid_sites)!=8)stop("SCIENTIFIC_STOP_SOURCE_8_FOREST_SITE_JOIN_NOT_VERIFIED")
  list(plot_year_keys=allowed,site_codes=sort(valid_sites),
       coavailable_original_plot_years=length(allowed),
       original_observed_site_years=length(originalsiteyears))
}
vst_year <- function(d) {
  if("year"%in%names(d)) {
     y<-suppressWarnings(as.integer(as.character(d$year)))
     if(any(is.finite(y)))return(y)
  }
  for(k in c("date","eventDate","event_date","sampleDate")){
    if(k%in%names(d))return(year(d[[k]]))
  }
  rep(NA_integer_,nrow(d))
}
vst_source_meta <- function(path) {
  r<-readRDS(path)
  if(!is.list(r)||!all(c("plots","trees","opportunity_source","meta","contract")%in%names(r)))
    stop("SCIENTIFIC_STOP_PUBLIC_VST_RELEASE_BUNDLE_STRUCTURE_DRIFT")
  d<-r$plots
  if(!is.data.frame(d)||!all(c("plotID","eventID")%in%names(d)))
    stop("SCIENTIFIC_STOP_PUBLIC_VST_SOURCE_PLOT_EVENT_IDENTITY_DRIFT")
  hasdate<-("year"%in%names(d)||"date"%in%names(d)||"eventDate"%in%names(d))
  if(!hasdate)stop("SCIENTIFIC_STOP_VST_PLOT_OPPORTUNITY_YEAR_MISSING")
  yy<-vst_year(d)
  support_col<-if("tree_support"%in%names(d))"tree_support" else NA_character_
  area_col<-if("area_trees"%in%names(d))"area_trees" else NA_character_
  if(is.na(support_col)||is.na(area_col))
     stop("SCIENTIFIC_STOP_VST_EVENT_SUPPORT_OR_SAMPLE_AREA_MISSING")
  if(!is.data.frame(r$trees)||!"plotID"%in%names(r$trees))
     stop("SCIENTIFIC_STOP_VST_TREE_PLOT_JOIN_MISSING")
  rawareas<-suppressWarnings(as.numeric(as.character(d[[area_col]])))
  observed<-d[[support_col]]%in%c("sampled_with_records","sampled_absence")&
    is.finite(rawareas)&rawareas>0&!is.na(yy)&valid_plot(d$plotID)
  measured<-d[[support_col]]=="sampled_with_records"&observed
  plotyear<-paste(d$plotID,yy,sep="|")
  # Do not inspect actual plant height, canopy complexity, species, or DBH.
  contract<-r$contract
  contract_id<-if(is.list(contract)&&"id"%in%names(contract))as.character(contract$id) else NA_character_
  if(!identical(contract_id,"NEON-VST-DP1.10098.001-v2"))
     stop("SCIENTIFIC_STOP_VST_PUBLISHED_CONTRACT_VERSION_DRIFT")
  list(
     all_plotyears=unique(plotyear[!is.na(yy)&valid_plot(d$plotID)]),
     eligible_plotyears=unique(plotyear[observed]),
     measured_plotyears=unique(plotyear[measured]),
     original_rows=nrow(d),
     original_woody_measurement_rows_NOT_OUTCOME_READ=nrow(r$trees),
     original_woody_plant_height_field_declared="height"%in%names(r$trees),
     original_context_plot_event_ids=length(unique(paste(d$plotID,d$eventID,sep="|"))),
     eligible_opportunity_events=sum(observed),
     measured_tree_opportunity_events=sum(measured),
     original_context_year_range=range(yy[is.finite(yy)],na.rm=TRUE),
     source_QA_held_events=sum(!observed),
     source_field_names_metadata_ONLY=sort(names(d)),
     source_tree_field_names_metadata_ONLY=sort(names(r$trees))
  )
}
eligible_sites <- function(official) {
  z<-as.character(official$site_id[official_forest(official$dominant_nlcd_classes)])
  if(!length(z)||anyNA(z))stop("SCIENTIFIC_STOP_NO_AUTHORITATIVE_SITE_LIST")
  z
}
synthetic <- function(){
  stopifnot(all(source_forest(c("evergreenForest","mixedForest","Deciduous Forest"))),
            !any(source_forest(c("shrubScrub","NA","pastureHay"))),
            all(year(c("2019-01-01","2023-12-01"))==c(2019,2023)),
            is.na(year("2026-11-12")))
  cat("VST SOURCE SCHEMA synthetic forest class/year PASS\n")
}
if(identical(Sys.getenv("NEON_VST_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=3)stop("usage: Rscript neon_public_vst42_original_plotyear_join.R OFFICIAL_SITE_CSV PRIVATE_BUNDLES_DIRECTORY OUTPUT_DIRECTORY")
synthetic()
official<-read.csv(args[1],stringsAsFactors=FALSE,check.names=FALSE)
if(nrow(official)!=81||!all(c("site_id","dominant_nlcd_classes","domain_id")%in%names(official)))
 stop("SCIENTIFIC_STOP_NEON_OFFICIAL_81SITE_SOURCE_DRIFT")
source <- biodiversity_source_plotyears(
   neonDivData::data_beetle,neonDivData::data_plant,official)
store<-args[2];out<-args[3];dir.create(out,recursive=TRUE,showWarnings=FALSE)
summary<-list();support<-character()
for(site in source$site_codes){
  filepath<-file.path(store,paste0(site,".rds"))
  if(!file.exists(filepath))next
  r<-vst_source_meta(filepath)
  # r$plotyears use source VST plotID, align with observed source beetle/plant
  # plotID + year from the independently curated sampled products.
  vst<-paste(site,r$eligible_plotyears,sep="|")
  met<-paste(site,r$measured_plotyears,sep="|")
  joined<-intersect(vst,source$plot_year_keys)
  measurements<-intersect(met,source$plot_year_keys)
  support<-union(support,joined)
  summary[[site]]<-list(
    source_original_opportunity_event_rows=r$original_rows,
    source_woody_apparent_measurement_rows_NOT_USED_AS_BIODIVERSITY=r$original_woody_measurement_rows_NOT_OUTCOME_READ,
    source_plant_height_column_DECLARED_ONLY=r$original_woody_plant_height_field_declared,
    source_opportunity_supported_plotyears=length(r$eligible_plotyears),
    source_woody_measured_plotyears=length(r$measured_plotyears),
    cross_source_same_plot_year_supported_opportunity=length(joined),
    cross_source_same_plot_year_measured_woody_opportunity=length(measurements),
    original_context_year_range=r$original_context_year_range,
    source_vst_tree_support_status_held_events=r$source_QA_held_events,
    source_opportunity_coverage_NOT_A_BIODIVERSITY_EFFECT=TRUE
  )
}
matched<-length(support)
site_count<-sum(vapply(summary,function(x)x$cross_source_same_plot_year_supported_opportunity>0,logical(1)))
original_site_codes<-names(Filter(function(x)x$cross_source_same_plot_year_supported_opportunity>0,summary))
domain_count<-length(unique(official$domain_id[match(original_site_codes,official$site_id)]))
report<-list(
 schema="structural.NEON_vst2026_public42site_neonDivData0p3p1_plotyear_gate.v1",
 vetted_source_repo=SOURCE_VST_REPO,
 exact_source_commit=SOURCE_VST_COMMIT,
 upstream_NEON_vegetation_structure_product="DP1.10098.001",
 upstream_NEON_VST_release="RELEASE-2026",
 official_NEON_source_site_release="2026-08-05",
 published_neonDivData_release="0.3.1",
 historical_beetle_plant_strict_forest_sites=length(source$site_codes),
 historical_beetle_plant_sameplot_1m2_effort_plotyear_coavailability=source$coavailable_original_plot_years,
 forest_sites_with_public_VST_bundle=length(summary),
 forest_sites_with_sameplot_sameyear_supported_VST_woody_opportunity=site_count,
 domains_with_sameplot_sameyear_supported_VST_opportunity=domain_count,
 source_original_beetle_plant_VST_sameplot_sameyear_SUPPORTED_opportunity_count=matched,
 site_anonymous_VST_year_join_counts=unname(summary),
 actual_tree_height_abundance_or_species_values_NOT_INSPECTED=TRUE,
 tree_height_COLUMN_declared_in_all_loaded_VST_bundles=all(vapply(summary,function(x)x$source_plant_height_column_DECLARED_ONLY,logical(1))),
 forest_structure_does_not_imply_site_microclimate=TRUE,
 original_NEON_source_site_area_and_woody_channels_are_QA_filtered=TRUE,
 public_VST_bundle_not_equal_current_token_required_NEON_API=TRUE,
 source_site_plot_tree_species_measurements_NOT_REEXPORTED=TRUE,
 plant_zero_absence_not_inferred_from_neonDivData=TRUE,
 no_independent_canopy_mechanism_or_biological_effect_claim=TRUE,
 metadata_source_stop_if_fewer_than_six_independent_forest_sites=site_count<6,
 eBird_used=FALSE
)
path<-file.path(out,"neon_public_vst_release2026_plotyear_sourceonly.json")
writeLines(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),path)
cat(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
