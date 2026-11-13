#!/usr/bin/env Rscript
# 2026-11-13: ORIGINAL DATA SOURCE METADATA ONLY.
# Frozen 73 forest patch plot×years with 3+ unique VST live DBH>=10cm
# height-support plants. Match beetle unflagged traps and plant 1m2
# survey effort to the SAME plot/year and forest VST opportunity date.
# No taxon IDs, abundance, alpha/beta values, woody height magnitudes,
# source plot/site/date/measurement rows exported.
suppressPackageStartupMessages(library(neonDivData))
suppressPackageStartupMessages(library(jsonlite))

valid_id<-function(x)!is.na(x)&nzchar(trimws(as.character(x)))
isforest<-function(x){
  z<-tolower(gsub("[[:space:]_/-]+","",trimws(as.character(x))))
  z[is.na(z)]<-""
  z%in%c("deciduousforest","evergreenforest","mixedforest")
}
extractyear<-function(x){
  z<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  z[!(z%in%2019:2023)]<-NA_integer_
  z
}
asday<-function(x){
  suppressWarnings(as.Date(substr(as.character(x),1,10)))
}
within_ratio<-function(x,y,lower=.5,upper=2){
  is.finite(x)&&is.finite(y)&&x>0&&y>0&&x/y>=lower&&x/y<=upper
}
compare_forest_plot_pair<-function(a,b){
  # Both plots must be same original site/year, source sampling effort ratio,
  # and a common field season. Number of plot pairs is not independent n.
  within_ratio(a$beetle_total_trap_days,b$beetle_total_trap_days)&&
    within_ratio(a$plant_recorded_1m2_subplots,b$plant_recorded_1m2_subplots)&&
    abs(as.numeric(a$plant_first_date-b$plant_first_date))<=30
}
date_effort_in_plot<-function(beetle,plant,vst_dates) {
  # Fail closed if the caller accidentally mixes plot/year or site.
  if(!nrow(beetle)||!nrow(plant))return(list(status="NO_SOURCE_BOTH_TAXA"))
  a<-unique(paste(beetle$siteID,beetle$plotID,
     extractyear(beetle$observation_datetime),sep="|"))
  b<-unique(paste(plant$siteID,plant$plotID,
     extractyear(plant$observation_datetime),sep="|"))
  if(length(a)!=1||length(b)!=1||a!=b||grepl("\\|NA$",a))
    return(list(status="STOP_INPUT_NOT_SAME_ORIGINAL_SITE_PLOT_YEAR"))
  p<-plant[isforest(plant$nlcdClass),,drop=FALSE]
  pdate<-asday(p$observation_datetime)
  area<-suppressWarnings(as.numeric(as.character(p$sample_area_m2)))
  goodp<-is.finite(area)&abs(area-1)<1e-9&
    valid_id(p$unique_sample_id)&valid_id(p$subplotID)&!is.na(pdate)
  if(!any(goodp))return(list(status="NO_VALID_PLANT_ONE_M2_SOURCE"))
  first<-min(pdate[goodp])
  p<-p[goodp & abs(as.numeric(pdate-first))<=7,,drop=FALSE]
  ps<-unique(as.character(p$subplotID))
  b<-beetle[isforest(beetle$nlcdClass),,drop=FALSE]
  bdate<-asday(b$observation_datetime)
  days<-suppressWarnings(as.numeric(as.character(b$trappingDays)))
  flags<-as.character(b$trapConditionFlag)
  goodb<-is.finite(days)&days>0&valid_id(b$unique_sample_id)&
    valid_id(b$trapID)&(is.na(flags)|!nzchar(trimws(flags)))&
    !is.na(bdate)&abs(as.numeric(bdate-first))<=30
  b<-b[goodb,,drop=FALSE]
  if(!nrow(b))return(list(status="NO_UNFLAGGED_BEETLE_SAME_PLOT_WITHIN_30D"))
  # One original trap sample has one effort. Reject contradictions rather
  # than taking favorable source rows (taxon records repeat sample metadata).
  per_sample<-split(as.numeric(as.character(b$trappingDays)),
                    as.character(b$unique_sample_id))
  if(any(vapply(per_sample,function(v)length(unique(v))!=1,logical(1))))
    return(list(status="STOP_DUPLICATE_ORIGINAL_SAMPLE_EFFORT_CONFLICT"))
  nbeetle<-length(per_sample)
  nplant<-length(ps)
  if(nbeetle<4||nplant<4)
    return(list(status="INSUFFICIENT_FOUR_BEETLE_FOUR_RECORDED_PLANT_SUBPLOTS",
      unflagged_beetle_samples=nbeetle,
      recorded_one_m2_plant_subplots=nplant))
  validvst<-vst_dates[!is.na(vst_dates)]
  if(!length(validvst))return(list(status="VST_ORIGINAL_EVENT_DATE_MISSING",
     unflagged_beetle_samples=nbeetle,recorded_one_m2_plant_subplots=nplant))
  closest<-min(abs(as.numeric(validvst-first)))
  if(!is.finite(closest)||closest>90)
    return(list(status="VST_EVENT_OUTSIDE_PRESPEC_90DAY_PLANT_SEASON",
      unflagged_beetle_samples=nbeetle,
      recorded_one_m2_plant_subplots=nplant))
  list(
    status="PLOT_SOURCE_SEASON_EFFORT_SUPPORTED",
    unflagged_beetle_samples=nbeetle,
    recorded_one_m2_plant_subplots=nplant,
    beetle_total_trap_days=sum(vapply(per_sample,function(v)v[1],numeric(1))),
    plant_first_date=first,
    vst_to_plant_min_days=closest)
}
vst_event_date_by_source_plotyear<-function(source_bundle,site,selected){
  x<-source_bundle$plots
  if(!is.data.frame(x)||!all(c("plotID","eventID","area_trees",
                                  "tree_support","nlcdClass")%in%names(x)))
    stop("SCIENTIFIC_STOP_VST_2026_AUTHOR_PLOT_OPPORTUNITY_SCHEMA")
  if(!identical(as.character(source_bundle$contract$id),"NEON-VST-DP1.10098.001-v2"))
    stop("SCIENTIFIC_STOP_SOURCE_VST2026_CONTRACT_DRIFT")
  yy<-if("year"%in%names(x))suppressWarnings(as.integer(as.character(x$year))) else
     if("date"%in%names(x))extractyear(x$date) else
     stop("SCIENTIFIC_STOP_VST_ORIGINAL_EVENT_YEAR_MISSING")
  if(!("date"%in%names(x))) {
    # It is NOT valid to treat having the same calendar year as close season.
    return(list())
  }
  area<-suppressWarnings(as.numeric(as.character(x$area_trees)))
  ok<-isforest(x$nlcdClass)&is.finite(area)&area>0&
    x$tree_support=="sampled_with_records"&valid_id(x$plotID)&
    valid_id(x$eventID)&!is.na(yy)
  selected_keys<-paste(site,x$plotID,yy,sep="|")
  ok<-ok&selected_keys%in%selected
  split(asday(x$date[ok]),selected_keys[ok])
}
run_gate<-function(official,bsource,psource,rds_dir,private_keys){
  if(as.character(utils::packageVersion("neonDivData"))!="0.3.1")
    stop("SCIENTIFIC_STOP_NEON_DERIVATIVE_VERSION_DRIFT")
  if(nrow(official)!=81||!all(c("site_id","domain_id","dominant_nlcd_classes")%in%names(official)))
    stop("SCIENTIFIC_STOP_OFFICIAL_81_SITE_SOURCE_SCHEMA")
  if(length(private_keys)!=73||anyDuplicated(private_keys))
    stop("SCIENTIFIC_STOP_PREVIOUS_SOURCE_73_ORIGINAL_HEIGHT_PLOTYEARS_CHANGED")
  required_b<-c("siteID","plotID","observation_datetime","nlcdClass",
    "trappingDays","trapConditionFlag","unique_sample_id","trapID")
  required_p<-c("siteID","plotID","observation_datetime","nlcdClass",
    "sample_area_m2","unique_sample_id","subplotID")
  if(!all(required_b%in%names(bsource))||!all(required_p%in%names(psource)))
    stop("SCIENTIFIC_STOP_ORIGINAL_SOURCE_EFFORT_METADATA_SCHEMA")
  # Selecting metadata columns explicitly prevents any taxon/value access.
  b<-bsource[,required_b,drop=FALSE]
  p<-psource[,required_p,drop=FALSE]
  by<-extractyear(b$observation_datetime)
  py<-extractyear(p$observation_datetime)
  bk<-paste(b$siteID,b$plotID,by,sep="|")
  pk<-paste(p$siteID,p$plotID,py,sep="|")
  b<-b[!is.na(by)&bk%in%private_keys,,drop=FALSE]
  p<-p[!is.na(py)&pk%in%private_keys,,drop=FALSE]
  bk<-bk[!is.na(by)&bk%in%private_keys]
  pk<-pk[!is.na(py)&pk%in%private_keys]
  bi<-split(seq_len(nrow(b)),bk)
  pi<-split(seq_len(nrow(p)),pk)
  dates<-list()
  source_sites<-sort(unique(sub("\\|[^|]+\\|[0-9]{4}$","",private_keys)))
  for(site in source_sites) {
    filename<-file.path(rds_dir,paste0(site,".rds"))
    if(!file.exists(filename))stop("SCIENTIFIC_STOP_REQUIRED_AUTHOR_PUBLIC_VST_SOURCE_BUNDLE_MISSING")
    dates<-c(dates,vst_event_date_by_source_plotyear(readRDS(filename),site,private_keys))
  }
  status<-character()
  retained<-list()
  for(k in private_keys){
    bb<-if(k%in%names(bi))b[bi[[k]],,drop=FALSE]else b[FALSE,,drop=FALSE]
    pp<-if(k%in%names(pi))p[pi[[k]],,drop=FALSE]else p[FALSE,,drop=FALSE]
    dd<-if(k%in%names(dates))dates[[k]]else as.Date(character())
    val<-date_effort_in_plot(bb,pp,dd)
    status<-c(status,val$status)
    if(identical(val$status,"PLOT_SOURCE_SEASON_EFFORT_SUPPORTED"))
      retained[[k]]<-val
  }
  # Within a common source site/year retain only observational plot pairs
  # with mutually comparable trap-days, 1m2 recorded subplot counts and DOY.
  valid_keys<-names(retained)
  group<-split(valid_keys,sub("\\|[^|]+\\|([0-9]{4})$","|\\1",valid_keys))
  # Independent SOURCE-ONLY failure attribution. These are not three
  # alternative model specifications, and they never relax the joint gate.
  pair_flags<-lapply(group,function(keys) {
    if(length(keys)<2) return(matrix(FALSE,nrow=0,ncol=3,
                                    dimnames=list(NULL,c("beetle_effort",
                                                        "plant_subplot_effort",
                                                        "field_season"))))
    pairidx<-combn(keys,2)
    m<-vapply(seq_len(ncol(pairidx)),function(i){
      a<-retained[[pairidx[1,i]]];b<-retained[[pairidx[2,i]]]
      c(beetle_effort=within_ratio(a$beetle_total_trap_days,b$beetle_total_trap_days),
        plant_subplot_effort=within_ratio(a$plant_recorded_1m2_subplots,
                                         b$plant_recorded_1m2_subplots),
        field_season=abs(as.numeric(a$plant_first_date-b$plant_first_date))<=30)
    },logical(3))
    if(is.null(dim(m)))matrix(m,nrow=3,dimnames=list(c("beetle_effort",
      "plant_subplot_effort","field_season"),NULL)) else m
  })
  allflags<-do.call(cbind,pair_flags[lengths(group)>=2])
  if(is.null(allflags))allflags<-matrix(FALSE,nrow=3,ncol=0,
      dimnames=list(c("beetle_effort","plant_subplot_effort","field_season"),NULL))
  pair_pass<-vapply(pair_flags,function(m){
    if(nrow(m)==0)return(FALSE)
    if(nrow(m)==3)any(apply(m,2,all)) else any(apply(m,1,all))
  },logical(1))
  eligible_sy<-names(pair_pass)[pair_pass]
  pairdiagnostics<-list(
     original_same_siteyear_candidate_plot_pairs_total=if(ncol(allflags))ncol(allflags) else 0,
     original_candidate_pairs_with_beetle_trapdays_ratio_0p5to2=if(ncol(allflags))sum(allflags["beetle_effort",])else 0,
     original_candidate_pairs_with_positive_plant_subplot_ratio_0p5to2=if(ncol(allflags))sum(allflags["plant_subplot_effort",])else 0,
     original_candidate_pairs_with_plant_first_survey_dates_within30d=if(ncol(allflags))sum(allflags["field_season",])else 0,
     original_candidate_pairs_with_both_effort_ratios=if(ncol(allflags))sum(allflags["beetle_effort",]&allflags["plant_subplot_effort",])else 0,
     original_candidate_pairs_with_effort_and_season_all_three=if(ncol(allflags))sum(apply(allflags,2,all))else 0,
     source_siteyears_with_any_beetle_effort_matched_pair=sum(vapply(pair_flags,function(m)
        nrow(m)>0&&any(m["beetle_effort",]),logical(1))),
     source_siteyears_with_any_plant_subplot_matched_pair=sum(vapply(pair_flags,function(m)
        nrow(m)>0&&any(m["plant_subplot_effort",]),logical(1))),
     source_siteyears_with_any_plant_date_matched_pair=sum(vapply(pair_flags,function(m)
        nrow(m)>0&&any(m["field_season",]),logical(1)))
  )
  eligible_sites<-unique(sub("\\|[0-9]{4}$","",eligible_sy))
  eligible_domains<-unique(as.character(official$domain_id[
     match(eligible_sites,as.character(official$site_id))]))
  if(anyNA(eligible_domains))stop("SCIENTIFIC_STOP_MISSING_OFFICIAL_DOMAIN_FOR_SELECTED_NEON_SITE")
  # Key distinction: a site/year with 3 plots but no pair satisfying
  # comparable effort does not count as a within-site comparison.
  pass<-length(eligible_sites)>=10 &&
        length(eligible_domains)>=6 &&
        length(eligible_sy)>=12
  diagnostics<-as.list(table(factor(status,levels=c(
    "PLOT_SOURCE_SEASON_EFFORT_SUPPORTED",
    "NO_SOURCE_BOTH_TAXA","STOP_INPUT_NOT_SAME_ORIGINAL_SITE_PLOT_YEAR","NO_VALID_PLANT_ONE_M2_SOURCE",
    "NO_UNFLAGGED_BEETLE_SAME_PLOT_WITHIN_30D",
    "INSUFFICIENT_FOUR_BEETLE_FOUR_RECORDED_PLANT_SUBPLOTS",
    "VST_ORIGINAL_EVENT_DATE_MISSING",
    "VST_EVENT_OUTSIDE_PRESPEC_90DAY_PLANT_SEASON",
    "STOP_DUPLICATE_ORIGINAL_SAMPLE_EFFORT_CONFLICT"))))
  list(
    schema="structural.NEON_2026VST_0p3p1_forestpatch_strict_plot_season_effort.v1",
    pinned_VST_release_commit="3391e702e7be80a3f049c905782661f043be8db8",
    preoutcome_73_real_height_eligible_source_plotyears_UNCHANGED=length(private_keys),
    original_source_height_three_live_DBH10_plotyear_cohort_used=TRUE,
    original_source_taxon_values_never_accessed=TRUE,
    original_tree_height_magnitude_never_accessed=TRUE,
    source_original_valid_plotyears_by_non_biological_exclusion_reason=diagnostics,
    original_source_height_plotyears_with_four_unflagged_beetle_samples_four_plant_1m2_subplots_and_VST_within90d=length(retained),
    source_siteyear_groups_with_2plus_eligible_plots_BEFORE_effort_matching=sum(lengths(group)>=2),
    source_only_candidate_pair_failure_attribution_NO_GATE_CHANGED=pairdiagnostics,
    source_siteyear_groups_with_2plus_effort_comparable_plantseason_plots=length(eligible_sy),
    source_forest_sites_with_2plus_source_plantbeetle_VST_comparable_plots=length(eligible_sites),
    source_official_NEO_domain_count_with_2plus_comparable_plots=length(eligible_domains),
    source_siteyear_eligible_plot_pair_count_NONINDEPENDENT=if(ncol(allflags)) sum(apply(allflags,2,all)) else 0L,
    frozen_min_10_sites_6_domains_12_siteyears_PASS=pass,
    gate_status=if(pass)"SOURCE_SEASON_EFFORT_ELIGIBLE_NO_BIOLOGY_YET" else
       "SCIENTIFIC_STOP_ORIGINAL_SAMEPLOT_SEASON_EFFORT_REPLICATION_INSUFFICIENT",
    source_tree_woody_event_not_equal_microclimate_measurement=TRUE,
    siteyear_and_plot_pairs_NOT_independent_forests=TRUE,
    plant_1m2_positive_records_not_complete_zero_absence_census=TRUE,
    no_original_site_plot_individual_or_source_event_IDs_exported=TRUE,
    no_biodiversity_effect_or_causes_inferred=TRUE,
    original_PREDICTS_primary_and_NEON_v2_temporal_results_left_sealed=TRUE,
    eBird_used=FALSE)
}
synthetic<-function() {
  b<-data.frame(
    siteID=rep("S001",6),plotID=rep("P1",6),
    observation_datetime=rep("2020-06-15",6),nlcdClass="mixedForest",
    trappingDays=rep(14,6),trapConditionFlag=rep(NA_character_,6),
    unique_sample_id=paste0("B",1:6),trapID=paste0("T",1:6))
  p<-data.frame(siteID=rep("S001",6),plotID=rep("P1",6),
    observation_datetime=rep("2020-06-10",6),nlcdClass="mixedForest",
    sample_area_m2=rep(1,6),unique_sample_id=paste0("P",1:6),
    subplotID=paste0("Q",1:6))
  v<-date_effort_in_plot(b,p,as.Date("2020-06-20"))
  stopifnot(v$status=="PLOT_SOURCE_SEASON_EFFORT_SUPPORTED",
    v$unflagged_beetle_samples==6,
    v$recorded_one_m2_plant_subplots==6,
    v$beetle_total_trap_days==84)
  b$trapConditionFlag[1:3]<-"source flag"
  stopifnot(date_effort_in_plot(b,p,as.Date("2020-06-20"))$status==
    "INSUFFICIENT_FOUR_BEETLE_FOUR_RECORDED_PLANT_SUBPLOTS")
  stopifnot(date_effort_in_plot(b,transform(p,plotID="OTHER"),as.Date("2020-06-20"))$status==
    "STOP_INPUT_NOT_SAME_ORIGINAL_SITE_PLOT_YEAR")
  b$trapConditionFlag<-NA_character_
  stopifnot(date_effort_in_plot(b,p,as.Date("2020-12-20"))$status==
    "VST_EVENT_OUTSIDE_PRESPEC_90DAY_PLANT_SEASON")
  a<-v;bb<-v;bb$beetle_total_trap_days<-200
  stopifnot(!compare_forest_plot_pair(a,bb))
  bb<-v;bb$plant_recorded_1m2_subplots<-20
  stopifnot(!compare_forest_plot_pair(a,bb))
  bb<-v;bb$plant_first_date<-a$plant_first_date+90
  stopifnot(!compare_forest_plot_pair(a,bb))
  cat("SOURCE KNOWN TRUTH PASS: source sample effort / season / QA / between-plot ratios\n")
}
if(identical(Sys.getenv("NEON_VST_SEASON_EFFORT_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=4)stop("usage: Rscript neon_vst2026_forestpatch_species_source_season_effort_gate.R OFFICIAL_SOURCE SITE_BUNDLES 73_PRIVATE_HEIGHT_KEYS AGG_OUT")
synthetic()
official<-read.csv(args[1],stringsAsFactors=FALSE,check.names=FALSE)
target<-readLines(args[3],warn=FALSE)
report<-run_gate(official,neonDivData::data_beetle,
  neonDivData::data_plant,args[2],target)
dir.create(args[4],recursive=TRUE,showWarnings=FALSE)
writeLines(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),
  file.path(args[4],"neon_vst2026_forestpatch_original_season_effort_gate.json"))
cat(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
