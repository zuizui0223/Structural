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
      if(!((y+1L) %in% years))next
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
  # Regression test for 2023 boundary. In R, the special %in% operator
  # has higher precedence than +; explicit (year+1L) is mandatory.
  mini<-list()
  for(yy in 2019:2023){
    id<-paste("SECRET_SITE","SECRET_PLOT",yy,sep="|")
    mini[[id]]<-list(site="SECRET_SITE",plot="SECRET_PLOT",
       year=as.integer(yy),day_of_year=170,
       beetle_effort_days=14,plant_1m2_recorded_subplots=8)
  }
  at<-build_transitions(mini,
      data.frame(site_id="SECRET_SITE",domain_id="D01"))
  stopifnot(length(at$pairs)==4,
            all(vapply(at$pairs,function(z)z$year,integer(1))%in%2019:2022),
            !at$pre_taxon_gate_pass)
  cat("NEON SYNTHETIC PASS: within-site year alignment, true beta=0/1/1/3, source effort and no identifiers\n")
}

# V2 IS A DISTINCT ESTIMAND. V1 required >=5 sitewise correlations from
# sites with >=3 time transitions and stopped at 4. V2 treats sites as blocks
# in one pooled site-centered temporal covariance (>=2 yr transitions).
site_equal_within_correlation <- function(site_frames) {
  components<-lapply(site_frames,function(z) {
    if(nrow(z)<2)return(NULL)
    bb<-z$beetle_beta-mean(z$beetle_beta)
    pp<-z$plant_beta-mean(z$plant_beta)
    c(cov=mean(bb*pp),varb=mean(bb^2),varp=mean(pp^2))
  })
  components<-Filter(Negate(is.null),components)
  if(!length(components))return(NA_real_)
  q<-do.call(rbind,components)
  b<-mean(q[,"varb"]);p<-mean(q[,"varp"])
  if(!is.finite(b)||!is.finite(p)||b<=0||p<=0)return(NA_real_)
  mean(q[,"cov"])/sqrt(b*p)
}
fit_v2 <- function(df,sites,B=4000,P=9999,seed=20261112) {
  siteframes<-split(df,df$site)
  siteframes<-Filter(function(d)nrow(d)>=2,siteframes)
  domains<-length(unique(sites$domain_id[match(names(siteframes),sites$site_id)]))
  if(length(siteframes)<6||domains<4||sum(lengths(lapply(siteframes,function(d)d$year)))<16)
    return(list(status="SCIENTIFIC_STOP_V2_BIOLOGICAL_SITE_TIME_SUPPORT",
                scoreable_sites=length(siteframes),scoreable_domains=domains))
  ob<-site_equal_within_correlation(siteframes)
  if(!is.finite(ob))return(list(status="SCIENTIFIC_STOP_V2_POOLED_WITHIN_SITE_ZERO_VARIANCE",
                           scoreable_sites=length(siteframes)))
  set.seed(seed)
  bootstrap<-replicate(B,{
    ix<-sample(seq_along(siteframes),length(siteframes),replace=TRUE)
    site_equal_within_correlation(unname(siteframes[ix]))
  })
  bootstrap<-bootstrap[is.finite(bootstrap)]
  set.seed(seed+1)
  perm<-replicate(P,{
    shuf<-lapply(siteframes,function(d){
      d$plant_beta<-sample(d$plant_beta,length(d$plant_beta))
      d
    })
    site_equal_within_correlation(shuf)
  })
  perm<-perm[is.finite(perm)]
  if(length(bootstrap)<.95*B||length(perm)<.95*P)
    return(list(status="SCIENTIFIC_STOP_V2_NULL_OR_BOOTSTRAP_UNDEFINED",
                bootstrap_valid=length(bootstrap),null_valid=length(perm)))
  co<-vapply(siteframes,function(d)
    mean((d$beetle_beta-mean(d$beetle_beta))*
         (d$plant_beta-mean(d$plant_beta))),numeric(1))
  loo<-vapply(seq_along(siteframes),function(j){
     site_equal_within_correlation(siteframes[-j])
  },numeric(1))
  list(
    status="V2_EXPLORATORY_POOLED_SITE_DEMEANED_TEMPORAL_COHERENCE",
    independent_NEON_source_site_blocks=length(siteframes),
    independent_ecoclimatic_domains=domains,
    annual_site_transition_scores_NONINDEPENDENT=nrow(df),
    source_sites_positive_within_site_covariance=sum(co>0),
    source_sites_negative_within_site_covariance=sum(co<0),
    observed_site_equal_within_site_annual_beta_correlation=ob,
    site_block_4000bootstrap_95CI=unname(as.numeric(quantile(bootstrap,c(.025,.975)))),
    within_site_9999year_label_permutation_twosided_p=(1+sum(abs(perm)>=abs(ob)-1e-12))/(length(perm)+1),
    leave_one_source_site_out_correlation_range=unname(range(loo)),
    mean_site_equal_beetle_temporal_simpson_beta=mean(vapply(siteframes,function(d)mean(d$beetle_beta),numeric(1))),
    mean_site_equal_plant_recorded_temporal_simpson_beta=mean(vapply(siteframes,function(d)mean(d$plant_beta),numeric(1))),
    source_taxa_measurements_do_not_establish_true_absences_or_independent_plot_studies=TRUE,
    nsite_is_not_nplot=TRUE,
    no_canopy_structure_or_colonization_causality_claim=TRUE
  )
}
synthetic_v2 <- function(){
  # Four sites with >=3 transitions, four with two; valid pooled 8-site
  # coherence even though v1 cannot estimate 5 independent sitewise r.
  q<-do.call(rbind,lapply(1:8,function(i) {
     x<-if(i<=4)c(.2,.8,.4,.7) else c(.2,.8)
     data.frame(site=paste0("SECRET",i),
                year=2019+seq_along(x)-1,
                beetle_beta=x,plant_beta=x)
  }))
  forest<-data.frame(site_id=paste0("SECRET",1:8),
     domain_id=paste0("D",c(1:7,7)))
  z<-fit_v2(q,forest,B=99,P=199)
  stopifnot(z$status=="V2_EXPLORATORY_POOLED_SITE_DEMEANED_TEMPORAL_COHERENCE",
            z$independent_NEON_source_site_blocks==8,
            abs(z$observed_site_equal_within_site_annual_beta_correlation-1)<1e-10,
            z$source_sites_positive_within_site_covariance==8,
            !grepl("SECRET",paste(capture.output(str(z)),collapse=" ")))
  stopifnot(is.na(site_equal_within_correlation(list(
      data.frame(beetle_beta=c(.1,.1),plant_beta=c(.2,.6))))))
  cat("V2 synthetic pass: site-demeaned pooled covariance, n=2 site blocks and no original IDs\n")
}
if(identical(Sys.getenv("NEON_CROSS_TAXON_V2_SYNTHETIC_ONLY"),"1")){
  synthetic();synthetic_v2();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=2)stop("usage: Rscript neon_forest_cross_taxon_temporal_alignment_v2.R OUT OFFICIAL_SOURCE_CSV")
