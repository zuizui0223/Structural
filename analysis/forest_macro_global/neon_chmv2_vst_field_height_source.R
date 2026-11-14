#!/usr/bin/env Rscript
# VST2026 live DBH>=10 cm author-quality positive height plot-years
# as independently published field source for Meta/WRI CHMv2 proxy check.
# All VST field height numbers/site identities remain runner-private.
# Zero NEON beetle/plant biological data values are read.
suppressPackageStartupMessages(library(jsonlite))
FOREST<-c("deciduousforest","evergreenforest","mixedforest")
norm<-function(z){
  q<-tolower(gsub("[[:space:]_/-]+","",as.character(z)))
  q[is.na(q)]<-"";q
}
forest<-function(x)norm(x)%in%FOREST
hasid<-function(x)!is.na(x)&nzchar(trimws(as.character(x)))
yr<-function(x){
  v<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  v[!(v%in%2019:2023)]<-NA_integer_;v
}
original_field<-function(bundle,site) {
  if(!is.list(bundle)||!all(c("plots","trees","contract")%in%names(bundle))||
     !identical(as.character(bundle$contract$id),"NEON-VST-DP1.10098.001-v2"))
    stop("SCIENTIFIC_STOP_VST_FIELD_AUTHOR_CONTRACT_CHANGED")
  q<-bundle$plots;t<-bundle$trees
  needed_q<-c("plotID","eventID","tree_support","area_trees","nlcdClass")
  needed_t<-c("plotID","eventID","individualID","height","stemDiameter","growthForm")
  if(!all(needed_q%in%names(q))||!all(needed_t%in%names(t)))
    stop("SCIENTIFIC_STOP_SOURCE_VST_AUTHOR_FIELD_SCHEMA_CHANGED")
  y<-if("year"%in%names(q))suppressWarnings(as.integer(as.character(q$year))) else
     if("date"%in%names(q))yr(q$date) else
       stop("SCIENTIFIC_STOP_ORIGINAL_VST_EVENT_YEAR_UNAVAILABLE")
  qa<-q$tree_support=="sampled_with_records"&forest(q$nlcdClass)&
      is.finite(suppressWarnings(as.numeric(as.character(q$area_trees))))&
      suppressWarnings(as.numeric(as.character(q$area_trees)))>0&
      hasid(q$plotID)&hasid(q$eventID)&!is.na(y)&y%in%2019:2023
  q<-q[which(qa),,drop=FALSE]
  y<-y[which(qa)]
  if(!nrow(q))return(data.frame())
  k<-paste(q$plotID,q$eventID,sep="|")
  if(anyDuplicated(k)){
    grouped<-split(y,k)
    if(any(vapply(grouped,function(z)length(unique(z))>1,logical(1))))
      stop("SCIENTIFIC_STOP_VST_EVENT_LOCATOR_YEAR_CONFLICT")
  }
  unique_event<-!duplicated(k)
  event_year<-setNames(y[unique_event],k[unique_event])
  event_area<-setNames(as.numeric(as.character(q$area_trees))[unique_event],k[unique_event])
  k_tree<-paste(t$plotID,t$eventID,sep="|")
  original_year<-unname(event_year[k_tree])
  original_area<-unname(event_area[k_tree])
  h<-suppressWarnings(as.numeric(as.character(t$height)))
  d<-suppressWarnings(as.numeric(as.character(t$stemDiameter)))
  life<-if("live"%in%names(t)){
    as.logical(t$live)%in%TRUE
  } else if("plantStatus"%in%names(t)) {
    tolower(trimws(as.character(t$plantStatus)))=="live"
  } else stop("SCIENTIFIC_STOP_VST_LIVE_STATUS_UNAVAILABLE")
  qc<-if("size_height_ok"%in%names(t))
    as.logical(t$size_height_ok)%in%TRUE else rep(TRUE,nrow(t))
  gf<-tolower(trimws(as.character(t$growthForm)))
  good<-is.finite(original_year)&original_year%in%2019:2023&
        is.finite(original_area)&original_area>0&
        is.finite(h)&h>0&is.finite(d)&d>=10&
        life&qc&gf%in%c("single bole tree","multi-bole tree")&
        hasid(t$individualID)&hasid(t$plotID)
  if(!any(good))return(data.frame())
  # Author physical individual is unique per original site×plot×year;
  # multiple stems/events are one plant and the maximum valid stem height
  # is fixed regardless of the observed CHMv2 value.
  rows<-data.frame(
    siteID=site,
    plotID=as.character(t$plotID[good]),
    year=as.integer(original_year[good]),
    individualID=as.character(t$individualID[good]),
    height_m=h[good],
    area_m2=original_area[good],stringsAsFactors=FALSE)
  phys<-paste(rows$siteID,rows$plotID,rows$year,rows$individualID,sep="|")
  split_phys<-split(seq_len(nrow(rows)),phys)
  values<-lapply(split_phys,function(i) {
    z<-rows[i[1],,drop=FALSE]
    z$height_m<-max(rows$height_m[i])
    z
  })
  oneplant<-do.call(rbind,unname(values))
  original_key<-paste(oneplant$siteID,oneplant$plotID,oneplant$year,sep="|")
  byplot<-split(seq_len(nrow(oneplant)),original_key)
  output<-list()
  for(k in names(byplot)) {
    sub<-oneplant[byplot[[k]],,drop=FALSE]
    if(nrow(sub)<3)next
    record<-sub[1,c("siteID","plotID","year"),drop=FALSE]
    record$VST_field_p90_live_DBH10_height_m<-as.numeric(quantile(
       sub$height_m,.90,names=FALSE,type=7))
    record$source_distinct_live_tree_individuals<-nrow(sub)
    record$source_original_tree_sample_area_m2<-median(sub$area_m2)
    output[[k]]<-record
  }
  if(!length(output))return(data.frame())
  do.call(rbind,unname(output))
}
synthetic<-function() {
  sample<-list(
    plots=data.frame(plotID=c("NEON_P1","NEON_P2","NEON_P1"),
       eventID=c("e1","e2","e3"),year=c(2020,2020,2021),
       nlcdClass="mixedForest",area_trees=400,
       tree_support=c("sampled_with_records","held_sampling_impractical","sampled_with_records")),
    trees=data.frame(plotID=c(rep("NEON_P1",5),"NEON_P2"),
       eventID=c(rep("e1",4),"e3","e2"),
       individualID=c("i1","i1","i2","i3","i4","i5"),
       height=c(12,13,15,21,19,50),
       stemDiameter=15,growthForm="single bole tree",live=TRUE,
       size_height_ok=TRUE),
    contract=list(id="NEON-VST-DP1.10098.001-v2"))
  q<-original_field(sample,"S001")
  stopifnot(nrow(q)==1,q$source_distinct_live_tree_individuals==3,
            q$VST_field_p90_live_DBH10_height_m>15,
            q$VST_field_p90_live_DBH10_height_m<21,
            q$source_original_tree_sample_area_m2==400,
            !any(grepl("i1|i2|NEON_P",names(q))))
  cat("VST FIELD SOURCE synthetic original individual de-dup, live QA, plot/year, height p90 PASS\n")
}
if(identical(Sys.getenv("NEON_CHM_FIELD_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=4)stop("usage: Rscript neon_chmv2_vst_field_height_source.R OFFICIAL_CSV PRIVATE_NEON_952_PLOTYEARS_CSV PUBLIC_VST_RDS_FOLDER PRIVATE_OUTPUT_ROOT")
synthetic()
site<-read.csv(args[1],check.names=FALSE,stringsAsFactors=FALSE)
loc<-read.csv(args[2],stringsAsFactors=FALSE)
if(nrow(site)!=81||!all(c("site_id","domain_id")%in%names(site))||
   nrow(loc)!=952||!all(c("siteID","plotID","source_year")%in%names(loc)))
  stop("STOP_ORIGINAL_NEON_952_SOURCE_IDENTITY_DRIFT")
candidate<-unique(paste(loc$siteID,loc$plotID,loc$source_year,sep="|"))
if(length(candidate)!=952)stop("STOP_DUPLICATED_PRIVATE_ORIGINAL_PLOTYEAR")
sites<-sort(unique(as.character(loc$siteID)))
if(length(sites)!=35)stop("STOP_FROZEN_NEON_FOREST_PATCH_35_SITE_FRAME")
results<-list();sites_missing<-character()
for(si in sites) {
  f<-file.path(args[3],paste0(si,".rds"))
  if(!file.exists(f)){sites_missing<-c(sites_missing,si);next}
  z<-original_field(readRDS(f),si)
  if(!nrow(z))next
  k<-paste(z$siteID,z$plotID,z$year,sep="|")
  z<-z[k%in%candidate,,drop=FALSE]
  if(nrow(z))results[[si]]<-z
}
if(length(sites_missing))stop("STOP_ORIGINAL_35_SITE_VST_PUBLIC_SOURCE_BUNDLE_INCOMPLETE")
if(!length(results))stop("STOP_NO_VALID_SOURCE_FIELD_HEIGHT")
d<-do.call(rbind,unname(results))
if(nrow(d)!=73||anyDuplicated(paste(d$siteID,d$plotID,d$year,sep="|")))
  stop("STOP_PREVIOUS_AUTHOR_VST_73_HEIGHT_PLOTYEAR_COHORT_DRIFT")
site_count<-length(unique(d$siteID))
domain_count<-length(unique(site$domain_id[match(unique(d$siteID),site$site_id)]))
if(site_count!=22||domain_count!=13)
  stop("STOP_PREVIOUS_22SITE_13DOMAIN_AUTHOR_VST_SAMPLE_DRIFT")
count_by_year<-table(factor(d$year,levels=2019:2023))
plot_key<-paste(d$siteID,d$plotID,sep="|")
repeat_plot<-length(unique(plot_key))
# Source selected year closest to 2020; ties older first.
choice<-order(abs(d$year-2020),d$year)
d<-d[choice,,drop=FALSE]
unique_plot<-d[!duplicated(paste(d$siteID,d$plotID,sep="|")),,drop=FALSE]
if(nrow(unique_plot)!=repeat_plot)stop("STOP_VST_ORIGINAL_PLOT_YEAR_PRIORITY")
dest<-file.path(args[4],"private_vst_field_height_plotyears.csv")
dir.create(args[4],recursive=TRUE,showWarnings=FALSE)
write.csv(d,dest,row.names=FALSE)
pub<-list(
 schema="structural.NEON_original_VST_RE2026_73_field_height_plotyears_source.v1",
 published_VST_release_commit="3391e702e7be80a3f049c905782661f043be8db8",
 original_published_forest_plots_with_3plus_independent_live_trees_field_height=nrow(d),
 original_NEON_field_sites_revalidated=site_count,
 original_NEON_ecoclimatic_domains_revalidated=domain_count,
 original_VST_distinct_spatial_plots_before_any_CHMv2_values=repeat_plot,
 source_VST_field_year_support_counts=as.list(count_by_year),
 original_multiple_year_VST_plot_surveys_NOT_independent=TRUE,
 original_plot_year_for_unique_siteplot_selected_closest_to_2020_without_looking_at_CHMv2=TRUE,
 original_VST_living_DBH10_unique_individual_heights_used_NOT_BIOLOGICAL_RESPONSE=TRUE,
 previous_2019_23_SCIENTIFIC_STOP_original_10siteyear_not_changed=TRUE,
 original_NEON_plant_beetle_species_taxon_abundance_values_NOT_READ=TRUE,
 original_raw_VST_height_individual_site_plot_identifiers_NOT_PUBLISHED=TRUE,
 eBird_used=FALSE)
writeLines(jsonlite::toJSON(pub,auto_unbox=TRUE,pretty=TRUE,null="null"),
  file.path(args[4],"source_public_field_VST_support.json"))
cat(jsonlite::toJSON(pub,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
