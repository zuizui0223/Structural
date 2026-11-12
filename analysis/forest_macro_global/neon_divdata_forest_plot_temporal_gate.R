#!/usr/bin/env Rscript
# Frozen in source-only phase. neonDivData 0.3.1 beetle and plant 2019-2023:
# examine author plotID, sample effort, subplot area, sample dates in the eight
# forest-only NEON sites. Do NOT touch taxon_id/taxon_name/value, no biodiversity
# response and no raw source IDs/coordinates/export.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))
good_year <- function(x) {
  z<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  z[!(z %in% 2019:2023)]<-NA_integer_;z
}
good_date <- function(x){
  suppressWarnings(as.Date(substr(as.character(x),1,10)))
}
source_plot_forest <- function(x){
 # The published neonDivData 0.3.1 plot-level NLCD codes are camelCase.
 y<-tolower(gsub("[[:space:]_-]","",as.character(x)))
 y[is.na(y)]<-""
 y %in% c("deciduousforest","evergreenforest","mixedforest")
}
only_forest <- function(meta) {
  cls<-as.character(meta$dominant_nlcd_classes)
  vapply(strsplit(cls,"|",fixed=TRUE),function(z){
    z<-trimws(z);z<-z[nzchar(z)]
    length(z)>0 && all(z %in% c("Deciduous Forest","Evergreen Forest","Mixed Forest"))
  },logical(1))
}
clean <- function(d, fields) {
  if(!all(fields %in% names(d))) stop(paste("STOP_PUBLIC_NEON_DERIVATIVE_METADATA_SCHEMA",paste(setdiff(fields,names(d)),collapse=",")))
  z<-d[,fields,drop=FALSE]
  z$year<-good_year(z$observation_datetime)
  z<-z[!is.na(z$year),,drop=FALSE]
  z$date<-good_date(z$observation_datetime)
  z
}
distinct_valid <- function(z) {
  z<-as.character(z);length(unique(z[!is.na(z)&nzchar(z)]))
}
key_siteyears <- function(d) {
  unique(paste(d$siteID,d$year,sep="|"))
}
counts_by_category <- function(z) {
  z<-trimws(as.character(z));z[is.na(z)|!nzchar(z)]<-"(missing)"
  t<-sort(table(z),decreasing=TRUE)
  # categories (land-cover labels) only, never site/plot IDs
  out<-as.list(as.integer(t[seq_len(min(12,length(t)))]))
  names(out)<-names(t)[seq_len(min(12,length(t)))]
  out
}
forest_plot_label <- function(x) {
  z<-tolower(gsub("[[:space:]_/-]+","",trimws(as.character(x))))
  z[is.na(z)]<-""
  z %in% c("deciduousforest","evergreenforest","mixedforest")
}
# All conditions must occur on the SAME original site, plot and sampling year,
# with at least one acceptable beetle and plant sampling date <=30 days apart.
# Never let three different plots jointly pass a site-year criterion.
qualified_plot_periods <- function(bb,pp) {
  bp<-as.character(bb$plotID);ppid<-as.character(pp$plotID)
  plots<-intersect(unique(bp[!is.na(bp)&nzchar(bp)]),
                   unique(ppid[!is.na(ppid)&nzchar(ppid)]))
  matched<-character()
  effortplots<-character()
  for(pl in plots) {
    b<-bb[!is.na(bp)&bp==pl,,drop=FALSE]
    p<-pp[!is.na(ppid)&ppid==pl,,drop=FALSE]
    days<-suppressWarnings(as.numeric(as.character(b$trappingDays)))
    area<-suppressWarnings(as.numeric(as.character(p$sample_area_m2)))
    bk<-as.character(b$unique_sample_id);pk<-as.character(p$unique_sample_id)
    flags<-as.character(b$trapConditionFlag)
    bpass<-is.finite(days)&days>0&!is.na(bk)&nzchar(bk)&
      !is.na(b$trapID)&nzchar(as.character(b$trapID))&
      (is.na(flags)|!nzchar(trimws(flags)))&
      forest_plot_label(b$nlcdClass)&!is.na(b$date)
    ppass<-is.finite(area)&abs(area-1)<1e-9&!is.na(pk)&nzchar(pk)&
      forest_plot_label(p$nlcdClass)&!is.na(p$date)
    if(!any(bpass)||!any(ppass))next
    effortplots<-c(effortplots,pl)
    bd<-sort(unique(b$date[bpass]))
    pd<-sort(unique(p$date[ppass]))
    if(any(abs(outer(as.numeric(bd),as.numeric(pd),"-"))<=30)){
      matched<-c(matched,pl)
    }
  }
  list(original_same_plot_valid_effort_and_1m2=length(unique(effortplots)),
       original_plot_ids_qualified=unique(matched))
}

