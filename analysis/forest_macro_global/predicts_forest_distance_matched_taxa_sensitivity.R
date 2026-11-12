#!/usr/bin/env Rscript
# One prespecified (after exposed primary result) PREDICTS geographic
# sensitivity. Study selection depends ONLY on original site coordinates,
# not on beta-diversity scores. Prior 39-study +0.0942 result SEALED.
# This second analysis is explicitly exploratory and NOT a new confirmation.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(predictsr))
norm <- function(x){
 a<-tolower(trimws(as.character(x)));a[is.na(a)]<-""
 gsub("[[:space:]]+"," ",a)
}
site_id <- function(d){
 if("SSBS" %in% names(d))return(as.character(d$SSBS))
 paste(as.character(d$Source_ID),as.character(d$Study_number),
       as.character(d$Block),as.character(d$Site_number),sep="|")
}
source_study <- function(d){
 if("SS" %in% names(d))return(as.character(d$SS))
 paste(as.character(d$Source_ID),as.character(d$Study_number),sep="|")
}
forest_scope <- function(d){
 req<-c("Source_ID","Study_number","Sampling_method","Study_common_taxon",
   "Biome","Habitat_as_described","Predominant_land_use","Use_intensity",
   "Country","Latitude","Longitude")
 if(!all(req %in% names(d)))stop("STOP_SOURCE_SITE_COLUMN_DRIFT")
 land<-norm(d$Predominant_land_use)
 strict<-grepl("forest|taiga|woodland",norm(d$Biome)) &
   grepl("forest|woodland|mangrove|laurel",norm(d$Habitat_as_described)) &
   grepl("^primary vegetation|^secondary vegetation|^plantation forest",land)
 ref<-strict & grepl("^primary vegetation",land) &
   grepl("minimal|light",norm(d$Use_intensity))
 alt<-strict & grepl("^secondary vegetation|^plantation forest",land)
 ids<-site_id(d)
 g<-paste(source_study(d),norm(d$Sampling_method),
          norm(d$Study_common_taxon),sep="|||")
 x<-data.frame(id=ids,study=source_study(d),group=g,
   reference=ref,altered=alt,
   lat=suppressWarnings(as.numeric(as.character(d$Latitude))),
   lon=suppressWarnings(as.numeric(as.character(d$Longitude))),
   stringsAsFactors=FALSE)
 x<-x[!duplicated(x$id)&strict,,drop=FALSE]
 keep<-vapply(split(x,x$group),function(z)
   sum(z$reference)>=2 && sum(z$altered)>=2,logical(1))
 x<-x[x$group %in% names(keep)[keep],,drop=FALSE]
 if(nrow(d)!=35738 || nrow(x)!=1145 ||
   length(unique(x$group))!=39 || length(unique(x$study))!=39)
   stop("STOP_PREVIOUS_39_SOURCE_STUDY_SCOPE_CHANGED")
 x
}
distkm<-function(a,b){
 p1<-a[1]*pi/180;p2<-b[1]*pi/180
 dx<-(b[1]-a[1])*pi/180;dy<-(b[2]-a[2])*pi/180
 h<-sin(dx/2)^2+cos(p1)*cos(p2)*sin(dy/2)^2
 6371.0088*2*asin(pmin(1,sqrt(h)))
}
geometric_matches<-function(x){
 r<-x[x$reference,,drop=FALSE]
 a<-x[x$altered,,drop=FALSE]
 if(nrow(r)<3 || nrow(a)<2)return(NULL)
 xy<-as.matrix(rbind(r,a)[,c("lat","lon")])
 if(!all(is.finite(xy))||any(abs(xy[,1])>90)||any(abs(xy[,2])>180))return(NULL)
 rr<-combn(seq_len(nrow(r)),2)
 rr_dist<-apply(rr,2,function(ii)distkm(xy[ii[1],],xy[ii[2],]))
 ar<-as.matrix(expand.grid(ref=seq_len(nrow(r)),alt=seq_len(nrow(a))))
 ar_dist<-apply(ar,1,function(ii)distkm(xy[ii[1],],xy[nrow(r)+ii[2],]))
 # Same source-only geo-rule from pre-biological CI #43166027360.
 best<-vapply(ar_dist,function(v)
    which.min(abs(log((v+.05)/(rr_dist+.05)))),integer(1))
 log_gap<-abs(log((ar_dist+.05)/(rr_dist[best]+.05)))
 use<-which(log_gap<=log(1.5))
 if(ncol(rr)<3 || length(use)<5 ||
    length(unique(ar[use,1]))<2 ||length(unique(ar[use,2]))<2)return(NULL)
 list(
   AR=matrix(c(r$id[ar[use,1]],a$id[ar[use,2]]),ncol=2),
   RR=matrix(c(r$id[rr[1,best[use]]],r$id[rr[2,best[use]]]),ncol=2),
   n_AR_matched=length(use),n_all_AR=nrow(ar),
   n_RR_baseline=ncol(rr),
   mean_abs_geographic_matching_logratio=mean(log_gap[use]),
   selected_AR_zero_distance_count=sum(ar_dist[use]==0),
   selected_RR_zero_distance_count=sum(rr_dist[best[use]]==0))
}
simpson<-function(a,b){
 if(!length(a)||!length(b))return(NA_real_)
 common<-length(intersect(a,b))
 unshared<-min(length(setdiff(a,b)),length(setdiff(b,a)))
 if(common+unshared==0)return(NA_real_)
 unshared/(common+unshared)
}
matched_effect<-function(matches,site_taxa){
 nr<-nrow(matches$AR)
 if(nr!=nrow(matches$RR))stop("STOP_GEOGRAPHIC_MATCHING_PAIRS_COUNT")
 delta<-numeric(nr)
 for(i in seq_len(nr)){
   ar<-matches$AR[i,];rr<-matches$RR[i,]
   if(any(!(c(ar,rr) %in% names(site_taxa))))return(NULL)
   s1<-simpson(site_taxa[[ar[1]]],site_taxa[[ar[2]]])
   s0<-simpson(site_taxa[[rr[1]]],site_taxa[[rr[2]]])
   if(!is.finite(s1)||!is.finite(s0))return(NULL)
   delta[i]<-s1-s0
 }
 list(delta=mean(delta),n_matched_pairs_DEPENDENT=nr)
}
study_infer<-function(x,B=4000,P=9999,seed=20261112){
 if(length(x)<10)return(list(status="STOP_FROZEN_DISTANCE_SUPPORT_LESS_THAN_TEN_STUDIES",
                          effective_studies=length(x)))
 set.seed(seed)
 o<-mean(x)
 b<-replicate(B,mean(sample(x,length(x),replace=TRUE)))
 s<-replicate(P,mean(x*sample(c(-1,1),length(x),replace=TRUE)))
 list(status="EXPLORATORY_DISTANCE_MATCHED_SENSITIVITY_NOT_NEW_CONFIRMATION",
    original_studies=length(x),
    positive_studies=sum(x>0),
    negative_studies=sum(x<0),
    mean_distance_matched_delta_beta_sim=o,
    study_bootstrap_95CI=as.numeric(unname(quantile(b,c(.025,.975)))),
    descriptive_study_sign_flip_two_sided_p=(sum(abs(s)>=abs(o)-1e-12)+1)/(P+1),
    study_bootstrap_B=B,sign_flips_P=P)
}
synthetic<-function(){
 x<-data.frame(id=c("r1","r2","r3","a1","a2"),
   reference=c(TRUE,TRUE,TRUE,FALSE,FALSE),
   altered=c(FALSE,FALSE,FALSE,TRUE,TRUE),
   lat=rep(0,5),lon=c(0,1,2,.5,1.5))
 m<-geometric_matches(x)
 stopifnot(!is.null(m),m$n_AR_matched>=5,
           all(m$AR[,1]%in%c("r1","r2","r3")),
           all(m$AR[,2]%in%c("a1","a2")),
           m$mean_abs_geographic_matching_logratio<=log(1.5))
 taxa<-list(r1=c("A","B","C"),r2=c("A","B","D"),r3=c("A","B","E"),
            a1=c("F","G","H"),a2=c("F","G","I"))
 v<-matched_effect(m,taxa)
 stopifnot(!is.null(v),v$delta>0)
 stopifnot(is.null(geometric_matches(x[x$id!="r3",])))
 cat("SYNTHETIC PASS: fixed geometry before taxa, true paired turnover, 3-reference support\n")
}
if(identical(Sys.getenv("PREDICTS_GEO_MATCHED_SYNTHETIC_ONLY"),"1")){
 synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=1)stop("usage: Rscript predicts_forest_distance_matched_taxa_sensitivity.R OUT")