synthetic();synthetic_v2()
dir.create(args[1],recursive=TRUE,showWarnings=FALSE)
official<-utils::read.csv(args[2],stringsAsFactors=FALSE,check.names=FALSE)
beetles<-neonDivData::data_beetle
plants<-neonDivData::data_plant
source<-select_metadata(beetles,plants,official)
c0<-build_plot_year(source$beetle,source$plant)
if(c0$raw_spatial_source_plotyear_keys<339)
  stop("STOP_ORIGINAL_339_PLOTYEAR_SOURCE_DENOMINATOR_DRIFT")
c1<-build_transitions(c0$cohorts,official)
original_blocks<-c1$blocks
by_site<-split(names(original_blocks),vapply(original_blocks,function(k)
   c1$pairs[[k[1]]]$site,character(1)))
select_sites<-names(Filter(function(k)length(k)>=2,by_site))
candidate_blocks<-original_blocks[vapply(original_blocks,function(k)
   c1$pairs[[k[1]]]$site%in%select_sites,logical(1))]
original_domains<-length(unique(official$domain_id[match(select_sites,official$site_id)]))
v2metadata<-length(select_sites)>=6&&original_domains>=4&&length(candidate_blocks)>=16
report<-list(
 schema="structural.NEON_forest_cross_taxon_temporal_alignment_sourceadaptive_v2.v1",
 v1_scientific_STOP_NOT_OVERRIDDEN=TRUE,
 source_only_adaptation_to_distinct_site_centered_estimand=TRUE,
 published_neonDivData_version="0.3.1",
 official_NEON_site_metadata="2026-08-05",
 original_source_only_8forests_7domains_verified=TRUE,
 original_source_only_339plotyear_v2_metadata_gate_reused=TRUE,
 original_plotyear_keys_after_earliest_plant_date_4samples_4subplots=length(c0$cohorts),
 original_strict_siteyear_blocks_with_3plus_effort_matched_plots=length(original_blocks),
 original_strict_source_sites_with_2plus_annual_transitions=length(select_sites),
 original_strict_original_ecoclimatic_domains=original_domains,
 original_siteyear_transitions_after_v2_site_2plus_filter=length(candidate_blocks),
 source_only_v2_admission_passed=v2metadata,
 original_species_taxon_or_abundance_values_READ=FALSE,
 plant_1m2_empty_target_species_surveys_missing_from_public_derivative=TRUE,
 source_original_plot_site_taxon_sample_names_coordinates_NOT_EXPORTED=TRUE,
 forest_canopy_structure_temperature_effect_NOT_OBSERVED=TRUE,
 PREDICTS_39study_beta_and_31study_sensitivity_LEFT_FROZEN=TRUE,
 eBird_used=FALSE
)
if(!v2metadata)report$status="SCIENTIFIC_STOP_V2_SITE_BLOCK_SUPPORT"
else {
  included_keys<-unique(unlist(lapply(candidate_blocks,function(group)
    unlist(lapply(group,function(pk)c(c1$pairs[[pk]]$k1,c1$pairs[[pk]]$k2))))))
  for(k in included_keys){
    co<-c0$cohorts[[k]]
    bi<-co$b_source_rows;pi<-co$p_source_rows
    co$beetle_taxa<-fixed_species_set(beetles$taxon_id[bi],
              beetles$taxon_rank[bi],beetles$value[bi],plant=FALSE)
    co$plant_taxa<-fixed_species_set(plants$taxon_id[pi],
              plants$taxon_rank[pi],plant=TRUE)
    c0$cohorts[[k]]<-co
  }
  report$original_species_taxon_or_abundance_values_READ=TRUE
  records<-list();fails<-0L
  for(ky in names(candidate_blocks)){
    matched<-lapply(candidate_blocks[[ky]],function(pk){
      pr<-c1$pairs[[pk]]
      a<-c0$cohorts[[pr$k1]];b<-c0$cohorts[[pr$k2]]
      x<-beta_sim(a$beetle_taxa,b$beetle_taxa)
      y<-beta_sim(a$plant_taxa,b$plant_taxa)
      if(!is.finite(x)||!is.finite(y))return(NULL)
      c(x,y)
    })
    matched<-Filter(Negate(is.null),matched)
    if(length(matched)<3){fails<-fails+1L;next}
    m<-do.call(rbind,matched)
    x<-c1$pairs[[candidate_blocks[[ky]][1]]]
    records[[ky]]<-data.frame(site=x$site,year=x$year,
       beetle_beta=mean(m[,1]),plant_beta=mean(m[,2]),
       original_plot_contrasts_not_independent=nrow(m))
  }
  df<-if(length(records))do.call(rbind,records) else data.frame()
  report$siteyear_transitions_with_both_taxon_beta_defined<-nrow(df)
  report$siteyear_transitions_excluded_undefined_taxon_beta<-fails
  report$total_scored_plot_annual_contrasts_NOT_independent<-if(nrow(df))sum(df$original_plot_contrasts_not_independent) else 0
  if(!nrow(df))report$status="SCIENTIFIC_STOP_V2_NO_DEFINED_TAXON_TRANSITIONS"
  else{
    z<-fit_v2(df,official)
    report$v2_site_equal_temporal_coherence_inference<-z
    report$status<-z$status
  }
}
writeLines(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),
     file.path(args[1],"NEON_8forest_sourceadaptive_v2_site_centered_temporal_coherence.json"))
cat(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
