#!/usr/bin/env Rscript
# Separate pre-2019 historical source-only NEON cohort.
# Original taxon_id/taxon_name/value columns are NEVER referenced.
# Old 2019-2023 PREDICTS and NEON source and outcome scores are SEALED.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))

YEARS<-2014:2018
VST_COMMIT<-"3391e702e7be80a3f049c905782661f043be8db8"
valid_id<-function(x) !is.na(x)&nzchar(trimws(as.character(x)))
source_year<-function(x){
  z<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  z[!(z%in%YEARS)]<-NA_integer_;z
}
source_day<-function(x) suppressWarnings(as.Date(substr(as.character(x),1,10)))
forest_plot<-function(x){
  z<-tolower(gsub("[[:space:]_/-]+","",trimws(as.character(x))))
  z[is.na(z)]<-""
  z %in% c("evergreenforest","deciduousforest","mixedforest")
}
ratio_ok<-function(x,y) {
  if(!is.finite(x)||!is.finite(y)||x<=0||y<=0)return(FALSE)
  x/y>=.5&&x/y<=2
}
core_fields_b<-c("siteID","plotID","unique_sample_id","trapID",
                 "trappingDays","trapConditionFlag","nlcdClass","observation_datetime")
core_fields_p<-c("siteID","plotID","unique_sample_id","subplotID",
                 "sample_area_m2","nlcdClass","observation_datetime")