dir.create(args[[1]],recursive=TRUE,showWarnings=FALSE)
synthetic()
cat("PHASE 1 source-site only: fixed geometric study eligibility before taxon download\n")
sites<-predictsr::GetSitelevelSummaries(extract=c(2016,2022))
x<-forest_scope(sites)
geo<-lapply(split(x,x$group),geometric_matches)
eligible<-geo[!vapply(geo,is.null,logical(1))]
if(length(eligible)!=33){
 stop("STOP_DISTANCE_COMMON_SUPPORT_UNIVERSE_DIFFERS_FROM_SOURCE_ONLY_33_STUDIES")
}
geo_n<-length(eligible);cat("PRE-BIOLOGICAL_GEOGRAPHY_ADMITTED_STUDIES",geo_n,"\n")
rm(sites);gc()
cat("PHASE 2 source biodiversity of preselected sites; PREDICTS primary scorer remains sealed\n")
full<-predictsr::GetPredictsData(extract=c(2016,2022))
if(!is.data.frame(full)||nrow(full)<4000000)stop("STOP_ORIGINAL_NHM_PREDICTS_FULL_SOURCE_MISSING")
req<-c("Taxon_number","Measurement","Diversity_metric_type")
if(!all(req%in%names(full)))stop("STOP_ORIGINAL_TAXON_MEASUREMENT_SCHEMA_CHANGED")
raw_siteid<-site_id(full)
sel<-raw_siteid %in% x$id
raw_n<-sum(sel)
if(raw_n!=242677)stop("STOP_PREVIOUSLY_FROZEN_BIODIVERSITY_EXTRACT_CHANGED")
d<-full[sel,req,drop=FALSE]
d$id<-raw_siteid[sel]
rm(full,raw_siteid,sel);gc()
d$measurement<-suppressWarnings(as.numeric(as.character(d$Measurement)))
d$type<-norm(d$Diversity_metric_type)
d$taxon<-as.character(d$Taxon_number)
valid<-d$type%in%c("abundance","occurrence") &
 is.finite(d$measurement)&d$measurement>=0&!is.na(d$taxon)&d$taxon!=""
