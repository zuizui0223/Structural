#!/usr/bin/env Rscript
# ONE-SHOT after the published, taxon-unopened 26-site original source cohort:
# 2019-2020 forest ground-beetle Simpson replacement vs STATIC CHMv2 40m
# canopy height difference with site intercept and log plot distance.
# Site-level bootstrap, within-site PLOT LABEL canopy permutations only.
# All original source IDs/taxa/values/coords stay inside Actions runner;
# output is anonymous study-aggregate only, regardless of positive/null/STOP.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))
SOURCE_YEAR<-2019:2020
META_COLUMNS_B<-c("siteID","plotID","observation_datetime","nlcdClass",
   "trappingDays","trapConditionFlag","unique_sample_id","trapID")
META_COLUMNS_P<-c("siteID","plotID","observation_datetime","nlcdClass",
   "sample_area_m2","unique_sample_id","subplotID")
BIO_COLUMNS_B<-c("taxon_id","taxon_rank","value")
source_date<-function(x)suppressWarnings(as.Date(substr(as.character(x),1,10)))
source_year<-function(x){
 y<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
 y[!(y%in%SOURCE_YEAR)]<-NA_integer_;y
}
valid<-function(x)!is.na(x)&nzchar(trimws(as.character(x)))
isforest<-function(x) {
 x<-tolower(gsub("[[:space:]_/-]+","",as.character(x)))
 x[is.na(x)]<-"";x%in%c("deciduousforest","evergreenforest","mixedforest")
}
source_beta_sim<-function(a,b){
 if(!length(a)||!length(b))return(NA_real_)
 overlap<-length(intersect(a,b))
 uncommon<-min(length(setdiff(a,b)),length(setdiff(b,a)))
 if(overlap+uncommon==0)return(NA_real_)
 uncommon/(overlap+uncommon)
}
recorded_beetle_taxa<-function(d){
 ranks<-tolower(trimws(as.character(d$taxon_rank)))
 v<-suppressWarnings(as.numeric(as.character(d$value)))
 ids<-as.character(d$taxon_id)
 ok<-valid(ids)&ranks%in%c("species","subspecies","variety")&
   is.finite(v)&v>0
 unique(ids[ok])
}
distance_km<-function(lat_a,lon_a,lat_b,lon_b){
 p1<-lat_a*pi/180;p2<-lat_b*pi/180
 dlat<-(lat_b-lat_a)*pi/180;dlon<-(lon_b-lon_a)*pi/180
 h<-sin(dlat/2)^2+cos(p1)*cos(p2)*sin(dlon/2)^2
 6371.0088*2*asin(min(1,sqrt(h)))
}
source_pair_stats<-function(y,h,d){
 # Equal weight per SITE, not per pair; residualize fixed site intercept by
 # centering pairs BEFORE aggregating sufficient statistics.
 n<-length(y)
 if(n<3||any(!is.finite(c(y,h,d))))return(NULL)
 yc<-y-mean(y);hc<-h-mean(h);dc<-d-mean(d)
 c(Shh=mean(hc^2),Sdd=mean(dc^2),Shd=mean(hc*dc),
   Shy=mean(hc*yc),Sdy=mean(dc*yc),
   mean_beta=mean(y),mean_height_delta10=mean(h),
   mean_logdist=mean(d),n_pairs=n)
}
source_partial_slope<-function(stats){
 if(is.null(stats)||!nrow(stats))return(NA_real_)
 x<-colSums(stats[,c("Shh","Sdd","Shd","Shy","Sdy"),drop=FALSE])
 if(!is.finite(x[["Sdd"]])||x[["Sdd"]]<=1e-10)return(NA_real_)
 rem<-x[["Shh"]]-x[["Shd"]]^2/x[["Sdd"]]
 if(!is.finite(rem)||rem<=1e-10)return(NA_real_)
 (x[["Shy"]]-x[["Shd"]]*x[["Sdy"]]/x[["Sdd"]])/rem
}
source_sampled_taxa<-function(beetle,plant,cohort){
 if(!all(c(META_COLUMNS_B,BIO_COLUMNS_B)%in%names(beetle))||
    !all(META_COLUMNS_P%in%names(plant)))
    stop("SCIENTIFIC_STOP_NEON_ORGANISMAL_META_OR_TAXON_SOURCE_SCHEMA")
 b<-beetle[,c(META_COLUMNS_B,BIO_COLUMNS_B),drop=FALSE]
 p<-plant[,META_COLUMNS_P,drop=FALSE]
 k<-function(d)paste(d$siteID,d$plotID,source_year(d$observation_datetime),sep="|")
 selected<-unique(paste(cohort$siteID,cohort$plotID,cohort$year,sep="|"))
 bkey<-k(b);pkey<-k(p)
 b<-b[bkey%in%selected,,drop=FALSE];p<-p[pkey%in%selected,,drop=FALSE]
 bkey<-bkey[bkey%in%selected];pkey<-pkey[pkey%in%selected]
 bi<-split(seq_len(nrow(b)),bkey)
 pi<-split(seq_len(nrow(p)),pkey)
 result<-list();source_disagreement<-0L
 for(i in seq_len(nrow(cohort))){
    row<-cohort[i,,drop=FALSE]
    key<-paste(row$siteID,row$plotID,row$year,sep="|")
    if(!(key%in%names(bi)&&key%in%names(pi)))
      stop("SCIENTIFIC_STOP_ORIGINAL_SELECTED_SOURCE_PLOT_RECORDS_GONE")
    bb<-b[bi[[key]],,drop=FALSE];pp<-p[pi[[key]],,drop=FALSE]
    date<-as.Date(row$first_plant_survey_date)
    pd<-source_date(pp$observation_datetime)
    area<-suppressWarnings(as.numeric(as.character(pp$sample_area_m2)))
    pg<-isforest(pp$nlcdClass)&is.finite(area)&abs(area-1)<1e-9&
      valid(pp$unique_sample_id)&valid(pp$subplotID)&!is.na(pd)&
      abs(as.numeric(pd-date))<=7
    plant<-pp[pg,,drop=FALSE]
    bd<-source_date(bb$observation_datetime)
    tr<-suppressWarnings(as.numeric(as.character(bb$trappingDays)))
    flag<-as.character(bb$trapConditionFlag)
    bg<-isforest(bb$nlcdClass)&is.finite(tr)&tr>0&
      valid(bb$unique_sample_id)&valid(bb$trapID)&
      (is.na(flag)|!nzchar(trimws(flag)))&!is.na(bd)&
      abs(as.numeric(bd-date))<=30
    beetle<-bb[bg,,drop=FALSE]
    ids<-as.character(beetle$unique_sample_id)
    effort<-split(suppressWarnings(as.numeric(as.character(beetle$trappingDays))),ids)
    if(any(vapply(effort,function(z)length(unique(z))!=1,logical(1))))
      stop("SCIENTIFIC_STOP_ORIGINAL_SELECTED_TRAP_SOURCE_EFFORT_CONFLICT")
    total_days<-sum(vapply(effort,function(z)z[1],numeric(1)))
    nplant<-length(unique(as.character(plant$subplotID)))
    if(length(effort)!=row$source_beetle_normal_samples ||
       abs(total_days-row$source_beetle_total_trapdays)>1e-7 ||
       nplant!=row$source_plant_recorded_1m2_subplots ||
       length(effort)<4||nplant<4)
      stop("SCIENTIFIC_STOP_ORIGINAL_PREOUTCOME_SOURCE_EFFORT_COHORT_CHANGED")
    # The fixed source sampling mask is COMPLETE. Open ONLY beetle taxon
    # rank and positive value at this point; taxon zero excludes whole site.
    result[[key]]<-recorded_beetle_taxa(beetle)
 }
 result
}
make_site_pairs<-function(siteplot,taxa){
 if(length(unique(siteplot$year))!=1||length(unique(siteplot$siteID))!=1)
   stop("SCIENTIFIC_STOP_ORIGINAL_SITE_ONE_YEAR_PER_SITE_SOURCE_SELECTION")
 if(nrow(siteplot)<3)return(NULL)
 sourcekeys<-paste(siteplot$siteID,siteplot$plotID,siteplot$year,sep="|")
 if(any(!sourcekeys%in%names(taxa)))return(NULL)
 sub<-taxa[sourcekeys]
 if(any(lengths(sub)==0))return(NULL)  # do not select favorable subsets
 ix<-combn(seq_len(nrow(siteplot)),2)
 ys<-numeric(ncol(ix));hs<-ys;ds<-ys
 for(j in seq_len(ncol(ix))){
    a<-ix[1,j];b<-ix[2,j]
    ys[j]<-source_beta_sim(sub[[a]],sub[[b]])
    hs[j]<-abs(siteplot$CHMv2_40m_static_p90_m[a]-
                 siteplot$CHMv2_40m_static_p90_m[b])/10
    d<-distance_km(siteplot$original_baseplot_lat[a],
         siteplot$original_baseplot_lon[a],
         siteplot$original_baseplot_lat[b],
         siteplot$original_baseplot_lon[b])
    ds[j]<-log(d+.05)
 }
 if(any(!is.finite(ys))||any(!is.finite(hs))||any(!is.finite(ds)))
   return(NULL)
 list(y=ys,h=hs,d=ds,plot_i=ix[1,],plot_j=ix[2,],
   source_plot_CHM_p90_m=as.numeric(siteplot$CHMv2_40m_static_p90_m),
   plot_source_taxa_counts=lengths(sub),site=as.character(siteplot$siteID[1]),
   source_year=as.integer(siteplot$year[1]))
}
infer_fixed_site_effects<-function(groups,B=4000,P=9999,seed=20261114) {
 if(length(groups)<12)return(list(status="SCIENTIFIC_STOP_FEWER_THAN_TWELVE_SOURCE_SITE_YEAR_GROUPS",
   source_sites=length(groups)))
 stats<-do.call(rbind,lapply(groups,function(g)source_pair_stats(g$y,g$h,g$d)))
 if(any(!is.finite(stats)))return(list(status="SCIENTIFIC_STOP_UNDEFINED_ORIGINAL_SITE_STATS"))
 observed<-source_partial_slope(stats)
 if(!is.finite(observed))return(list(status="SCIENTIFIC_STOP_CHM_HEIGHT_DIFFERENCE_NOT_DISTANCE_IDENTIFIABLE"))
 set.seed(seed)
 boots<-replicate(B,{
   ix<-sample(seq_len(nrow(stats)),nrow(stats),replace=TRUE)
   source_partial_slope(stats[ix,,drop=FALSE])
 })
 valid_boot<-boots[is.finite(boots)]
 if(length(valid_boot)<.95*B)
   return(list(status="SCIENTIFIC_STOP_SOURCE_SITE_BOOTSTRAP_UNDEFINED",
     bootstrap_valid=length(valid_boot)))
 # Plot canopy-height labels are permuted within each original source SITE.
 # Community response and pair geography remain fixed. Pairs are NOT
 # independently shuffled, which would create pseudoreplication.
 set.seed(seed+1L)
 null<-replicate(P,{
   permstats<-do.call(rbind,lapply(groups,function(g){
     h0<-sample(g$source_plot_CHM_p90_m,length(g$source_plot_CHM_p90_m))
     source_pair_stats(g$y,abs(h0[g$plot_i]-h0[g$plot_j])/10,g$d)
   }))
   source_partial_slope(permstats)
 })
 validnull<-null[is.finite(null)]
 if(length(validnull)<.95*P)
   return(list(status="SCIENTIFIC_STOP_PLOT_LABEL_PERMUTATIONS_UNIDENTIFIABLE",
      valid_permutation_count=length(validnull)))
 medbeta<-median(unlist(lapply(groups,function(g)g$y),use.names=FALSE))
 original_sites<-length(groups)
 list(
    status="EXPLORATORY_NEON_FOREST_SITE_EQUAL_BEETLE_SPATIAL_SIMSPON_REPLACEMENT_CHM_HEIGHT_SLOPE",
    original_independent_NEON_sites=original_sites,
    original_site_year_groups_one_per_site=original_sites,
    original_pairs_NOT_INDEPENDENT=sum(vapply(groups,function(g)length(g$y),integer(1))),
    original_distinct_plots_in_selected_source_cliques=sum(vapply(groups,function(g)length(g$source_plot_CHM_p90_m),integer(1))),
    observed_site_equal_partial_beta_sim_slope_per_10m_absolute_CHMv2_height_difference=observed,
    site_block_bootstrap_95_percentile_CI=unname(as.numeric(quantile(valid_boot,c(.025,.975)))),
    within_original_site_plot_CHM_label_permutations=P,
    two_sided_within_site_original_plot_label_permutation_p=(1+sum(abs(validnull)>=abs(observed)-1e-12))/(length(validnull)+1),
    original_site_bootstrap_B=B,
    observed_mean_site_equal_Simpson_replacement=mean(vapply(groups,function(g)mean(g$y),numeric(1))),
    observed_median_pairwise_Simpson_replacement_NONINDEPENDENT=medbeta,
    source_site_plot_pairwise_beta_not_an_independent_forest_replicate=TRUE,
    after_distance_site_intercept_effect_not_causal_landuse_effect=TRUE,
    original_NEON_2019_2020_static_CHMv2_not_pixel_year_verified=TRUE
 )
}
synthetic<-function(){
 stopifnot(source_beta_sim(c("A","B","C"),c("A","B","D"))==1/3,
           source_beta_sim(c("A","B","C"),c("D","E","F"))==1,
           source_beta_sim(c("A"),c("A"))==0,
           is.na(source_beta_sim(c("A"),character())))
 stopifnot(identical(recorded_beetle_taxa(data.frame(taxon_id=c("S","G","Z"),
     taxon_rank=c("species","genus","species"),value=c(1,2,0))),"S"))
 sets<-lapply(seq_len(12),function(i){
    h<-c(10,14,20,27)+i*.1
    pairs<-combn(1:4,2)
    dh<-abs(h[pairs[1,]]-h[pairs[2,]])/10
    d<-log(c(.12,.17,.32,.21,.42,.47)+.05)
    y<-.20+.18*dh+.025*d+seq_len(6)*.001
    list(y=y,h=dh,d=d,plot_i=pairs[1,],plot_j=pairs[2,],
      source_plot_CHM_p90_m=h,site=paste0("PRIVATE_SITE",i),
      source_year=2020)
 })
 result<-infer_fixed_site_effects(sets,B=199,P=199)
 stopifnot(result$status==
    "EXPLORATORY_NEON_FOREST_SITE_EQUAL_BEETLE_SPATIAL_SIMSPON_REPLACEMENT_CHM_HEIGHT_SLOPE",
    result$observed_site_equal_partial_beta_sim_slope_per_10m_absolute_CHMv2_height_difference>0,
    result$original_independent_NEON_sites==12,
    !grepl("PRIVATE_SITE",paste(capture.output(str(result)),collapse=" ")))
 cat("BEETLE CHM BIOLOGICAL KNOWN TRUTH: source Simpson beta, site+distance partial slope, site bootstrap, plot-label permutation PASS\n")
}
if(identical(Sys.getenv("NEON_CHM_BEETLE_SYNTHETIC_ONLY"),"1")){
 synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=3)stop("usage: Rscript neon_chmv2_2019_2020_beetle_spatial_beta_onepass.R PRIVATE_26SITE_SOURCE_CLIQUES_CSV OFFICIAL_NEON_SITE_CSV AGGREGATE_OUT")