source_frame<-function(beetle,plant,official){
  if(as.character(utils::packageVersion("neonDivData"))!="0.3.1")
    stop("SCIENTIFIC_STOP_NEON_PUBLISHED_DERIVATIVE_VERSION_DRIFT")
  if(!all(core_fields_b%in%names(beetle))||
     !all(core_fields_p%in%names(plant))||
     !all(c("site_id","domain_id","dominant_nlcd_classes")%in%names(official))||
     nrow(official)!=81)
    stop("SCIENTIFIC_STOP_ORIGINAL_SOURCE_SCHEMA_DRIFT")
  b<-as.data.frame(beetle[,core_fields_b,drop=FALSE])
  p<-as.data.frame(plant[,core_fields_p,drop=FALSE])
  b$year<-source_year(b$observation_datetime)
  p$year<-source_year(p$observation_datetime)
  b$day<-source_day(b$observation_datetime)
  p$day<-source_day(p$observation_datetime)
  bd<-suppressWarnings(as.numeric(as.character(b$trappingDays)))
  flags<-as.character(b$trapConditionFlag)
  size<-suppressWarnings(as.numeric(as.character(p$sample_area_m2)))
  bok<-!is.na(b$year)&!is.na(b$day)&forest_plot(b$nlcdClass)&
     valid_id(b$siteID)&valid_id(b$plotID)&valid_id(b$unique_sample_id)&
     valid_id(b$trapID)&is.finite(bd)&bd>0&
     (is.na(flags)|!nzchar(trimws(flags)))
  pok<-!is.na(p$year)&!is.na(p$day)&forest_plot(p$nlcdClass)&
     valid_id(p$siteID)&valid_id(p$plotID)&valid_id(p$unique_sample_id)&
     valid_id(p$subplotID)&is.finite(size)&abs(size-1)<1e-9
  b<-b[bok,,drop=FALSE]
  p<-p[pok,,drop=FALSE]
  make_key<-function(d)paste(d$siteID,d$plotID,d$year,sep="|")
  bkey<-make_key(b);pkey<-make_key(p)
  keys<-intersect(unique(bkey),unique(pkey))
  original_sites<-as.character(official$site_id)
  codes<-unique(sub("\\|[^|]+\\|[0-9]{4}$","",keys))
  if(any(!codes%in%original_sites))stop("SCIENTIFIC_STOP_NEON_SITE_NOT_IN_ORIGINAL_OFFICIAL_81")
  bs<-split(seq_len(nrow(b)),bkey);ps<-split(seq_len(nrow(p)),pkey)
  exact<-list();reasons<-character()
  for(k in keys) {
    bb<-b[bs[[k]],,drop=FALSE]
    pp<-p[ps[[k]],,drop=FALSE]
    first<-min(pp$day)
    pp<-pp[abs(as.numeric(pp$day-first))<=7,,drop=FALSE]
    bb<-bb[abs(as.numeric(bb$day-first))<=30,,drop=FALSE]
    if(!nrow(bb)||!nrow(pp)) {
      reasons<-c(reasons,"SOURCE_SEASONAL_NO_BEETLE_OR_PLANT");next
    }
    efforts<-split(suppressWarnings(as.numeric(as.character(bb$trappingDays))),
         as.character(bb$unique_sample_id))
    if(any(vapply(efforts,function(v)length(unique(v))!=1,logical(1)))){
      reasons<-c(reasons,"SCIENTIFIC_STOP_CONFLICTING_SOURCE_TRAP_EFFORT")
      next
    }
    nb<-length(efforts)
    np<-length(unique(as.character(pp$subplotID)))
    if(nb<4||np<4) {
      reasons<-c(reasons,"SOURCE_MIN_FOUR_BOTH_CHANNELS_NOT_MET");next
    }
    effort<-sum(vapply(efforts,function(v)v[1],numeric(1)))
    bits<-strsplit(k,"|",fixed=TRUE)[[1]]
    if(length(bits)!=3)stop("SCIENTIFIC_STOP_SOURCE_ORIGINAL_PLOT_YEAR_GRAIN_PARSE")
    exact[[k]]<-list(site=bits[1],plot=bits[2],year=as.integer(bits[3]),
                    first_plant_date=first,beetle_trap_days=effort,
                    plant_recorded_subplots=np,
                    source_unflagged_beetle_samples=nb)
  }
  list(
    exact=exact,candidates=keys,
    source_candidate_sites=sort(codes),
    source_sampled_plotyear_keys=length(keys),
    source_qualifying_four_sample_plotyear_keys=length(exact),
    meta_exclusions=as.list(table(reasons)),
    source_candidate_by_year=as.list(table(factor(
       sub("^.*\\|","",keys),levels=as.character(YEARS))))
  )
}
source_vst_for_candidate<-function(bundle,site,cohorts){
  if(!is.list(bundle)||!all(c("plots","trees","meta","contract")%in%names(bundle))||
      !identical(as.character(bundle$contract$id),"NEON-VST-DP1.10098.001-v2"))
    stop("SCIENTIFIC_STOP_PUBLISHED_VST_2026_CONTRACT_OR_SOURCE_SCHEMA_DRIFT")
  q<-bundle$plots;t<-bundle$trees
  qneed<-c("plotID","eventID","tree_support","area_trees","nlcdClass","date")
  tneed<-c("plotID","eventID","individualID","height","stemDiameter","growthForm")
  if(!all(qneed%in%names(q))||!all(tneed%in%names(t)))
    stop("SCIENTIFIC_STOP_PUBLISHED_VST_PLOT_EVENT_TREE_SCHEMA_DRIFT")
  if(!("live"%in%names(t)||"plantStatus"%in%names(t)))
    stop("SCIENTIFIC_STOP_PUBLISHED_VST_LIVE_STATUS_UNAVAILABLE")
  y<-source_year(q$date);qd<-source_day(q$date)
  area<-suppressWarnings(as.numeric(as.character(q$area_trees)))
  qok<-!is.na(y)&!is.na(qd)&valid_id(q$plotID)&valid_id(q$eventID)&
      forest_plot(q$nlcdClass)&is.finite(area)&area>0&
      q$tree_support=="sampled_with_records"
  q<-q[qok,,drop=FALSE];y<-y[qok];qd<-qd[qok]
  if(!nrow(q))return(character())
  qkey<-paste(q$plotID,q$eventID,sep="|")
  if(anyDuplicated(qkey)){
    by<-split(seq_along(qkey),qkey)
    if(any(vapply(by,function(i)length(unique(as.character(qd[i])))>1,logical(1))))
      stop("SCIENTIFIC_STOP_AUTHOR_VST_EVENT_DATE_CONFLICT")
  }
  # Original source event date used to match original first plant date.
  evdates<-setNames(qd,qkey)
  tkey<-paste(t$plotID,t$eventID,sep="|")
  hasq<-tkey%in%names(evdates)
  h<-suppressWarnings(as.numeric(as.character(t$height)))
  dbh<-suppressWarnings(as.numeric(as.character(t$stemDiameter)))
  gf<-tolower(trimws(as.character(t$growthForm)))
  islive<-if("live"%in%names(t)) {
    as.logical(t$live)%in%TRUE
  } else {
    tolower(trimws(as.character(t$plantStatus)))=="live"
  }
  qcheight<-if("size_height_ok"%in%names(t))as.logical(t$size_height_ok)%in%TRUE
            else rep(TRUE,nrow(t))
  goodtree<-hasq&valid_id(t$individualID)&is.finite(h)&h>0&
      is.finite(dbh)&dbh>=10&islive&qcheight&
      gf%in%c("single bole tree","multi-bole tree")
  if(!any(goodtree))return(character())
  tree_index<-split(which(goodtree),tkey[goodtree])
  selected<-character()
  for(k in names(cohorts)){
    o<-cohorts[[k]]
    if(o$site!=site)next
    qidx<-which(q$plotID==o$plot)
    qidx<-qidx[abs(as.numeric(qd[qidx]-o$first_plant_date))<=90]
    if(!length(qidx))next
    ids<-character()
    for(i in qidx){
      ek<-qkey[i]
      rows<-tree_index[[ek]]
      if(is.null(rows))next
      ids<-c(ids,as.character(t$individualID[rows]))
    }
    if(length(unique(ids))>=3)selected<-c(selected,k)
  }
  selected
}
pair_diagnostic<-function(cohorts,allowed){
  groups<-split(allowed,vapply(cohorts[allowed],function(x)
      paste(x$site,x$year,sep="|"),character(1)))
  pair_n<-0L;pair_effort<-0L;pair_plants<-0L;pair_season<-0L
  pair_ok<-0L;siteyears<-character()
  for(ky in names(groups)){
    ks<-groups[[ky]]
    if(length(ks)<2)next
    combos<-combn(ks,2)
    nmatch<-0L
    for(j in seq_len(ncol(combos))){
      a<-cohorts[[combos[1,j]]];b<-cohorts[[combos[2,j]]]
      eb<-ratio_ok(a$beetle_trap_days,b$beetle_trap_days)
      ep<-ratio_ok(a$plant_recorded_subplots,b$plant_recorded_subplots)
      et<-abs(as.numeric(a$first_plant_date-b$first_plant_date))<=30
      pair_n<-pair_n+1L
      pair_effort<-pair_effort+as.integer(eb)
      pair_plants<-pair_plants+as.integer(ep)
      pair_season<-pair_season+as.integer(et)
      nmatch<-nmatch+as.integer(eb&&ep&&et)
    }
    pair_ok<-pair_ok+nmatch
    if(nmatch>0)siteyears<-c(siteyears,ky)
  }
  list(eligible_original_site_years=unique(siteyears),
       original_candidate_plot_pairs_NONINDEPENDENT=pair_n,
       original_pairs_beetle_effort_ratio=pair_effort,
       original_pairs_plant_recorded_subplots_ratio=pair_plants,
       original_pairs_plant_first_date_within30=pair_season,
       original_pairs_all_fixed_effort_season_gates=pair_ok)
}
tests<-function(){
  stopifnot(identical(forest_plot(c("deciduousForest","Mixed Forest",
         "shrubScrub","evergreenForest")),c(TRUE,TRUE,FALSE,TRUE)))
  stopifnot(all(source_year(c("2014-01-01","2018-12-10"))==c(2014,2018)),
            is.na(source_year("2019-02-02")))
  # R's original source library must be pinned even in known-truth mode.
  official<-data.frame(site_id=c(paste0("S",sprintf("%03d",1:81))),
       domain_id=rep("D01",81),dominant_nlcd_classes=rep("Grassland",81))
  b<-data.frame(siteID=rep("S001",8),plotID=rep("S001_P1",8),
      unique_sample_id=paste0("b",1:8),trapID=paste0("t",1:8),
      trappingDays=14,trapConditionFlag=NA_character_,
      nlcdClass="mixedForest",observation_datetime="2016-06-15")
  p<-data.frame(siteID=rep("S001",8),plotID=rep("S001_P1",8),
      unique_sample_id=paste0("p",1:8),subplotID=paste0("q",1:8),
      sample_area_m2=1,nlcdClass="mixedForest",observation_datetime="2016-06-15")
  c<-source_frame(b,p,official)
  stopifnot(c$source_sampled_plotyear_keys==1,
    c$source_qualifying_four_sample_plotyear_keys==1)
  tree<-data.frame(plotID=rep("S001_P1",3),eventID="E2016",
      individualID=c("T1","T2","T3"),height=c(12,15,17),
      stemDiameter=c(14,17,19),growthForm="single bole tree",
      live=TRUE,size_height_ok=TRUE)
  q<-data.frame(plotID="S001_P1",eventID="E2016",
       date="2016-06-20",tree_support="sampled_with_records",
       area_trees=400,nlcdClass="mixedForest")
  bundle<-list(plots=q,trees=tree,meta=list(),contract=list(id="NEON-VST-DP1.10098.001-v2"))
  z<-source_vst_for_candidate(bundle,"S001",c$exact)
  stopifnot(length(z)==1)
  bundle$plots$date<-"2016-12-01"
  stopifnot(length(source_vst_for_candidate(bundle,"S001",c$exact))==0)
  bundle$plots$date<-"2016-06-20"
  bundle$trees$size_height_ok[2]<-FALSE
  stopifnot(length(source_vst_for_candidate(bundle,"S001",c$exact))==0)
  cat("HISTORICAL 2014–18 original forest source grain/date/height QA known truths PASS\n")
}
if(identical(Sys.getenv("NEON_HISTORICAL_SOURCE_SYNTHETIC_ONLY"),"1")){
  tests();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)<2)stop("usage: Rscript neon_vst2026_historical_2014_2018_source_gate.R OFFICIAL_CSV CANDIDATE_SITE_CODES_PATH [PUBLIC_VST_RDS_DIR ANONYMIZED_OUT]")
