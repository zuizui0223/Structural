#!/usr/bin/env Rscript
# Source-structure-only quality diagnostic for published 2026 NEON VST
# original matched forest-patch plot-years. Never open beetle/plant taxa,
# values, canopy cause, biodiversity, or microclimate.
# Original site/plot/year keys stay local to Actions and are NOT exported.

forest_plot<-function(z){
  x<-tolower(gsub("[[:space:]_/-]+","",trimws(as.character(z))))
  x[is.na(x)]<-""
  x%in%c("evergreenforest","deciduousforest","mixedforest")
}
calendar_year<-function(z){
  y<-suppressWarnings(as.integer(substr(as.character(z),1,4)))
  y[!(y%in%2019:2023)]<-NA_integer_
  y
}
valid_name<-function(z) !is.na(z)&nzchar(trimws(as.character(z)))
original_VST_height_qualifying_plant_counts<-function(r,matched) {
  if(!all(c("plots","trees","contract")%in%names(r)) ||
     !identical(as.character(r$contract$id),"NEON-VST-DP1.10098.001-v2"))
    stop("SCIENTIFIC_STOP_ORIGINAL_PUBLISHED_VST_CONTRACT")
  q<-r$plots;t<-r$trees
  reqplot<-c("plotID","eventID","tree_support","area_trees","nlcdClass")
  reqtree<-c("plotID","eventID","individualID","height",
             "stemDiameter","growthForm")
  if(!all(reqplot%in%names(q))||!all(reqtree%in%names(t)))
    stop("SCIENTIFIC_STOP_PUBLISHED_ORIGINAL_VST_TREE_EVENT_METRIC_SCHEMA")
  y<-if("year"%in%names(q))suppressWarnings(as.integer(as.character(q$year))) else
       if("date"%in%names(q))calendar_year(q$date) else
       stop("SCIENTIFIC_STOP_PUBLISHED_VST_SOURCE_EVENT_YEAR")
  sampled_area<-suppressWarnings(as.numeric(as.character(q$area_trees)))
  eligible<-forest_plot(q$nlcdClass) & !is.na(y)& y%in%2019:2023&
    q$tree_support=="sampled_with_records" &
    is.finite(sampled_area)&sampled_area>0&
    valid_name(q$plotID)&valid_name(q$eventID)
  q<-q[which(eligible),,drop=FALSE]
  y<-y[which(eligible)]
  if(!nrow(q))return(list(counts=integer(),siteplotyear=character(),
                         raw_source_tree_rows=0L,raw_source_height_qualifying_plant_keys=0L))
  eventkey<-paste(q$plotID,q$eventID,sep="|")
  years_by_event<-setNames(y,eventkey)
  # If distinct source event rows contain repeated operational locators
  # with conflicting years, do not pick one by source ordering.
  if(anyDuplicated(eventkey)){
     grouped<-split(y,eventkey)
     if(any(vapply(grouped,function(z)length(unique(z))>1,logical(1))))
         stop("SCIENTIFIC_STOP_VST_PLOT_EVENT_IDENTITY_YEAR_CONFLICT")
     years_by_event<-vapply(grouped,function(z)z[1],integer(1))
  }
  tkey<-paste(t$plotID,t$eventID,sep="|")
  eventyear<-years_by_event[tkey]
  sourced<-!is.na(eventyear)
  h<-suppressWarnings(as.numeric(as.character(t$height)))
  dbh<-suppressWarnings(as.numeric(as.character(t$stemDiameter)))
  is_tree<-tolower(trimws(as.character(t$growthForm)))%in%
        c("single bole tree","multi-bole tree")
  # Any explicit canonical source height QC hold is respected. We do not
  # create a new tree-height smoothing or extrapolation function.
  height_quality<-if("size_height_ok"%in%names(t)) {
     as.logical(t$size_height_ok)%in%TRUE
  } else rep(TRUE,nrow(t))
  if("live"%in%names(t)) {
    live<-as.logical(t$live)%in%TRUE
  } else if("plantStatus"%in%names(t)) {
    live<-tolower(trimws(as.character(t$plantStatus)))=="live"
  } else {
    stop("SCIENTIFIC_STOP_NO_VST_SOURCE_LIVE_STATUS_FIELD")
  }
  okay<-sourced & is.finite(h)&h>0 & is.finite(dbh)&dbh>=10 &
      is_tree&height_quality&live&valid_name(t$individualID)
  if(!any(okay))return(list(counts=integer(),siteplotyear=character(),
                           raw_source_tree_rows=sum(sourced),
                           raw_source_height_qualifying_plant_keys=0L))
  vals<-paste(t$plotID[okay],eventyear[okay],sep="|")
  # Repeated stems of the same physical source plant are NOT independent.
  plants<-paste(vals,t$individualID[okay],sep="|")
  distinct<-!duplicated(plants)
  counts<-table(vals[distinct])
  list(counts=counts,siteplotyear=names(counts),
       raw_source_tree_rows=sum(sourced),
       raw_source_height_qualifying_plant_keys=sum(distinct))
}
synthetic<-function(){
  plot<-data.frame(
     plotID=c("S000_1","S000_2","S000_1"),
     eventID=c("E1","E2","E3"),
     year=c(2020,2020,2021),
     nlcdClass=c("mixedForest","mixedForest","mixedForest"),
     tree_support=c("sampled_with_records","held_sampling_impractical","sampled_with_records"),
     area_trees=c(400,400,400))
  trees<-data.frame(
     plotID=c("S000_1","S000_1","S000_1","S000_2","S000_1"),
     eventID=c("E1","E1","E1","E2","E3"),
     individualID=c("I1","I1","I2","I3","I4"),
     height=c(12,13,8,20,14),
     stemDiameter=c(15,16,13,20,11),
     growthForm="single bole tree",live=TRUE,
     size_height_ok=TRUE)
  r<-list(plots=plot,trees=trees,
          contract=list(id="NEON-VST-DP1.10098.001-v2"))
  q<-original_VST_height_qualifying_plant_counts(r,character())
  stopifnot(sum(q$counts)==3,
            q$counts[["S000_1|2020"]]==2,
            q$counts[["S000_1|2021"]]==1,
            q$raw_source_tree_rows==4,
            q$raw_source_height_qualifying_plant_keys==3)
  trees$size_height_ok[3]<-FALSE
  r$trees<-trees
  assert<-original_VST_height_qualifying_plant_counts(r,character())
  stopifnot(assert$counts[["S000_1|2020"]]==1)
  cat("Forest VST sampled-opportunity and unique-live-DBH height availability known truth PASS\n")
}
if(identical(Sys.getenv("NEON_VST_HEIGHT_SOURCE_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=4)stop("usage: Rscript neon_public_vst2026_forestpatch_height_quality_gate.R PRIVATE_VST_BUNDLE_DIR PRIVATE_MATCHED_PLOTYEAR_KEYS OFFICIAL_SITE_CSV AGGREGATE_OUT")
synthetic()
files<-sort(list.files(args[1],pattern="^[A-Z0-9]{4}\\.rds$",full.names=TRUE))
if(!length(files))stop("SCIENTIFIC_STOP_PUBLISHED_VST_BUNDLE_FILES_MISSING")
target<-readLines(args[2],warn=FALSE)
if(length(target)!=74||anyDuplicated(target))
  stop("SCIENTIFIC_STOP_FROZEN_74_ORIGINAL_WOODY_MATCHED_KEYS_CHANGED")
official<-read.csv(args[3],stringsAsFactors=FALSE,check.names=FALSE)
if(nrow(official)!=81 || !all(c("site_id","domain_id","dominant_nlcd_classes")%in%names(official)))
  stop("SCIENTIFIC_STOP_OFFICIAL_NEON_FIELD_SITE_OR_DOMAIN_SOURCE_CHANGED")
plotkeys<-character()
all_counts<-list();source_tree_rows<-0L;source_height_plants<-0L
for(file in files){
  site<-sub("\\.rds$","",basename(file))
  r<-readRDS(file)
  z<-original_VST_height_qualifying_plant_counts(r,target)
  source_tree_rows<-source_tree_rows+z$raw_source_tree_rows
  source_height_plants<-source_height_plants+z$raw_source_height_qualifying_plant_keys
  ks<-paste(site,z$siteplotyear,sep="|")
  aligned<-intersect(ks,target)
  if(length(aligned)){
    ix<-match(sub(paste0("^",site,"\\|"),"",aligned),z$siteplotyear)
    vals<-as.integer(z$counts[ix])
    names(vals)<-aligned
    all_counts[[site]]<-vals
    plotkeys<-union(plotkeys,aligned)
  }
}
private<-unlist(all_counts,use.names=TRUE)
if(length(private)!=length(plotkeys)||anyDuplicated(names(private)))
  stop("SCIENTIFIC_STOP_TRIPLE_SOURCE_WOODY_PLOTYEAR_KEYS_NOT_UNIQUE")
qualify<-private>=3
site<-sub("\\|[^|]+\\|[0-9]{4}$","",names(private))
site_good<-unique(site[qualify])
domain_good<-unique(official$domain_id[match(site_good,official$site_id)])
yearkey<-sub("\\|[^|]+$","",names(private))
# Same-year site-conditional replication: a fixed site-year with >=2 valid
# forest plots, useful for within-site structural comparisons.
site_year_good<-sub("\\|[^|]+\\|([0-9]{4})$","|\\1",names(private)[qualify])
per_sy<-table(site_year_good)
supports<-if(length(per_sy))sum(per_sy>=2) else 0L
site_with_contrast<-unique(sub("\\|[0-9]{4}$","",names(per_sy)[per_sy>=2]))
rule<-length(site_good)>=6&&length(domain_good)>=4&&sum(qualify)>=40
result<-list(
  schema="structural.NEON_vst2026_forestpatch_woody_height_source_quality.v1",
  fixed_published_public_VST_RELEASE2026_commit="3391e702e7be80a3f049c905782661f043be8db8",
  previous_75forestpatch_74woodyrecord_plotyear_prebiology_source_cohort_UNMODIFIED=TRUE,
  prior_VST_original_plotyear_matched_record_supported=length(target),
  source_VST_height_status_field_exists=TRUE,
  original_forest_plotyear_with_any_source_valid_tree_height_plant=length(private),
  original_forest_plotyear_with_3plus_distinct_source_live_trees_DBH10_and_usable_height=sum(qualify),
  original_forests_with_3plus_tree_height_field_support=length(site_good),
  original_NEON_domains_with_3plus_tree_height_field_support=length(domain_good),
  source_same_siteyear_with_two_or_more_distinct_supported_height_plots=supports,
  source_sites_with_any_sameyear_2plot_height_comparison=length(site_with_contrast),
  original_tree_measurement_rows_with_valid_opportunity_context_not_BIOLOGY=source_tree_rows,
  original_DISTINCT_live_tree_plant_height_opportunity_source_records=source_height_plants,
  source_original_height_eligible_individuals_per_qualifying_plotyear_median=if(any(qualify))median(private[qualify]) else NULL,
  metadata_only_next_biology_admission_min6sites_min4domains_min40plotyears_PASS=rule,
  next_biological_stage_status=if(rule) "HEIGHT_METADATA_ELIGIBLE_BIOLOGICAL_RESPONSE_STILL_SEALED" else "SCIENTIFIC_STOP_NOT_ENOUGH_VALID_SAMEYEAR_VST_HEIGHT_FOREST_PLOTS",
  source_sampled_absence_not_assigned_zero_canopy_height=TRUE,
  original_VST_plot_event_opportunity_and_plant_identity_unique=TRUE,
  no_original_tree_height_values_or_species_exported=TRUE,
  no_original_beetle_plant_taxon_abundance_or_composition_values_read=TRUE,
  no_raw_site_plot_year_or_original_woody_tree_identifiers_exported=TRUE,
  microclimate_not_measurement_joined=TRUE,
  canopy_structure_causal_hypothesis_NOT_TESTED=TRUE,
  previous_positive_PREDICTS_and_nonsignificant_NEON_synchrony_left_frozen=TRUE,
  eBird_used=FALSE
)
dir.create(args[4],recursive=TRUE,showWarnings=FALSE)
path<-file.path(args[4],"neon_vst2026_forest_patch_height_source_availability.json")
writeLines(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE,null="null"),path)
cat(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