d<-d[valid,,drop=FALSE]
types<-vapply(split(d$type,d$id),function(t)paste(sort(unique(t)),collapse="|"),character(1))
positive<-d[d$measurement>0,c("id","taxon"),drop=FALSE]
sets<-lapply(split(positive$taxon,positive$id),unique)
res<-list();reasons<-c()
for(g in names(eligible)){
 group_sites<-x[x$group==g,,drop=FALSE]
 distinct_types<-unique(types[group_sites$id])
 distinct_types<-distinct_types[!is.na(distinct_types)]
 if(length(distinct_types)!=1 || !(distinct_types%in%c("abundance","occurrence"))){
    reasons<-c(reasons,"metric_mismatch");next
 }
 z<-matched_effect(eligible[[g]],sets)
 if(is.null(z)){reasons<-c(reasons,"taxon_absence_or_undefined_beta");next}
 res[[g]]<-c(list(study=group_sites$study[1]),z)
}
if(length(res)<10)stop("STOP_NO_TAXON_VALID_DISTANCE_MATCHED_STUDIES")
study_delta<-vapply(res,function(v)v$delta,numeric(1))
# Eligibility was Study×method×taxon pre-fixed; one stratum each among 39 source Studies.
if(anyDuplicated(vapply(res,function(v)v$study,character(1))))
 stop("STOP_MULTIPLE_BIOLOGICAL_STRATA_PER_ORIGINAL_STUDY")
z<-study_infer(study_delta)
if(z$status=="STOP_FROZEN_DISTANCE_SUPPORT_LESS_THAN_TEN_STUDIES")
 stop("STOP_PRESELECTED_SECONDARY_SENSITIVITY_UNDERPOWERED")
output<-list(
 schema="structural.PREDICTS_forest_distance_matched_secondary_sensitivity.v1",
 frozen_primary_39study_delta_beta_sim=0.0942,
 frozen_primary_39study_result_NOT_REOPENED_FOR_MODEL_TUNING=TRUE,
 this_is_secondary_outcome_exposed_exploratory_sensitivity=TRUE,
 source_original_forest_sites=1145,
 original_Study_groups_frozen=39,
 original_Study_groups_admitted_by_geography_before_biology=33,
 original_Study_groups_with_scored_distance_matched_beta=length(res),
 original_Study_groups_lost_after_metric_frozen_rule=length(reasons),
 secondary_unscoreable_reason_counts=as.list(table(reasons)),
 original_source_taxon_measurement_rows_revisited=raw_n,
 original_source_site_pairs_and_taxon_rows_NOT_independent=TRUE,
 mean_distance_match_abs_log_ratio_study_equal=mean(vapply(eligible,function(v)v$mean_abs_geographic_matching_logratio,numeric(1))),
 source_study_geography_matched_AR_pair_count_nonindependent=sum(vapply(eligible,function(v)v$n_AR_matched,numeric(1))),
 source_study_geography_matched_AR_zero_distance_pairs_nonindependent=sum(vapply(eligible,function(v)v$selected_AR_zero_distance_count,numeric(1))),
 source_study_geography_matched_RR_zero_distance_pairs_nonindependent=sum(vapply(eligible,function(v)v$selected_RR_zero_distance_count,numeric(1))),
 secondary_descriptive_inference=z,
 no_causal_environmental_filtering_or_absolute_richness_stability_claim=TRUE,
 original_distances_have_unverified_coordinate_precision=TRUE,
 forest_canopy_height_or_microclimate_not_observed=TRUE,
 never_fished_multiple_distance_thresholds=TRUE,
 prior_art_PREDICTS_beta_already_studied=TRUE,
 no_original_source_site_study_taxon_measurements_coordinates_exported=TRUE,
 publisher_CC_NC_original_data_not_republished=TRUE,
 eBird_used=FALSE)
writeLines(jsonlite::toJSON(output,pretty=TRUE,auto_unbox=TRUE,null="null"),
 file.path(args[[1]],"predicts_forest_33study_distance_matched_secondary_beta.json"))
cat(jsonlite::toJSON(output,pretty=TRUE,auto_unbox=TRUE,null="null"),"\n")
