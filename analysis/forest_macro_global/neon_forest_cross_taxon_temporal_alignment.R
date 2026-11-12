#!/usr/bin/env Rscript
# Single outcome-opening exploration after NEON 0.3.1 source-only plot/effort
# gates. Source metadata and biological outcomes are NOT jointly optimized.
# Primary response: site-equal within-site annual alignment of Simpson
# replacement across beetle and plant taxon lists. No forest-structure causal.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))

yr <- function(x) {
  y<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  y[!(y%in%2019:2023)]<-NA_integer_;y
}
date_of <- function(x) suppressWarnings(as.Date(substr(as.character(x),1,10)))
forest_plot <- function(x) {
  z<-tolower(gsub("[[:space:]_/-]+","",trimws(as.character(x))))
  z[is.na(z)]<-"";z%in%c("deciduousforest","evergreenforest","mixedforest")
}
forest_sites <- function(d) {
  vapply(strsplit(as.character(d$dominant_nlcd_classes),"|",fixed=TRUE),function(y) {
    y<-trimws(y);y<-y[nzchar(y)]
    length(y)>0 && all(y%in%c("Deciduous Forest","Evergreen Forest","Mixed Forest"))
  },logical(1))
}
select_metadata <- function(b,p,source) {
  if(as.character(utils::packageVersion("neonDivData"))!="0.3.1")
    stop("SCIENTIFIC_STOP_NEON_PACKAGE_VERSION_DRIFT")
  columns_b<-c("siteID","plotID","unique_sample_id","trapID","observation_datetime",
               "trappingDays","trapConditionFlag","nlcdClass")
  columns_p<-c("siteID","plotID","unique_sample_id","subplotID",
               "observation_datetime","sample_area_m2","nlcdClass")
  if(!all(columns_b%in%names(b))||!all(columns_p%in%names(p)))
    stop("SCIENTIFIC_STOP_NEON_DERIVATIVE_META_SCHEMA_DRIFT")
  if(nrow(source)!=81||!all(c("site_id","domain_id","dominant_nlcd_classes")%in%names(source)))
    stop("SCIENTIFIC_STOP_NEON_OFFICIAL_SITE_SOURCE_DRIFT")
  keep_sites<-as.character(source$site_id[forest_sites(source)])
  bm<-as.data.frame(b[,columns_b,drop=FALSE]);bm$.source_row<-seq_len(nrow(b))
  pm<-as.data.frame(p[,columns_p,drop=FALSE]);pm$.source_row<-seq_len(nrow(p))
  bm$year<-yr(bm$observation_datetime);pm$year<-yr(pm$observation_datetime)
  bm$date<-date_of(bm$observation_datetime);pm$date<-date_of(pm$observation_datetime)
  bm<-bm[!is.na(bm$year)&as.character(bm$siteID)%in%keep_sites,,drop=FALSE]
  pm<-pm[!is.na(pm$year)&as.character(pm$siteID)%in%keep_sites,,drop=FALSE]
  site_year_b<-unique(paste(bm$siteID,bm$year,sep="|"))
  site_year_p<-unique(paste(pm$siteID,pm$year,sep="|"))
  common_sy<-intersect(site_year_b,site_year_p)
  if(length(common_sy)!=40||length(unique(sub("\\|[0-9]{4}$","",common_sy)))!=8)
    stop("SCIENTIFIC_STOP_FROZEN_8SITE_40YEAR_SOURCE_DRIFT")
  list(beetle=bm,plant=pm,official=source)
}
valid_beetle <- function(d) {
  days<-suppressWarnings(as.numeric(as.character(d$trappingDays)))
  flag<-as.character(d$trapConditionFlag)
  sid<-as.character(d$unique_sample_id)
  tid<-as.character(d$trapID)
  is.finite(days)&days>0&!is.na(sid)&nzchar(sid)&
    !is.na(tid)&nzchar(tid)&(is.na(flag)|!nzchar(trimws(flag)))&
    forest_plot(d$nlcdClass)&!is.na(d$date)
}
valid_plant <- function(d) {
  size<-suppressWarnings(as.numeric(as.character(d$sample_area_m2)))
  sid<-as.character(d$unique_sample_id)
  sub<-as.character(d$subplotID)
  is.finite(size)&abs(size-1)<1e-9&
    !is.na(sid)&nzchar(sid)&!is.na(sub)&nzchar(sub)&
    forest_plot(d$nlcdClass)&!is.na(d$date)
}
build_plot_year <- function(b,p) {
  b<-b[valid_beetle(b),,drop=FALSE]
  p<-p[valid_plant(p),,drop=FALSE]
  b$join<-paste(b$siteID,b$plotID,b$year,sep="|")
  p$join<-paste(p$siteID,p$plotID,p$year,sep="|")
  keys<-intersect(unique(b$join),unique(p$join))
  sb<-split(seq_len(nrow(b)),b$join)
  sp<-split(seq_len(nrow(p)),p$join)
  cohorts<-list()
  ndate<-0L;nbase<-0L
  for(k in keys) {
    bb<-b[sb[[k]],,drop=FALSE]; pp<-p[sp[[k]],,drop=FALSE]
    plant_first<-min(pp$date)
    p0<-pp[abs(as.numeric(pp$date-plant_first))<=7,,drop=FALSE]
    b0<-bb[abs(as.numeric(bb$date-plant_first))<=30,,drop=FALSE]
    # Prevent same sampleID with disagreeing original trapping days.
    if(nrow(b0)) {
      dup<-split(as.numeric(as.character(b0$trappingDays)),b0$unique_sample_id)
      if(any(vapply(dup,function(x)length(unique(x))>1,logical(1))))
        stop("SCIENTIFIC_STOP_CONTRADICTORY_ORIGINAL_TRAP_SAMPLE_EFFORT")
    }
    n0<-length(unique(as.character(b0$unique_sample_id)))
    p0count<-length(unique(as.character(p0$subplotID)))
    if(n0>0 && p0count>0)ndate<-ndate+1L
    if(n0<4 || p0count<4)next
    eff<-sum(vapply(split(as.numeric(as.character(b0$trappingDays)),b0$unique_sample_id),
       function(x)x[1],numeric(1)))
    parts<-strsplit(k,"|",fixed=TRUE)[[1]]
    if(length(parts)!=3)stop("SCIENTIFIC_STOP_NEON_ORIGINAL_PLOT_KEY_PARSE")
    cohorts[[k]]<-list(site=parts[1],plot=parts[2],year=as.integer(parts[3]),
      day_of_year=as.integer(format(plant_first,"%j")),
      beetle_effort_days=eff,beetle_samples=n0,plant_1m2_recorded_subplots=p0count,
      b_source_rows=unique(b0$.source_row),p_source_rows=unique(p0$.source_row))
    nbase<-nbase+1L
  }
  list(cohorts=cohorts,raw_spatial_source_plotyear_keys=length(keys),
       source_year_plot_keys_with_both_taxa_plant_season_30d=ndate,
       source_year_plot_keys_with_atleast4_unflagged_beetle_samples_and4_plant_1m2_subplots=nbase)
}
effort_ratio <- function(a,b) {
  if(!is.finite(a)||!is.finite(b)||a<=0||b<=0)return(FALSE)
  a/b>=.5&&a/b<=2
}
build_transitions <- function(cohorts,official) {
  keys<-names(cohorts)
  original_by_plot<-split(keys,vapply(cohorts,function(z)paste(z$site,z$plot,sep="|"),character(1)))
  pairs<-list()
  reason<-c(effort=0L,phenology=0L)
  for(pk in names(original_by_plot)) {
    ks<-original_by_plot[[pk]]
    years<-vapply(cohorts[ks],function(z)z$year,integer(1))
    for(y in sort(unique(years))) {
      if(!(y+1L%in%years))next
      k1<-ks[which(years==y)][1]
      k2<-ks[which(years==y+1L)][1]
      a<-cohorts[[k1]];b<-cohorts[[k2]]
      if(abs(a$day_of_year-b$day_of_year)>45) {
        reason["phenology"]<-reason["phenology"]+1L;next
      }
      if(!(effort_ratio(a$beetle_effort_days,b$beetle_effort_days) &&
            effort_ratio(a$plant_1m2_recorded_subplots,b$plant_1m2_recorded_subplots))) {
        reason["effort"]<-reason["effort"]+1L;next
      }
      pairs[[paste(pk,y,sep="|")]]<-list(site=a$site,year=y,
                                         plot=a$plot,k1=k1,k2=k2)
    }
  }
  blocks<-split(names(pairs),vapply(pairs,function(x)paste(x$site,x$year,sep="|"),character(1)))
  blocks<-Filter(function(z)length(z)>=3,blocks)
  sites<-unique(vapply(lapply(blocks,function(k)pairs[[k[1]]]),function(z)z$site,character(1)))
  source_id<-as.character(official$site_id)
  domain_count<-length(unique(official$domain_id[match(sites,source_id)]))
  site_year_by_site<-split(vapply(blocks,function(ks)pairs[[ks[1]]]$year,integer(1)),
    vapply(blocks,function(ks)pairs[[ks[1]]]$site,character(1)))
  corr_potential<-sum(vapply(site_year_by_site,function(v)length(unique(v))>=3,logical(1)))
  pass<-length(sites)>=6&&domain_count>=4&&length(blocks)>=16&&corr_potential>=5
  list(pairs=pairs,blocks=blocks,sites=sites,domains=domain_count,
    eligible_plot_annual_transitions=sum(lengths(blocks)),
    eligible_site_calendar_transitions=length(blocks),
    source_site_count=length(sites),
    sites_with_3plus_annual_transitions=corr_potential,
    pre_taxon_gate_pass=pass,
    excluded_plotyear_pairs_by_source_only_effort_or_DOY=as.list(reason))
}
beta_sim <- function(a,b) {
  if(!length(a)||!length(b))return(NA_real_)
  overlap<-length(intersect(a,b))
  u<-min(length(setdiff(a,b)),length(setdiff(b,a)))
  if(overlap+u==0)return(NA_real_)
  u/(overlap+u)
}
fixed_species_set <- function(tax,rank,value=NULL, plant=FALSE) {
  tax<-as.character(tax);r<-tolower(as.character(rank))
  ok<-!is.na(tax)&nzchar(tax)&!is.na(r)&
      r%in%c("species","subspecies","variety")
  if(!plant) {
    v<-suppressWarnings(as.numeric(as.character(value)))
    ok<-ok&is.finite(v)&v>0
  }
  unique(tax[ok])
}
source_site_bootstrap <- function(v,B=4000,P=9999,seed=20261112){
  if(length(v)<5) return(list(status="SCIENTIFIC_STOP_FEWER_THAN_FIVE_SITE_CORRELATIONS",
                              site_count=length(v)))
  set.seed(seed)
  observed<-mean(v)
  boot<-replicate(B,mean(sample(v,length(v),replace=TRUE)))
  list(status="MULTISITE_EXPLORATORY_WITHIN_SITE_CORRELATION",
       original_NEON_forest_site_count=length(v),
       site_correlations_positive=sum(v>0),
       site_correlations_negative=sum(v<0),
       site_equal_mean_pearson_temporal_alignment=observed,
       site_bootstrap_95CI=unname(as.numeric(quantile(boot,c(.025,.975)))),
       bootstrap_reps=B,
       permutation_reps=P)
}
fit_alignment <- function(frame,P=9999,seed=20261112){
  # Site frames have >=3 calendar-year transitions; within-site means and
  # variances are fixed, null permutes only the plant annual contrast labels.
  bysite<-split(frame,frame$site)
  valid<-Filter(function(d)nrow(d)>=3 &&
    sd(d$beetle_beta)>0&&sd(d$plant_beta)>0,bysite)
  if(length(valid)<5)return(list(status="SCIENTIFIC_STOP_5_INDEPENDENT_SITE_ALIGNMENT_NOT_ESTIMABLE",
                                source_scored_sites=length(valid)))
  cors<-vapply(valid,function(d)cor(d$beetle_beta,d$plant_beta),numeric(1))
  inf<-source_site_bootstrap(cors,P=P,seed=seed)
  set.seed(seed+1)
  null<-replicate(P,mean(vapply(valid,function(d)
    cor(d$beetle_beta,sample(d$plant_beta,length(d$plant_beta))),
    numeric(1))))
  obs<-mean(cors)
  inf$site_year_transition_scores_used<-sum(vapply(valid,nrow,integer(1)))
  inf$temporal_alignment_permutation_two_sided_p<-
    (1+sum(abs(null)>=abs(obs)-1e-12))/(P+1)
  inf$site_mean_beetle_temporal_beta<-mean(vapply(valid,function(d)mean(d$beetle_beta),numeric(1)))
  inf$site_mean_plant_temporal_beta<-mean(vapply(valid,function(d)mean(d$plant_beta),numeric(1)))
  inf$site_leave_one_out_alignment_range<-range(vapply(seq_along(cors),
             function(i)mean(cors[-i]),numeric(1)))
  inf$taxon_data_from_published_derivative_not_new_field_collection<-TRUE
  inf$no_canopy_vertical_causality_or_true_extinction_claim<-TRUE
  inf
}
synthetic <- function(){
  stopifnot(beta_sim(c("A","B","C"),c("A","B","D"))==1/3,
            beta_sim(c("A","B","C"),c("D","E","F"))==1,
            beta_sim(c("A"),c("A"))==0,
            is.na(beta_sim(character(),c("A"))))
  z<-fixed_species_set(c("S","G","Z"),c("species","genus","species"),c(1,2,0))
  stopifnot(identical(z,"S"))
  stopifnot(identical(fixed_species_set(c("S","Z"),c("species","species"),
              value=c(NA,NA),plant=TRUE),c("S","Z")))
  stopifnot(effort_ratio(10,20),!effort_ratio(10,25))
  # Known positive annual synchrony within each site; treatment/plot
  # identity is not present in the returned inference object.
  z<-do.call(rbind,lapply(1:6,function(site) {
    data.frame(site=paste0("SECRET_SITE",site),year=2019:2022,
      beetle_beta=c(.1,.7,.2,.8),
      plant_beta=c(.15,.65,.25,.75))
  }))
  inf<-fit_alignment(z,P=199)
  stopifnot(inf$status=="MULTISITE_EXPLORATORY_WITHIN_SITE_CORRELATION",
            inf$site_equal_mean_pearson_temporal_alignment>.9,
            inf$site_correlations_positive==6,
            !grepl("SECRET_SITE",paste(capture.output(str(inf)),collapse=" ")))
  cat("NEON SYNTHETIC PASS: within-site year alignment, true beta=0/1/1/3, source effort and no identifiers\n")
}
if(identical(Sys.getenv("NEON_CROSS_TAXON_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=2)stop("usage: Rscript neon_forest_cross_taxon_temporal_alignment.R OUT OFFICIAL_NEON_20260805_CSV")
synthetic()
dir.create(args[1],recursive=TRUE,showWarnings=FALSE)
official<-utils::read.csv(args[2],stringsAsFactors=FALSE,check.names=FALSE)
beetles<-neonDivData::data_beetle
plants<-neonDivData::data_plant
source<-select_metadata(beetles,plants,official)
c0<-build_plot_year(source$beetle,source$plant)
# Previous source-only minimum (>=1) cohort 339 based on unflagged source:
if(c0$raw_spatial_source_plotyear_keys<339)
  stop("SCIENTIFIC_STOP_PREVIOUSLY_FROZEN_STRICT_SOURCE_PLOT_UNIVERSE_SHRUNK")
c1<-build_transitions(c0$cohorts,official)
report<-list(
 schema="structural.NEON_forest_8site_temporal_taxon_alignment_exploratory.v1",
 source_public_package="neonDivData 0.3.1 (NEON-derived, independently published)",
 original_official_site_metadata="NEON_20260805",
 original_source_forests_NLCD_site_context=8,
 original_source_domains_before_effort=7,
 source_original_2019_2023_metadata_plot_years=c0$raw_spatial_source_plotyear_keys,
 source_original_metadata_plot_years_with_4beetle4plant_effort=length(c0$cohorts),
 source_plot_years_with_plant_first_survey_beetle_within30d=c0$source_year_plot_keys_with_both_taxa_plant_season_30d,
 source_plot_years_4_beetle_trap_samples_and_4_observed_plant_1m2_subplots=c0$source_year_plot_keys_with_atleast4_unflagged_beetle_samples_and4_plant_1m2_subplots,
 source_plots_with_valid_annual_4sample_both_groups_after_season_effort=c1$eligible_plot_annual_transitions,
 source_site_year_transitions_with_3plus_same_plots=c1$eligible_site_calendar_transitions,
 source_sites_after_fixed_effort_before_taxon=c1$source_site_count,
 source_domains_after_fixed_effort_before_taxon=c1$domains,
 source_sites_with_3plus_year_transition_groups_before_taxon=c1$sites_with_3plus_annual_transitions,
 source_only_gate_passed=c1$pre_taxon_gate_pass,
 source_only_excluded_transition_reasons=c1$excluded_plotyear_pairs_by_source_only_effort_or_DOY,
 plant_1m2_zero_species_samples_removed_in_published_derivative=TRUE,
 source_biology_taxon_or_values_read=FALSE,
 no_individual_source_site_plot_taxon_coordinates_reexported=TRUE,
 source_data_no_global_or_3D_forest_causality=TRUE,
 no_true_extinction_colonization_or_zero_survey_denominator_claim=TRUE,
 primary_39study_PREDICTS_result_left_frozen=TRUE,
 eBird_used=FALSE)
if(!c1$pre_taxon_gate_pass) {
  report$status="SCIENTIFIC_STOP_SAME_PLOT_EFFORT_TEMPORAL_SUPPORT"
} else {
  # Taxon value access begins ONLY here, after immutable metadata gate.
  for(k in names(c0$cohorts)){
    co<-c0$cohorts[[k]]
    bi<-co$b_source_rows;pi<-co$p_source_rows
    co$beetle_taxa<-fixed_species_set(beetles$taxon_id[bi],
             beetles$taxon_rank[bi],beetles$value[bi],plant=FALSE)
    co$plant_taxa<-fixed_species_set(plants$taxon_id[pi],
             plants$taxon_rank[pi],plant=TRUE)
    c0$cohorts[[k]]<-co
  }
  report$source_biology_taxon_or_values_read=TRUE
  records<-list()
  unscoreable<-0L
  for(ky in names(c1$blocks)){
    ps<-c1$blocks[[ky]]
    scores<-lapply(ps,function(z){
      pair<-c1$pairs[[z]]
      a<-c0$cohorts[[pair$k1]];b<-c0$cohorts[[pair$k2]]
      v1<-beta_sim(a$beetle_taxa,b$beetle_taxa)
      v2<-beta_sim(a$plant_taxa,b$plant_taxa)
      if(!is.finite(v1)||!is.finite(v2))return(NULL)
      c(v1,v2)
    })
    scores<-Filter(Negate(is.null),scores)
    if(length(scores)<3){unscoreable<-unscoreable+1L;next}
    m<-do.call(rbind,scores)
    root<-c1$pairs[[ps[1]]]
    records[[ky]]<-data.frame(site=root$site,year=root$year,
      beetle_beta=mean(m[,1]),plant_beta=mean(m[,2]),n_original_plots=nrow(m))
  }
  frame<-if(length(records))do.call(rbind,records) else data.frame()
  report$source_site_annual_transitions_scored_both_taxa<-nrow(frame)
  report$source_site_year_transition_groups_unscoreable_taxa<-unscoreable
  report$source_plot_transition_beta_pairs_fully_scored<-if(nrow(frame))sum(frame$n_original_plots) else 0
  if(!nrow(frame))report$status="SCIENTIFIC_STOP_NO_DEFINED_CROSS_TAXON_ANNUAL_BETA"
  else {
    fit<-fit_alignment(frame)
    report$exploratory_temporal_alignment_inference<-fit
    report$status<-fit$status
  }
}
writeLines(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),
           file.path(args[1],"NEON_cross_taxon_8forest_temporal_alignment_aggregate.json"))
cat(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
