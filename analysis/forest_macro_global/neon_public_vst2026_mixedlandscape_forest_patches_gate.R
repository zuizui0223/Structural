#!/usr/bin/env Rscript
# NEON public derived three-source forest-patch study eligibility:
# site context may contain nonforest but ORIGINAL plot-level NLCD labels must
# independently agree as forest in beetles, plants and VST.
#
# Distinct observational population from the 8 strict forest-DOMINANT sites;
# no biological taxon/abundance or actual tree height values read.
# Pinned public VST2014-24 commit, official NEON site metadata 20260805,
# neonDivData 0.3.1, 2019-2023 beetle/plant original plot/year.
suppressPackageStartupMessages(library(neonDivData))
suppressPackageStartupMessages(library(jsonlite))

REPO="tgilbert14/NEON-Vegetation-Structure-Explorer"
VST_COMMIT="3391e702e7be80a3f049c905782661f043be8db8"
YEAR_WINDOW=2019:2023
forest_plot <- function(z){
  a<-tolower(gsub("[[:space:]_/-]+","",as.character(z)))
  a[is.na(a)]<-""
  a%in%c("evergreenforest","deciduousforest","mixedforest")
}
calendar_year<-function(z){
  x<-suppressWarnings(as.integer(substr(as.character(z),1,4)))
  x[!(x%in%YEAR_WINDOW)]<-NA_integer_
  x
}
valid_id<-function(z) !is.na(z)&nzchar(trimws(as.character(z)))
official_forest<-function(z){
  vapply(strsplit(as.character(z),"|",fixed=TRUE),function(y){
     y<-trimws(y);y<-y[nzchar(y)]
     length(y)>0&&all(y%in%c("Evergreen Forest","Deciduous Forest","Mixed Forest"))
  },logical(1))
}
key_three <- function(site,plot,year) paste(site,plot,year,sep="|")
candidate_patch_cohort<-function(beetle,plant,official){
  bb<-c("siteID","plotID","observation_datetime","nlcdClass","trappingDays",
        "trapConditionFlag","unique_sample_id","trapID")
  pp<-c("siteID","plotID","observation_datetime","nlcdClass","sample_area_m2",
        "unique_sample_id")
  if(!all(bb%in%names(beetle))||!all(pp%in%names(plant))||
     !all(c("site_id","domain_id","dominant_nlcd_classes")%in%names(official))||
     nrow(official)!=81)
    stop("STOP_NEON_SOURCE_ORIGINAL_SITE_OR_SAMPLE_SCHEMA_CHANGED")
  b<-beetle[,bb,drop=FALSE];p<-plant[,pp,drop=FALSE]
  b$year<-calendar_year(b$observation_datetime)
  p$year<-calendar_year(p$observation_datetime)
  beff<-suppressWarnings(as.numeric(as.character(b$trappingDays)))
  area<-suppressWarnings(as.numeric(as.character(p$sample_area_m2)))
  flags<-as.character(b$trapConditionFlag)
  b<-b[!is.na(b$year)&valid_id(b$plotID)&valid_id(b$unique_sample_id)&
       valid_id(b$trapID)&forest_plot(b$nlcdClass)&
       is.finite(beff)&beff>0&(is.na(flags)|!nzchar(trimws(flags))),,drop=FALSE]
  p<-p[!is.na(p$year)&valid_id(p$plotID)&valid_id(p$unique_sample_id)&
       forest_plot(p$nlcdClass)&is.finite(area)&abs(area-1)<1e-9,,drop=FALSE]
  originals<-as.character(official$site_id)
  if(anyDuplicated(originals))stop("STOP_OFFICIAL_NEON_SOURCE_SITE_ID_DUPLICATED")
  kb<-unique(key_three(b$siteID,b$plotID,b$year))
  kp<-unique(key_three(p$siteID,p$plotID,p$year))
  joined<-intersect(kb,kp)
  site<-sub("\\|[^|]+\\|[0-9]{4}$","",joined)
  if(any(!(site %in% originals)))stop("STOP_ORIGINAL_NEON_PLOT_SITE_NOT_IN_OFFICIAL_TABLE")
  list(
    source_original_forest_patch_plot_years=joined,
    source_original_qualifying_site_codes=sort(unique(site)),
    source_original_b_qualifying_plot_years=length(kb),
    source_original_p_qualifying_plot_years=length(kp),
    official_all_NLCD_forest_site_list=as.character(official$site_id[
      official_forest(official$dominant_nlcd_classes)])
  )
}
vst_patch_metadata<-function(path) {
  d<-readRDS(path)
  if(!is.list(d)||!all(c("trees","plots","opportunity_source","meta","contract")%in%names(d)))
     stop("STOP_PUBLIC_VST2026_SOURCE_RDS_CONTRACT_CHANGED")
  if(!identical(as.character(d$contract$id),"NEON-VST-DP1.10098.001-v2"))
     stop("STOP_PUBLIC_VST2026_SOURCE_CONTRACT_ID_DRIFT")
  q<-d$plots
  required<-c("plotID","eventID","tree_support","area_trees","nlcdClass")
  if(!is.data.frame(q)||!all(required%in%names(q)))
     stop("STOP_VST_CANONICAL_PLOT_NLCD_OPPORTUNITY_FIELDS_MISSING")
  yy<-if("year"%in%names(q))suppressWarnings(as.integer(as.character(q$year))) else
    if("date"%in%names(q))calendar_year(q$date) else
    stop("STOP_VST_ORIGINAL_PLOT_EVENT_YEAR_NOT_DECLARED")
  a<-suppressWarnings(as.numeric(as.character(q$area_trees)))
  good<-forest_plot(q$nlcdClass)&valid_id(q$plotID)&
       is.finite(a)&a>0&
       q$tree_support%in%c("sampled_with_records","sampled_absence")&
       !is.na(yy)&yy%in%YEAR_WINDOW
  measured<-good&q$tree_support=="sampled_with_records"
  if(!is.data.frame(d$trees)||!all(c("plotID","height")%in%names(d$trees)))
     stop("STOP_PUBLIC_VST2026_ORIGINAL_TREE_HEIGHT_HEADER_NOT_DECLARED")
  list(
    original_VST_forest_plotyear_qa_valid=paste(q$plotID[good],yy[good],sep="|"),
    original_VST_forest_plotyear_with_tree_records=paste(q$plotID[measured],yy[measured],sep="|"),
    origin_plots_with_supported_tree_sample_context=length(unique(q$plotID[good])),
    supported_sample_opportunities=sum(good),
    source_VST_events_held_excluded_from_positive_tree_area=sum(!good),
    original_tree_height_FIELD_DECLARED_NOT_READ=TRUE
  )
}
test_source<-function(){
  stopifnot(identical(forest_plot(c("mixedForest","evergreenForest",
               "Shrub/Scrub","deciduous forest")),c(TRUE,TRUE,FALSE,TRUE)))
  m<-data.frame(site_id=paste0("S",sprintf("%03d",1:81)),
       domain_id=rep("D1",81),
       dominant_nlcd_classes=rep("Grassland/Herbaceous",81))
  b<-data.frame(siteID=c("S001","S001"),plotID=c("S001_001","S001_002"),
      observation_datetime=rep("2021-08-01",2),
      nlcdClass=c("mixedForest","grasslandHerbaceous"),
      trappingDays=c(14,14),trapConditionFlag=c(NA,NA),
      unique_sample_id=c("b1","b2"),trapID=c("t1","t2"))
  p<-data.frame(siteID=c("S001","S001"),plotID=c("S001_001","S001_002"),
      observation_datetime=rep("2021-08-02",2),
      nlcdClass=c("mixedForest","grasslandHerbaceous"),
      sample_area_m2=c(1,1),unique_sample_id=c("p1","p2"))
  c<-candidate_patch_cohort(b,p,m)
  stopifnot(length(c$source_original_forest_patch_plot_years)==1,
            length(c$source_original_qualifying_site_codes)==1,
            length(c$official_all_NLCD_forest_site_list)==0)
  q<-list(
    plots=data.frame(plotID=c("S001_001","S001_001","S001_002"),
       eventID=c("event1","event2","event3"),year=c(2021,2022,2021),
       nlcdClass=c("mixedForest","mixedForest","grasslandHerbaceous"),
       tree_support=c("sampled_with_records","held_sampling_impractical","sampled_with_records"),
       area_trees=c(400,400,400)),
    trees=data.frame(plotID="S001_001",height=15),
    opportunity_source=data.frame(plotID="S001_001",eventID="event1"),
    meta=list(release="RELEASE-2026"),
    contract=list(id="NEON-VST-DP1.10098.001-v2"))
  tmp<-tempfile(fileext=".rds");saveRDS(q,tmp);v<-vst_patch_metadata(tmp);unlink(tmp)
  stopifnot(length(v$original_VST_forest_plotyear_qa_valid)==1,
            length(v$original_VST_forest_plotyear_with_tree_records)==1,
            v$source_VST_events_held_excluded_from_positive_tree_area==2)
  cat("PUBLISHED NEON VST FOREST PATCH: source-only mixed-landscape synthetic PASS\n")
}
if(identical(Sys.getenv("VST_FOREST_PATCH_SYNTHETIC_ONLY"),"1")){
  test_source();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(identical(Sys.getenv("VST_FOREST_PATCH_SITE_LIST_ONLY"),"1")){
  if(length(args)!=2)stop("SOURCE SITE LIST requires official site metadata CSV and temporary path")
  site<-read.csv(args[1],stringsAsFactors=FALSE,check.names=FALSE)
  list<-candidate_patch_cohort(neonDivData::data_beetle,neonDivData::data_plant,site)
  dir.create(dirname(args[2]),recursive=TRUE,showWarnings=FALSE)
  writeLines(list$source_original_qualifying_site_codes,args[2])
  cat("Source-only forest PATCH candidate site count:",length(list$source_original_qualifying_site_codes),"\n")
  quit(status=0)
}
if(length(args)!=3)stop("usage: Rscript neon_public_vst2026_mixedlandscape_forest_patches_gate.R OFFICIAL_SITE_CSV PRIVATE_VST_DIR OUT")
test_source()
site<-read.csv(args[1],stringsAsFactors=FALSE,check.names=FALSE)
cohort<-candidate_patch_cohort(neonDivData::data_beetle,neonDivData::data_plant,site)
samplekeys<-cohort$source_original_forest_patch_plot_years
out<-args[3];dir.create(out,recursive=TRUE,showWarnings=FALSE)
allsite<-cohort$source_original_qualifying_site_codes
loaded<-0L;matchkeys<-character();recordkeys<-character();summaries<-list();lacking<-0L
for(si in allsite){
  file<-file.path(args[2],paste0(si,".rds"))
  if(!file.exists(file)){lacking<-lacking+1L;next}
  original<-vst_patch_metadata(file);loaded<-loaded+1L
  keys<-unique(paste(si,original$original_VST_forest_plotyear_qa_valid,sep="|"))
  measured<-unique(paste(si,original$original_VST_forest_plotyear_with_tree_records,sep="|"))
  both<-intersect(keys,samplekeys)
  withtree<-intersect(measured,samplekeys)
  matchkeys<-union(matchkeys,both)
  recordkeys<-union(recordkeys,withtree)
  summaries[[si]]<-list(
     anonymous_source_woody_qa_supported_original_plotyear_count=length(keys),
     anonymous_original_triple_forest_patch_plot_years_QA_supported=length(both),
     anonymous_original_triple_forest_patch_plot_years_WITH_WOODY_RECORDS=length(withtree),
     original_tree_height_FIELD_declared=original$original_tree_height_FIELD_DECLARED_NOT_READ,
     source_held_tree_opportunities_not_assumed_zero=original$source_VST_events_held_excluded_from_positive_tree_area
  )
}
# Optional intermediate original keys for a SEPARATE, same-run source-only
# tree-height availability check. Stored in runner-private source path and
# deliberately never included in aggregate/uploaded output directories.
if(identical(Sys.getenv("VST_FOREST_PATCH_WRITE_PRIVATE_JOIN_KEYS"),"1")){
  privatefile<-file.path(args[2],"..","private_verified_original_plotyear_keys.txt")
  writeLines(sort(unique(recordkeys)),privatefile)
  cat("Runner-private supported forest plot-year keys:",length(recordkeys),"\\n")
}
supportsite<-unique(sub("\\|[^|]+\\|[0-9]{4}$","",matchkeys))
source_domain<-unique(site$domain_id[match(supportsite,site$site_id)])
outcome_status<-if(length(supportsite)>=6&&length(source_domain)>=4&&length(matchkeys)>=40) {
  "PLOTLEVEL_FOREST_PATCH_METADATA_GATE_PASSED_BIOLOGICAL_RESPONSE_UNOPENED"
} else {
  "SCIENTIFIC_STOP_FOREST_PATCH_STRUCTURE_PLOTYEAR_SUPPORT_INSUFFICIENT"
}
report<-list(
 schema="structural.neon_vst2026_mixed_landscape_forest_patch_source_gate.v1",
 source_vst_repo=REPO,
 public_source_vst_fixed_commit=VST_COMMIT,
 published_woody_product="NEON DP1.10098.001 RELEASE-2026",
 published_organismal_derivative="neonDivData 0.3.1",
 forest_patches_within_sites_NOT_equivalent_entire_site_strict_forest_only=TRUE,
 forest_patches_both_organismal_original_source_sites=length(allsite),
 original_neon_organismal_forest_patch_coobserved_siteplotyears=length(samplekeys),
 original_VST_forest_patch_bundle_site_count=loaded,
 original_VST_bundle_sites_missing_from_public_42site_source=lacking,
 original_triple_source_supported_siteplotyears=length(matchkeys),
 original_triple_source_with_woody_records_siteplotyears=length(recordkeys),
 original_triple_source_distinct_NEON_site_count=length(supportsite),
 original_triple_source_NEON_ecoclimatic_domains=length(source_domain),
 baseline_official_strict_forest_only_sites_in_mixedlandscape_source=sum(
    supportsite%in%cohort$official_all_NLCD_forest_site_list),
 prior_eight_strict_forest_source_stop_unmodified=TRUE,
 frozen_source_support_min6sites_min4domains_min40plotyears_passed=outcome_status==
  "PLOTLEVEL_FOREST_PATCH_METADATA_GATE_PASSED_BIOLOGICAL_RESPONSE_UNOPENED",
 gate_status=outcome_status,
 original_site_anonymized_support_counts=unname(summaries),
 original_woody_height_values_never_read=TRUE,
 beetle_plant_taxon_species_abundance_values_never_read=TRUE,
 all_original_site_plot_tree_species_and_locations_not_reexported=TRUE,
 source_woody_held_opportunities_not_reclassified_to_zero=TRUE,
 site_level_forest_dominance_not_imposed_on_distinct_patch_population=TRUE,
 sameyear_plot_support_is_not_same_date_microclimate=TRUE,
 previous_PREDICTS_and_NEON_biological_scores_sealed=TRUE,
 eBird_used=FALSE
)
path<-file.path(out,"neon_vst2026_mixedlandscape_forest_patch_support.json")
writeLines(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),path)
cat(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