tests()
official<-read.csv(args[1],stringsAsFactors=FALSE,check.names=FALSE)
meta<-source_frame(neonDivData::data_beetle,neonDivData::data_plant,official)
if(length(args)==2){
   dir.create(dirname(args[2]),recursive=TRUE,showWarnings=FALSE)
   writeLines(meta$source_candidate_sites,args[2])
   cat("HISTORICAL 2014–18 SOURCE_SITES:",length(meta$source_candidate_sites),
       "candidate original plot-years:",meta$source_sampled_plotyear_keys,
       "pre-VST >=4 samples both taxa:",meta$source_qualifying_four_sample_plotyear_keys,"\n")
   quit(status=0)
}
if(length(args)!=4)stop("SCIENTIFIC_STOP_HISTORICAL_SOURCE_CLI")
dir.create(args[4],recursive=TRUE,showWarnings=FALSE)
files<-list.files(args[3],pattern="^[A-Z0-9]{4}\\.rds$",full.names=TRUE)
matched<-character();missing_sites<-character()
for(site in meta$source_candidate_sites){
  f<-file.path(args[3],paste0(site,".rds"))
  if(!file.exists(f)){missing_sites<-c(missing_sites,site);next}
  z<-source_vst_for_candidate(readRDS(f),site,meta$exact)
  matched<-union(matched,z)
}
matched<-sort(unique(matched))
comparison<-pair_diagnostic(meta$exact,matched)
pairsites<-unique(sub("\\|[0-9]{4}$","",comparison$eligible_original_site_years))
d<-unique(as.character(official$domain_id[match(pairsites,official$site_id)]))
if(anyNA(d))stop("SCIENTIFIC_STOP_HISTORICAL_SOURCE_DOMAIN_UNMAPPED")
admit<-length(pairsites)>=10&&length(d)>=6&&
        length(comparison$eligible_original_site_years)>=12