synthetic()
source<-read.csv(args[1],stringsAsFactors=FALSE)
official<-read.csv(args[2],stringsAsFactors=FALSE)
require_fields<-c("siteID","plotID","year","first_plant_survey_date",
  "source_beetle_total_trapdays","source_plant_recorded_1m2_subplots",
  "source_beetle_normal_samples","CHMv2_40m_static_p90_m",
  "original_baseplot_lat","original_baseplot_lon")
if(!all(require_fields%in%names(source))||nrow(official)!=81||
   !all(c("site_id","domain_id")%in%names(official)))
  stop("SCIENTIFIC_STOP_PREOUTCOME_SELECTED_FOREST_PLOT_META_SCHEMA")
site_count<-length(unique(source$siteID))
if(site_count!=26 || anyDuplicated(paste(source$siteID,source$plotID,source$year,sep="|")) ||
   any(table(source$siteID)<3))
  stop("STOP_FROZEN_26SOURCE_SITES_ORIGINAL_PLOT_CLIQUES_DRIFT")
by_site<-split(source,source$siteID)
if(any(vapply(by_site,function(d)length(unique(d$year))!=1,logical(1))))
  stop("STOP_ORIGINAL_SITE_MUST_HAVE_ONE_FROZEN_YEAR")
domains<-official$domain_id[match(names(by_site),official$site_id)]
if(anyNA(domains)||length(unique(domains))!=15)
  stop("STOP_FROZEN_15DOMAIN_SOURCE_TRIAD_SCOPE_DRIFT")
