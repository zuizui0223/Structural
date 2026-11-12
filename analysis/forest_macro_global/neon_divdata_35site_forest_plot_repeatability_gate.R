#!/usr/bin/env Rscript
# Source-only strict forest plot temporal sampling gate (neonDivData v0.3.1).
# No species/taxon_id/taxon_name/value or numerical diversity responses read.
# Real original site, plot, sample and trap/subplot keys only on CI runner;
# output 100% anonymous counts. Updated NEON site source is a fixed 81-site
# external context; it does not prove plot-height or causal microclimate.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))

YEAR<-2019:2023
forest_code<-function(x){
 v<-tolower(gsub("[[:space:]_-]","",as.character(x)))
 v[is.na(v)]<-""
 v%in%c("deciduousforest","evergreenforest","mixedforest")
}
year<-function(x){
 z<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
 z[!(z%in%YEAR)]<-NA_integer_;z
}
date<-function(x) suppressWarnings(as.Date(substr(as.character(x),1,10)))
nonempty<-function(x) !is.na(x)&nzchar(trimws(as.character(x)))
strict_flag_ok<-function(x) is.na(x)|!nzchar(trimws(as.character(x)))
count_unique<-function(x)length(unique(as.character(x)[nonempty(x)]))
sample_support<-function(b,p,meta,lock=TRUE){
  cols_b<-c("siteID","plotID","unique_sample_id","trapID",
            "observation_datetime","nlcdClass","trappingDays","trapConditionFlag")
  cols_p<-c("siteID","plotID","unique_sample_id","subplotID",
            "observation_datetime","nlcdClass","sample_area_m2")
  if(!all(cols_b%in%names(b))||!all(cols_p%in%names(p)))
    stop("SCIENTIFIC_STOP_ORIGINAL_NEON_DERIVATIVE_SAMPLE_COLUMNS_CHANGED")
  cols_m<-c("site_id","domain_id","dominant_nlcd_classes","mean_canopy_height_m")
  if(!all(cols_m%in%names(meta))||nrow(meta)!=81)
    stop("SCIENTIFIC_STOP_OFFICIAL_NEON_SITE_TABLE_IDENTITY_CHANGED")
  bb<-b[,c(cols_b,intersect("sampleCondition",names(b))),drop=FALSE]
  pp<-p[,cols_p,drop=FALSE]
  bb$year<-year(bb$observation_datetime)
  pp$year<-year(pp$observation_datetime)
  bb<-bb[!is.na(bb$year)&nonempty(bb$siteID)&nonempty(bb$plotID)&
           forest_code(bb$nlcdClass),,drop=FALSE]
  pp<-pp[!is.na(pp$year)&nonempty(pp$siteID)&nonempty(pp$plotID)&
           forest_code(pp$nlcdClass),,drop=FALSE]
  if(!nrow(bb)||!nrow(pp))stop("SCIENTIFIC_STOP_NO_ORIGINAL_FOREST_PLOTS")
  bb$k<-paste(bb$siteID,bb$plotID,bb$year,sep="|")
  pp$k<-paste(pp$siteID,pp$plotID,pp$year,sep="|")
  group_b<-split(seq_len(nrow(bb)),bb$k)
  group_p<-split(seq_len(nrow(pp)),pp$k)
  co<-intersect(names(group_b),names(group_p))
  base_b<-unique(paste(bb$siteID,bb$year,sep="|"))
  base_p<-unique(paste(pp$siteID,pp$year,sep="|"))
  common_siteyears<-intersect(base_b,base_p)
  sitecodes<-unique(sub("\\|[0-9]{4}$","",common_siteyears))
  domain<-as.character(meta$domain_id[match(sitecodes,meta$site_id)])
  if(any(is.na(domain))||any(!nzchar(domain)))
    stop("SCIENTIFIC_STOP_UNMAPPED_NEON_SITE_DOMAIN")
  if(lock&&(length(sitecodes)!=35||length(common_siteyears)!=166||
            length(unique(domain))!=17||length(co)!=957))
    stop("SCIENTIFIC_STOP_FROZEN_PLOT_FOREST_35SITE_166YEAR_957PLOT_KEYS_DRIFT")
  source_sample_bad<-function(x){
    bad<-!strict_flag_ok(x$trapConditionFlag)
    if("sampleCondition"%in%names(x))
      bad<-bad|!strict_flag_ok(x$sampleCondition)
    bad
  }
  supports<-vector("list",length(co));names(supports)<-co
  source_plots_all<-unique(sub("\\|[0-9]{4}$","",co))
  for(i in seq_along(co)){
    k<-co[i]
    bi<-bb[group_b[[k]],,drop=FALSE]
    pi<-pp[group_p[[k]],,drop=FALSE]
    # Reject flagged/missing-effort source beetle events, not taxon rows.
    tr<-suppressWarnings(as.numeric(as.character(bi$trappingDays)))
    keepb<-is.finite(tr)&tr>0&!source_sample_bad(bi)&
       nonempty(bi$unique_sample_id)&nonempty(bi$trapID)
    ar<-suppressWarnings(as.numeric(as.character(pi$sample_area_m2)))
    keepp<-is.finite(ar)&abs(ar-1)<1e-9&
       nonempty(pi$unique_sample_id)&nonempty(pi$subplotID)
    bt<-bi[keepb,,drop=FALSE];pt<-pi[keepp,,drop=FALSE]
    bd<-date(bt$observation_datetime)
    pd<-date(pt$observation_datetime)
    bd<-sort(unique(bd[!is.na(bd)]))
    pd<-sort(unique(pd[!is.na(pd)]))
    dmin<-if(length(bd)&&length(pd))
       min(abs(outer(as.numeric(bd),as.numeric(pd),"-"))) else Inf
    good<-length(bd)>0&&length(pd)>0&&dmin<=30
    key_parts<-strsplit(k,"|",fixed=TRUE)[[1]]
    s<-key_parts[1]; yr<-as.integer(tail(key_parts,1))
    supports[[i]]<-list(
      site=s,plot=paste(key_parts[-c(1,length(key_parts))],collapse="|"),
      year=yr,
      good=good,near_days=dmin,
      valid_beetle_sample_n=count_unique(bt$unique_sample_id),
      plant_1m2_sample_n=count_unique(pt$unique_sample_id),
      unflagged_distinct_beetle_trapIDs=unique(as.character(bt$trapID)[nonempty(bt$trapID)]),
      one_m2_plant_subplotIDs=unique(as.character(pt$subplotID)[nonempty(pt$subplotID)]),
      beetle_trapping_days_positive_source_rows=sum(is.finite(tr)&tr>0),
      beetle_source_sample_flagged_row_n=sum(source_sample_bad(bi)),
      raw_beetle_original_plot_record_n=nrow(bi),
      raw_plant_original_plot_record_n=nrow(pi)
    )
  }
  elig<-supports[vapply(supports,function(x)isTRUE(x$good),logical(1))]
  syear<-unique(vapply(elig,function(x)paste(x$site,x$year,sep="|"),character(1)))
  rep_plot_pairs<-0L
  rep_siteyears<-set()
  rep_sites<-character(0)
  rep_plots<-character(0)
  rep_2023<-0L
  for(k in names(elig)){
    x<-elig[[k]]
    if(x$year>=2023L)next
    nextkey<-paste(x$site,x$plot,x$year+1L,sep="|")
    y<-elig[[nextkey]]
    if(is.null(y))next
    common_beetle<-intersect(x$unflagged_distinct_beetle_trapIDs,
                            y$unflagged_distinct_beetle_trapIDs)
    common_plant<-intersect(x$one_m2_plant_subplotIDs,
                           y$one_m2_plant_subplotIDs)
    if(!length(common_beetle)||!length(common_plant))next
    rep_plot_pairs<-rep_plot_pairs+1L
    rep_sites<-c(rep_sites,x$site)
    rep_plots<-c(rep_plots,paste(x$site,x$plot,sep="|"))
    rep_siteyears<-c(rep_siteyears,paste(x$site,x$year,sep="|"))
    if(x$year==2022L)rep_2023<-rep_2023+1L
  }
  # The site/year denominator is not the plot transition count. Each eligible
  # site×consecutive-year interval can contain many repeated physical plots.
  rep_sy<-unique(rep_siteyears)
  qualified_sites<-unique(rep_sites)
  qualified_domains<-unique(as.character(meta$domain_id[
       match(qualified_sites,meta$site_id)]))
  prespecified<-length(qualified_sites)>=15&&length(qualified_domains)>=8&&
                 length(rep_sy)>=40
  outbyyear<-lapply(YEAR,function(yr){
    f<-vapply(supports,function(x)x$year==yr,logical(1))
    z<-supports[f]
    list(year=yr,
      original_forest_plot_year_keys_in_both_taxa=length(z),
      original_forest_plot_year_keys_with_unflagged_effort_1m2_date30=sum(
        vapply(z,function(v)isTRUE(v$good),logical(1))),
      original_forest_sites_with_both_plot_sampling=count_unique(
        vapply(z,function(v)v$site,character(1))),
      repeated_original_plot_pairs_to_next_year=if(yr<2023)sum(
        vapply(rep_sy,function(x)grepl(paste0("\\|",yr,"$"),x),logical(1)))
        else 0L)
  })
  list(
     schema="structural.neonDivData_forest_plot_specific_strict_longitudinal_quality_v1",
     derivative_public_package_version=as.character(utils::packageVersion("neonDivData")),
     original_site_metadata_2026_08_05_81sites_verified=nrow(meta)==81,
     source_original_beetle_plant_forest_co_observed_sites=length(sitecodes),
     source_original_beetle_plant_forest_co_observed_siteyears=length(common_siteyears),
     source_original_forest_plant_beetle_same_plot_year_keys=length(co),
     source_original_domain_count_in_forest_plot_cohort=length(unique(domain)),
     strict_unflagged_trap_positive_days_plant_1m2_same_plot_nearest30day_plotyears=length(elig),
     strict_fieldsite_years_with_at_least_one_valid_plot=length(syear),
     strict_fieldsites_with_at_least_one_valid_plot=count_unique(
       vapply(elig,function(v)v$site,character(1))),
     strict_repeated_same_plot_unflagged_trap_and_1m2_subplot_consecutive_plotyear_pairs=rep_plot_pairs,
     strict_independent_site_consecutive_year_intervals=length(rep_sy),
     strict_original_distinct_sites_repeated_plot_trap_and_subplot=length(qualified_sites),
     strict_original_distinct_ecoclimatic_domains_repeated_plot_trap_and_subplot=length(qualified_domains),
     strict_2022_2023_protocol_transition_repeated_original_plot_pairs=rep_2023,
     strict_distinct_original_plot_keys_in_repeated_years=length(unique(rep_plots)),
     precommitted_min15sites_min8domains_min40_siteintervals_supported=prespecified,
     by_year_source_plot_support=outbyyear,
     output_source_sample_plot_site_taxon_names_coordinates_ORIGINAL_VALUES_NOT_EXPORTED=TRUE,
     original_beetle_species_taxa_abundances_and_plant_species_values_NEVER_READ=TRUE,
     published_pretoken_neonDivData_not_current_NEON_API=TRUE,
     source_sampling_effort_cannot_be_inferred_from_taxon_rowcounts=TRUE,
     source_beetles_are_ground_pitfall_NOT_vertical_canopy_traps=TRUE,
     source_plot_NLCD_not_contemporaneous_LiDAR_or_air_temperature=TRUE,
     no_biodiversity_effect_or_ecosystem_service_cascade_test_performed=TRUE,
     eBird_used=FALSE
  )
}
synthetic<-function(){
  stopifnot(all(forest_code(c("deciduousForest","mixedForest","evergreenForest"))),
    !any(forest_code(c("urban","openWater","NA"))),
    strict_flag_ok(NA_character_),
    !strict_flag_ok("fluid level below"),year("2023-10-05")==2023)
  x<-data.frame(site_id=paste0("S",sprintf("%03d",1:81)),
     domain_id=c("D1","D2",rep("D3",79)),dominant_nlcd_classes=c(
     "Deciduous Forest","Mixed Forest",rep("Grassland",79)),
     mean_canopy_height_m=c(17,23,rep(0,79)))
  b<-data.frame(siteID=c("S001","S001","S002","S002"),
     plotID=c("P1","P1","P2","P2"),
     unique_sample_id=c("B1","B2","B3","B4"),
     trapID=c("T1","T1","T2","T2"),
     observation_datetime=c("2019-07-05","2020-07-05",
                            "2019-08-05","2020-08-05"),
     nlcdClass="deciduousForest",
     trappingDays=14,trapConditionFlag=NA_character_)
  p<-data.frame(siteID=c("S001","S001","S002","S002"),
     plotID=c("P1","P1","P2","P2"),
     unique_sample_id=c("P1-19","P1-20","P2-19","P2-20"),
     subplotID=c("31_1_1","31_1_1","32_1_2","32_1_2"),
     observation_datetime=c("2019-07-10","2020-07-10",
                             "2019-08-10","2020-08-10"),
     nlcdClass="deciduousForest",sample_area_m2=1)
  r<-sample_support(b,p,x,lock=FALSE)
  stopifnot(r$source_original_beetle_plant_forest_co_observed_sites==2,
   r$source_original_beetle_plant_forest_co_observed_siteyears==4,
   r$source_original_forest_plant_beetle_same_plot_year_keys==4,
   r$strict_unflagged_trap_positive_days_plant_1m2_same_plot_nearest30day_plotyears==4,
   r$strict_repeated_same_plot_unflagged_trap_and_1m2_subplot_consecutive_plotyear_pairs==2,
   r$strict_independent_site_consecutive_year_intervals==2,
   r$strict_2022_2023_protocol_transition_repeated_original_plot_pairs==0,
   r$original_beetle_species_taxa_abundances_and_plant_species_values_NEVER_READ)
  # Changing original trap identity across year must invalidate one interval.
  b$trapID[2]<-"DIFFERENT_TRAP"
  r2<-sample_support(b,p,x,lock=FALSE)
  stopifnot(r2$strict_repeated_same_plot_unflagged_trap_and_1m2_subplot_consecutive_plotyear_pairs==1)
  # A flagged pitfall sampling event is ineligible in source-verified strict tier.
  b$trapConditionFlag[1]<-"fluid level below"
  r3<-sample_support(b,p,x,lock=FALSE)
  stopifnot(r3$strict_repeated_same_plot_unflagged_trap_and_1m2_subplot_consecutive_plotyear_pairs==1)
  cat("SYNTHETIC PASS source forest-only plot-year, 1 m2, trap flags, stable plot+trap+subplot, no taxa\n")
}
if(identical(Sys.getenv("NEON_35FOREST_SOURCE_ONLY_SYNTHETIC_ONLY"),"1")){
 synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=2)stop("Usage: Rscript neon_divdata_35site_forest_plot_repeatability_gate.R OUT OFFICIAL_SITE_CSV")
synthetic()
dir.create(args[1],recursive=TRUE,showWarnings=FALSE)
meta<-utils::read.csv(args[2],stringsAsFactors=FALSE,check.names=FALSE)
r<-sample_support(neonDivData::data_beetle,neonDivData::data_plant,meta)
if(r$derivative_public_package_version!="0.3.1")
 stop("STOP_SOURCE_PACKAGE_VERSION_DRIFT_AFTER_SOURCE_0p3p1_GATE")
writeLines(jsonlite::toJSON(r,auto_unbox=TRUE,pretty=TRUE,null="null"),
 file.path(args[1],"NEON_35forest_sites_strict_plotlevel_repeated_sampling_2019_2023.json"))
cat(jsonlite::toJSON(r,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