status<-if(admit) {
  "HISTORICAL_SOURCE_GEOGRAPHY_AND_METHOD_METADATA_ELIGIBLE_BUT_BIOLOGY_SEALED"
} else {
  "SCIENTIFIC_STOP_HISTORICAL_SOURCE_PLOT_SEASON_EFFORT_INSUFFICIENT"
}
r<-list(
 schema="structural.NEON_2014_2018_historical_forestpatch_three_source_method_gate.v1",
 source_study_population="new 2014-2018 historical source-only cohort, no retrospective rescue of 2019-2023 scores",
 source_study_years=as.integer(YEARS),
 original_beetle_published_latest_year=2023,
 original_plant_published_latest_year=2024,
 original_woody_vst_RELEASE2026_latest_year=2024,
 source_beetle_plant_derivative="neonDivData 0.3.1",
 source_VST_published_exact_git_commit=VST_COMMIT,
 historical_beetle_plant_usable_source_plotyears_without_woody=meta$source_sampled_plotyear_keys,
 historical_beetle_plant_source_plotyear_counts_by_calendar_year=meta$source_candidate_by_year,
 historical_beetle_plant_4sample_and_4recorded_plant_subplot_plotyears=meta$source_qualifying_four_sample_plotyear_keys,
 historical_source_only_species_measurement_unopened_drop_reasons=meta$meta_exclusions,
 historical_forest_patch_sites_with_both_taxa_metadata=length(meta$source_candidate_sites),
 original_public_VST_source_site_bundles_missing_for_candidate_sites=length(missing_sites),
 historical_VST_original_forest_plotyears_with_3_live_DBH10_height_QA_and_plant_beetle_season_overlap=length(matched),
 historical_VST_site_count_with_three_source_year_alignment=length(unique(sub("\\|[^|]+\\|[0-9]{4}$","",matched))),
 historical_VST_three_source_plotyears_by_year=as.list(table(factor(
    sub("^.*\\|","",matched),levels=as.character(YEARS)))),
 original_same_siteyear_candidate_plot_pairs_nonindependent=comparison$original_candidate_plot_pairs_NONINDEPENDENT,
 original_same_siteyear_pairs_beetle_effort_ratio_0p5to2=comparison$original_pairs_beetle_effort_ratio,
 original_same_siteyear_pairs_plant_recorded_subplot_ratio_0p5to2=comparison$original_pairs_plant_recorded_subplots_ratio,
 original_same_siteyear_pairs_plant_first_date_within30days=comparison$original_pairs_plant_first_date_within30,
 original_same_siteyear_pairs_all_three_requirements=comparison$original_pairs_all_fixed_effort_season_gates,
 original_independent_NEON_sites_with_geographically_matched_forest_patch_pairs=length(pairsites),
 original_NEON_ecoclimatic_domains_with_geographically_matched_forest_patch_pairs=length(d),
 original_same_siteyear_groups_with_2plot_source_effort_and_date_matched=length(comparison$eligible_original_site_years),
 frozen_historical_10sites_6domains_12siteyears_threshold_PASS=admit,
 historical_source_only_status=status,
 prior_2019_2023_10site_8domain_10siteyear_source_STOP_NOT_REWRITTEN=TRUE,
 PREDICTS_original_39_study_positive_forest_result_sealed=TRUE,
 NEON_7forest_cross_taxon_no_synchrony_result_sealed=TRUE,
 raw_source_site_plot_woody_individual_taxon_names_coordinates_not_exported=TRUE,
 no_plant_or_beetle_taxon_name_id_abundance_value_or_beta_ACCESS=TRUE,
 actual_tree_height_values_ONLY_QC_read_NOT_EFFECT_SCORED=TRUE,
 season_method_matched_woody_height_not_canopy_microclimate=TRUE,
 source_plant_positive_only_subplots_not_true_effort_absence=TRUE,
 eBird_used=FALSE
)
out<-file.path(args[4],"neon_historical_2014_2018_source_only_forest_patch_gate.json")
writeLines(jsonlite::toJSON(r,auto_unbox=TRUE,pretty=TRUE,null="null"),out)
cat(jsonlite::toJSON(r,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