# The only response-opening point, after the source frame and effort
# identity have already been fixed.
sets<-source_sampled_taxa(neonDivData::data_beetle,neonDivData::data_plant,source)
pairs<-lapply(by_site,make_site_pairs,taxa=sets)
okay<-!vapply(pairs,is.null,logical(1))
groups<-pairs[okay]
source_good_domains<-length(unique(domains[okay]))
source_excluded_sites<-sum(!okay)
source_scoreable<-length(groups)
report<-list(
 schema="structural.NEON_CHMv2_2019_2020_beetle_spatial_replacement_single_endpoint.v1",
 original_source_CHMv2_2019_2020_26site_15domain_44siteyear_design_passed_before_species_values=TRUE,
 source_original_one_preselected_2020preferred_or_2019_year_per_site=TRUE,
 original_neon_source_26independent_site_cliques_before_taxonomy=site_count,
 original_neon_source_domains_before_taxonomy=length(unique(domains)),
 original_sites_excluded_whole_clique_for_beetle_taxon_not_defined=source_excluded_sites,
 original_sites_with_defined_beetle_species_rank_incidence_and_pairwise_beta=source_scoreable,
 original_domains_with_defined_beetle_beta=source_good_domains,
 original_selected_source_plot_count=sum(vapply(by_site,nrow,integer(1))),
 original_taxon_value_source_rank_filter="taxon_rank species/subspecies/variety; original value>0; original taxon_id valid; original normal trap +/-30d",
 source_tree_height_not_annual_NEON_AOP_LiDAR=TRUE,
 prior_PREDICTS_39study_beta0p0942_and_31study_sensitivity_beta0p0847_unchanged=TRUE,
 prior_NEON_7site_temporal_beta_alignment_negative0p0664_p0p536_unchanged=TRUE,
 no_original_site_plot_taxon_name_ID_species_abundance_or_coordinates_exported=TRUE,
 no_plant_species_beta_secondary_or_chem_ecosystem_services_scored=TRUE,
 previous_vst_original_12siteyear_effort_scientific_STOP_unchanged=TRUE,
 original_beetle_source_taxon_outcomes_read_once_after_precommitted_source_gate=TRUE,
 eBird_used=FALSE
)
if(source_scoreable<12||source_good_domains<6){
 report$status<-"SCIENTIFIC_STOP_TAXON_DETECTION_SITE_SUPPORT"
} else {
 inference<-infer_fixed_site_effects(groups,B=4000,P=9999)
 report$status<-inference$status
 report$primary_exploratory_beetle_site_equal_inference<-inference
}
dir.create(args[3],recursive=TRUE,showWarnings=FALSE)
path<-file.path(args[3],"NEON_2019_2020_CHMv2_static_canopy_beetle_spatial_beta_original_aggregate.json")
writeLines(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),path)
cat(jsonlite::toJSON(report,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