assess <- function(beetle,plant,siteinfo,expected_version="0.3.1"){
  if(as.character(utils::packageVersion("neonDivData"))!=expected_version)
    stop("STOP_PUBLIC_NEON_DERIVATIVE_VERSION_CHANGED")
  expected_site<-c("site_id","domain_id","dominant_nlcd_classes","mean_canopy_height_m")
  if(!all(expected_site%in%names(siteinfo)) || nrow(siteinfo)!=81)
    stop("STOP_NEON_ORIGINAL_20260805_81_SITE_TABLE_SCHEMA")
  sid<-as.character(siteinfo$site_id)
  if(anyDuplicated(sid))stop("STOP_DUPLICATE_NEON_OFFICIAL_SITES")
  forest<-only_forest(siteinfo)
  b<-clean(beetle,c("siteID","plotID","unique_sample_id","trapID",
   "observation_datetime","trappingDays","trapConditionFlag","nlcdClass"))
  p<-clean(plant,c("siteID","plotID","unique_sample_id",
   "observation_datetime","sample_area_m2","nlcdClass"))
  allowed<-sid[forest]
  b<-b[as.character(b$siteID)%in%allowed,,drop=FALSE]
  p<-p[as.character(p$siteID)%in%allowed,,drop=FALSE]
  sy<-sort(intersect(key_siteyears(b),key_siteyears(p)))
  if(length(sy)!=40 || distinct_valid(sub("\\|[0-9]{4}$","",sy))!=8)
    stop("STOP_PREVIOUS_FOREST_SITE_YEAR_SUPPORT_NOT_REPRODUCED")
  if(length(unique(siteinfo$domain_id[match(unique(sub("\\|[0-9]{4}$","",sy)),sid)]))!=7)
    stop("STOP_PREVIOUS_FOREST_DOMAIN_SUPPORT_NOT_REPRODUCED")
  groups<-list()
  for(k in sy){
    v<-strsplit(k,"|",fixed=TRUE)[[1]]
    si<-v[1];yr<-as.integer(v[2])
    bb<-b[as.character(b$siteID)==si & b$year==yr,,drop=FALSE]
    pp<-p[as.character(p$siteID)==si & p$year==yr,,drop=FALSE]
    plotb<-unique(as.character(bb$plotID))
    plotp<-unique(as.character(pp$plotID))
    plotb<-plotb[!is.na(plotb)&nzchar(plotb)]
    plotp<-plotp[!is.na(plotp)&nzchar(plotp)]
    shared<-intersect(plotb,plotp)
    bforestplot<-unique(as.character(bb$plotID[source_plot_forest(bb$nlcdClass)]))
    pforestplot<-unique(as.character(pp$plotID[source_plot_forest(pp$nlcdClass)]))
    sharedforest<-intersect(intersect(bforestplot,pforestplot),shared)
    area<-suppressWarnings(as.numeric(as.character(pp$sample_area_m2)))
    trapdays<-suppressWarnings(as.numeric(as.character(bb$trappingDays)))
    bvalid<-is.finite(trapdays)&trapdays>0&!is.na(bb$unique_sample_id)&
              nzchar(as.character(bb$unique_sample_id))
    bsids<-unique(as.character(bb$unique_sample_id[bvalid]))
    bsids<-bsids[!is.na(bsids)&nzchar(bsids)]
    pvalid<-is.finite(area)&area>0&!is.na(pp$unique_sample_id)&
              nzchar(as.character(pp$unique_sample_id))
    psids<-unique(as.character(pp$unique_sample_id[pvalid]))
    psids<-psids[!is.na(psids)&nzchar(psids)]
    p1<-is.finite(area)&abs(area-1)<1e-9
    p1sids<-unique(as.character(pp$unique_sample_id[pvalid&p1]))
    p1sids<-p1sids[!is.na(p1sids)&nzchar(p1sids)]
    mb<-unique(format(bb$date[!is.na(bb$date)],"%Y-%m"))
    mp<-unique(format(pp$date[!is.na(pp$date)],"%Y-%m"))
    db<-sort(unique(bb$date[!is.na(bb$date)]))
    dp<-sort(unique(pp$date[!is.na(pp$date)]))
    mindiff<-if(length(db)&&length(dp)){
       min(abs(outer(as.numeric(db),as.numeric(dp),"-")))
    } else Inf
    flags<-as.character(bb$trapConditionFlag)
    nflags<-sum(!is.na(flags)&nzchar(flags))
    exact<-qualified_plot_periods(bb,pp)
    exact_keys<-paste(si,exact$original_plot_ids_qualified,sep="|")
    # preserve original plot-year support, never pseudoreplicate taxon rows
    groups[[k]]<-list(
      site=si,year=yr,
      bplots=length(plotb),pplots=length(plotp),sharedplots=length(shared),
      bforestplots=length(bforestplot),pforestplots=length(pforestplot),
      sharedforestplots=length(sharedforest),
      bvalidsamples=length(bsids),pvalidsamples=length(psids),
      p1msamples=length(p1sids),
      monthmatch=length(intersect(mb,mp))>0,
      nearest_days=mindiff,
      any_condition_flag=nflags>0,
      b_plot_keys=paste(si,plotb,sep="|"),
      p_plot_keys=paste(si,plotp,sep="|"),
      shared_plot_keys=paste(si,shared,sep="|"),
      original_qualified_plot_keys=exact_keys,
      source_sameplot_effort_1m2_count=exact$original_same_plot_valid_effort_and_1m2,
      source_sameplot_effort_1m2_30day_count=length(exact$original_plot_ids_qualified),
      shared_forest_plot_keys=paste(si,sharedforest,sep="|")
    )
  }
  good<-vapply(groups,function(x)x$bvalidsamples>0 && x$p1msamples>0,
               logical(1))
  shared<-vapply(groups,function(x)x$sharedplots>0,logical(1))
  shared_source_forest<-vapply(groups,function(x)x$sharedforestplots>0,logical(1))
  nearby<-vapply(groups,function(x)x$nearest_days<=30,logical(1))
  overlap<-vapply(groups,function(x)x$monthmatch,logical(1))
  sitekeys<-vapply(groups,function(x)x$site,character(1))
  yrkeys<-vapply(groups,function(x)x$year,integer(1))
  tby<-lapply(2019:2023,function(yr){
    k<-yrkeys==yr
    list(calendar_year=yr,
      forest_sites_with_both_taxa=sum(k),
      forest_siteyears_same_orig_plot=sum(k&shared),
      forest_siteyears_beetle_effort_and_plant_1m2=sum(k&good),
      forest_siteyears_nearest_taxon_sampling_within_30days=sum(k&nearby),
      median_beetle_original_plots_per_site=median(vapply(groups[k],
             function(x)x$bplots,numeric(1))),
      median_plant_original_plots_per_site=median(vapply(groups[k],
             function(x)x$pplots,numeric(1))))
  })
  all_bplots<-unique(unlist(lapply(groups,function(v)v$b_plot_keys),use.names=FALSE))
  all_pplots<-unique(unlist(lapply(groups,function(v)v$p_plot_keys),use.names=FALSE))
  all_shplots<-intersect(all_bplots,all_pplots)
  qualified_sites<-unique(sitekeys[good&shared_source_forest&nearby])
  # Critical 2023 ground-beetle protocol shift: source counts may move
  # from ten to six original plotIDs. Only paired year intervals retaining
  # at least one SAME originally sampled plot in both years are suitable
  # candidates for later taxon turnover analyses.
  qualified_keys<-names(groups)[good&shared_source_forest&nearby]
  q_by_site<-split(qualified_keys,sitekeys[good&shared_source_forest&nearby])
  transitions<-0L
  transitions_sites<-character(0)
  overlap2022to2023<-0L
  for(si in names(q_by_site)){
    qk<-q_by_site[[si]]
    yr<-sort(unique(as.integer(sub("^.*\\|","",qk))))
    if(length(yr)<2)next
    for(y in yr){
      if(!((y+1L) %in% yr))next
      one<-paste(si,y,sep="|")
      two<-paste(si,y+1L,sep="|")
      if(!(one%in%names(groups) && two%in%names(groups)))next
      original_plots_both_years<-intersect(groups[[one]]$shared_forest_plot_keys,
                                        groups[[two]]$shared_forest_plot_keys)
      if(length(original_plots_both_years)>0){
        transitions<-transitions+1L
        transitions_sites<-c(transitions_sites,si)
        if(y==2022L)overlap2022to2023<-overlap2022to2023+1L
      }
    }
  }
  minimum_support<-length(unique(transitions_sites))>=6 &&
     transitions>=16 &&
     length(unique(siteinfo$domain_id[match(unique(transitions_sites),sid)]))>=4
  return(list(
    schema="structural.neonDivData_0.3.1_official_NEON_forest_plot_temporal_support.v1",
    original_NEON_metadata_release="2026-08-05",
    original_derivative_version=expected_version,
    candidate_strict_NLCD_forest_NEON_sites=distinct_valid(sitekeys),
    candidate_strict_forest_siteyears=length(groups),
    original_2019_2023_forest_site_years_by_calendar_year=tby,
    siteyears_with_actual_both_taxa_original_plotID_overlap=sum(shared),
    siteyears_with_original_plotlevel_forest_NLCD_for_both_taxa=sum(shared_source_forest),
    siteyears_original_plotlevel_forest_NLCD_same_plot_plant1m2_beetle_effort_30days=sum(
        good&shared_source_forest&nearby),
    original_plot_keys_with_beetle_sampling_in_forest_siteyear=length(all_bplots),
    original_plot_keys_with_plant_sampling_in_forest_siteyear=length(all_pplots),
    original_plot_keys_seen_by_both_taxa_some_year=length(all_shplots),
    original_siteyears_with_any_beetle_positive_effort_and_plant_positive_area=sum(vapply(
      groups,function(x)x$bvalidsamples>0&&x$pvalidsamples>0,logical(1))),
    original_siteyears_with_positive_beetle_effort_and_plant_1m2_samples=sum(good),
    original_siteyears_with_same_calendar_month_of_both_taxa=sum(overlap),
    original_siteyears_with_nearest_sample_dates_within_30days=sum(nearby),
    siteyears_exact_plot_effort_plant1m2_and_30day_supported=sum(good&shared_source_forest&nearby),
    distinct_forest_sites_exact_plot_effort_plant1m2_and_30day_supported=length(qualified_sites),
    consecutive_siteyear_transitions_exact_plot_effort_plant1m2_and_30day_supported=transitions,
    source_forest_sites_retaining_exact_same_original_plot_in_consecutive_suitable_years=length(unique(transitions_sites)),
    source_forest_ecoclimatic_domains_represented_in_strict_consecutive_plot_support=length(unique(
       siteinfo$domain_id[match(unique(transitions_sites),sid)])),
    source_original_plot_matched_2022_to_2023_transitions=overlap2022to2023,
    source_only_preoutcome_minimum_6sites_4domains_16consecutive_plotyears_passed=minimum_support,
    siteyear_count_is_not_independent_forest_network_count=TRUE,
    forest_beetle_siteyears_with_original_sample_condition_flag=sum(vapply(
      groups,function(x)x$any_condition_flag,logical(1))),
    forest_siteyear_beetle_plot_counts_median=median(vapply(groups,function(x)x$bplots,numeric(1))),
    forest_siteyear_plant_plot_counts_median=median(vapply(groups,function(x)x$pplots,numeric(1))),
    forest_plant_1m2_sample_count_siteyear_median=median(vapply(groups,function(x)x$p1msamples,numeric(1))),
    forest_beetle_valid_sample_count_siteyear_median=median(vapply(groups,function(x)x$bvalidsamples,numeric(1))),
    original_derived_beetle_nlcdClass_metadata_category_counts=counts_by_category(b$nlcdClass),
    original_derived_plant_nlcdClass_metadata_category_counts=counts_by_category(p$nlcdClass),
    cannot_claim_true_zero_or_comparable_effort_from_record_count=TRUE,
    unflagged_trap_level_methods_and_bout_coverage_NOT_fully_validated=TRUE,
    original_NLCD_site_context_not_a_beetle_or_plant_plot_specific_forest_proof=TRUE,
    original_beetle_ground_traps_NOT_canopy_strata=TRUE,
    original_tree_height_NOT_contemporaneous_plot_measurement=TRUE,
    species_taxon_id_name_value_and_biodiversity_composition_NEVER_ACCESSED=TRUE,
    original_site_plot_sample_event_identifiers_coordinates_NOT_EXPORTED=TRUE,
    no_ecological_effect_or_species_turnover_claim=TRUE,
    eBird_used=FALSE
  ))
}
synthetic<-function(){
  m<-data.frame(site_id=paste0("S",sprintf("%03d",1:81)),
     domain_id=c("D1","D2",rep("D3",79)),
     dominant_nlcd_classes=c("Evergreen Forest","Mixed Forest",rep("Grassland/Herbaceous",79)),
     mean_canopy_height_m=c(14,21,rep(0,79)))
  b<-data.frame(siteID=c("S001","S001","S002","S003"),
    plotID=c("P1","P1","P5","P8"),unique_sample_id=c("b1","b2","b3","b4"),
    trapID=c("T1","T1","T1","T1"),observation_datetime=
      c("2019-07-01","2020-07-01","2019-07-15","2019-08-01"),
    trappingDays=14,trapConditionFlag=NA_character_,
    nlcdClass="Evergreen forest")
  p<-data.frame(siteID=c("S001","S001","S002","S003"),
    plotID=c("P1","P1","P6","P8"),unique_sample_id=c("p1","p2","p3","p4"),
    observation_datetime=c("2019-07-12","2020-07-10","2019-08-15","2019-08-10"),
    sample_area_m2=1,nlcdClass="Evergreen forest")
  # Freeze an independent pure computational test on a flexible synthetic
  # dataset, separate from the actual 8/40 source gate.
  stopifnot(sum(only_forest(m))==2,
    all(good_year(b$observation_datetime)==c(2019,2020,2019,2019)),
    all(!is.na(good_date(b$observation_datetime))),
    distinct_valid(c("P1","P1","P2",""))==2)
  many<-data.frame(site_id=paste0("S",sprintf("%03d",1:81)),
    domain_id=c(paste0("D",c(1:7,7)),rep("D8",73)),
    dominant_nlcd_classes=c(rep("Deciduous Forest",8),rep("Grassland/Herbaceous",73)),
    mean_canopy_height_m=c(rep(18,8),rep(0,73)))
  pair<-expand.grid(site=1:8,yr=2019:2023)
  sitecode<-paste0("S",sprintf("%03d",pair$site))
  dt<-paste0(pair$yr,"-07-10")
  plantdate<-paste0(pair$yr,"-07-13")
  synthetic_b<-data.frame(siteID=sitecode,
    plotID=paste0(sitecode,"_P1"),
    unique_sample_id=paste0("b",seq_len(nrow(pair))),
    trapID="trap1",observation_datetime=dt,
    trappingDays=14,trapConditionFlag=NA_character_,nlcdClass="evergreenForest")
  synthetic_p<-data.frame(siteID=sitecode,
    plotID=paste0(sitecode,"_P1"),
    unique_sample_id=paste0("p",seq_len(nrow(pair))),
    observation_datetime=plantdate,
    sample_area_m2=1,nlcdClass="evergreenForest")
  v<-assess(synthetic_b,synthetic_p,many)
  stopifnot(v$candidate_strict_NLCD_forest_NEON_sites==8,
      v$candidate_strict_forest_siteyears==40,
      v$siteyears_with_actual_both_taxa_original_plotID_overlap==40,
      v$siteyears_with_original_plotlevel_forest_NLCD_for_both_taxa==40,
      v$siteyears_exact_plot_effort_plant1m2_and_30day_supported==40,
      v$distinct_forest_sites_exact_plot_effort_plant1m2_and_30day_supported==8,
      v$consecutive_siteyear_transitions_exact_plot_effort_plant1m2_and_30day_supported==32,
      v$source_forest_sites_retaining_exact_same_original_plot_in_consecutive_suitable_years==8,
      v$source_forest_ecoclimatic_domains_represented_in_strict_consecutive_plot_support==7,
      v$source_original_plot_matched_2022_to_2023_transitions==8,
      v$source_only_preoutcome_minimum_6sites_4domains_16consecutive_plotyears_passed,
      v$original_plot_keys_seen_by_both_taxa_some_year==8,
      v$species_taxon_id_name_value_and_biodiversity_composition_NEVER_ACCESSED)
  cat("SYNTHETIC PASS: 8 sites, 40 plot-year co-locations, 32 consecutive year links, no taxa\n")
}
if(identical(Sys.getenv("NEON_FOREST_PLOT_TIMING_SYNTHETIC_ONLY"),"1")){
 synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=2)stop("Usage: Rscript neon_divdata_forest_plot_temporal_gate.R OUT OFFICIAL_SITE_CSV")
synthetic()
dir.create(args[1],recursive=TRUE,showWarnings=FALSE)
official<-utils::read.csv(args[2],stringsAsFactors=FALSE,check.names=FALSE)
r<-assess(neonDivData::data_beetle,neonDivData::data_plant,official)
dest<-file.path(args[1],"NEON_forest_47site_8forest_plottemporal_sourceonly.json")
writeLines(jsonlite::toJSON(r,auto_unbox=TRUE,pretty=TRUE,null="null"),dest)
cat(jsonlite::toJSON(r,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
