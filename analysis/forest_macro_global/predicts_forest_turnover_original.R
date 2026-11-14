#!/usr/bin/env Rscript
# Independent cross-study forest macro pilot on original PREDICTS 2016+2022.
# One predeclared observational estimand, retrospective source reanalysis,
# not a new experiment or an independent published-cohort confirmation.
#
# Main endpoint per original Study×sampling method×common taxon:
# mean Simpson species/taxon replacement for ALTERED-vs-REFERENCE site pairs
# MINUS mean reference-vs-reference Simpson replacement.
# Equal-weight independent ORIGINAL STUDY mean; forest comparators only.
#
# Never treat nested site pairs, study strata, repeated species or individual
# biological records as independent forest regions. No raw CC-NC source data,
# source taxon names, coordinates, site or source IDs are redistributed.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(predictsr))

norm <- function(x) {
  a <- tolower(trimws(as.character(x)))
  a[is.na(a)] <- ""
  gsub("[[:space:]]+"," ",a)
}
vec <- function(d,k) {
  if (!(k %in% names(d))) stop(paste("SOURCE_SCHEMA_REQUIRED_FIELD_MISSING",k))
  as.character(d[[k]])
}
site_key <- function(d) {
  if("SSBS" %in% names(d)) return(vec(d,"SSBS"))
  paste(vec(d,"Source_ID"),vec(d,"Study_number"),
        vec(d,"Block"),vec(d,"Site_number"),sep="|")
}
study_key <- function(d) {
  if("SS" %in% names(d))return(vec(d,"SS"))
  paste(vec(d,"Source_ID"),vec(d,"Study_number"),sep="|")
}
notmissing <- function(x) !is.na(x) & x!=""
isforest <- function(x) grepl("forest|woodland|mangrove|laurel",norm(x))
source_support <- function(s) {
  needed <- c("Source_ID","Study_number","Sampling_method","Study_common_taxon",
    "Biome","Habitat_as_described","Predominant_land_use","Use_intensity",
    "Country","Sample_midpoint")
  if(!all(needed %in% names(s)))stop("STOP_SOURCE_SITE_SUMMARY_FIELDS_DRIFT")
  id <- site_key(s)
  if(any(!notmissing(id))) stop("STOP_SOURCE_SITE_KEYS_MISSING")
  if(length(unique(id)) < .95*nrow(s)) stop("STOP_SOURCE_SITE_GRAIN")
  study <- study_key(s)
  method <- norm(vec(s,"Sampling_method"))
  common <- norm(vec(s,"Study_common_taxon"))
  biome <- norm(vec(s,"Biome"))
  lu <- norm(vec(s,"Predominant_land_use"))
  intensity <- norm(vec(s,"Use_intensity"))
  strict <- grepl("forest|taiga|woodland",biome) &
    isforest(vec(s,"Habitat_as_described")) &
    grepl("^primary vegetation|^secondary vegetation|^plantation forest",lu)
  reference <- strict & grepl("^primary vegetation",lu) &
    grepl("minimal|light",intensity)
  altered <- strict & grepl("^secondary vegetation|^plantation forest",lu)
  group <- paste(study,method,common,sep="|||")
  keep <- !duplicated(id) & strict
  local <- data.frame(id=id[keep],study=study[keep],group=group[keep],
    reference=reference[keep],altered=altered[keep],
    country=vec(s,"Country")[keep],biome=vec(s,"Biome")[keep],
    stringsAsFactors=FALSE)
  split_rows <- split(seq_len(nrow(local)),local$group)
  admitted <- names(Filter(function(ix) {
    q<-local[ix,,drop=FALSE]
    sum(q$reference)>=2 && sum(q$altered)>=2
  },split_rows))
  out <- local[local$group %in% admitted,,drop=FALSE]
  if(nrow(out)==0)stop("STOP_NO_MATCHED_FOREST_CONTRAST")
  list(rows=out,baseline_n=nrow(s),eligible_n=nrow(out),
    stratum_n=length(admitted),study_n=length(unique(out$study)),
    country_n=length(unique(out$country)))
}
beta_sim <- function(a,b) {
  if(!length(a) || !length(b)) return(NA_real_)
  overlap <- length(intersect(a,b))
  shared_unique_min <- min(length(setdiff(a,b)),length(setdiff(b,a)))
  z <- overlap+shared_unique_min
  if(z==0)return(NA_real_)
  shared_unique_min/z
}
group_effect <- function(q,taxa) {
  # "q" has site IDs, stable sample grain and source reference statuses.
  if(anyDuplicated(q$id))stop("STOP_DUPLICATE_PHYSICAL_SITE_WITHIN_STRATUM")
  rr<-q$id[q$reference];aa<-q$id[q$altered]
  rr<-rr[rr %in% names(taxa)]
  aa<-aa[aa %in% names(taxa)]
  if(length(rr)<2 || length(aa)<2)return(NULL)
  score <- function(x,y) beta_sim(taxa[[x]],taxa[[y]])
  rr_scores <- combn(rr,2,FUN=function(x)score(x[1],x[2]))
  ra_scores <- unlist(lapply(aa,function(a)
    vapply(rr,function(r)score(a,r),numeric(1))),use.names=FALSE)
  if(any(!is.finite(rr_scores))||any(!is.finite(ra_scores)))return(NULL)
  p_ref<-length(rr_scores);p_alt<-length(ra_scores)
  list(
    observed_reference_site_count=length(rr),
    observed_modified_site_count=length(aa),
    within_reference_pairs_DEPENDENT=p_ref,
    between_modified_reference_pairs_DEPENDENT=p_alt,
    mean_within_reference_beta_sim=mean(rr_scores),
    mean_modified_reference_beta_sim=mean(ra_scores),
    delta_relative_to_reference_variation=mean(ra_scores)-mean(rr_scores),
    absolute_mean_site_alpha_reference=mean(vapply(rr,function(x)length(taxa[[x]]),numeric(1))),
    absolute_mean_site_alpha_altered=mean(vapply(aa,function(x)length(taxa[[x]]),numeric(1)))
  )
}
cluster_inference <- function(study_effects,B=4000,P=9999,seed=20261112) {
  x<-as.numeric(study_effects)
  n<-length(x)
  if(n<5)return(list(status="STOP_FEWER_THAN_FIVE_EFFECTIVE_STUDIES",
    effective_studies=n))
  set.seed(seed)
  boots<-replicate(B,mean(sample(x,n,replace=TRUE)))
  null<-replicate(P,mean(x*sample(c(-1,1),n,replace=TRUE)))
  est<-mean(x)
  ci<-unname(quantile(boots,c(.025,.975),na.rm=TRUE))
  list(status="STUDY_EQUAL_EXPLORATORY_RESULT",
    effective_original_studies=n,
    original_studies_positive=sum(x>0),
    original_studies_negative=sum(x<0),
    original_studies_zero=sum(x==0),
    study_equal_delta_beta_sim=est,
    study_bootstrap_95_percentile_interval=as.numeric(ci),
    two_sided_study_sign_flip_association_p=(1+sum(abs(null)>=abs(est)-1e-12))/(P+1),
    study_bootstrap_reps=B,
    study_sign_flip_randomizations=P,
    no_pairwise_sample_independence_claim=TRUE,
    no_causal_landuse_or_species_colonization_claim=TRUE
  )
}
synthetic <- function(){
  # Species replacement without richness loss; study-method matched source data
  a<-c("A","B","C")
  b<-c("A","B","D")
  c<-c("E","F","G")
  d<-c("E","F","H")
  stopifnot(beta_sim(a,a)==0,
    beta_sim(a,b)==1/3,
    beta_sim(a,c)==1,
    beta_sim(a,c)==beta_sim(c,a),
    beta_sim(a,c)>beta_sim(a,b))
  q<-data.frame(id=c("r1","r2","m1","m2"),
    reference=c(TRUE,TRUE,FALSE,FALSE),
    altered=c(FALSE,FALSE,TRUE,TRUE))
  res<-group_effect(q,list(r1=a,r2=b,m1=c,m2=d))
  stopifnot(res$observed_reference_site_count==2,
    res$observed_modified_site_count==2,
    abs(res$mean_within_reference_beta_sim-1/3)<1e-12,
    res$mean_modified_reference_beta_sim==1,
    abs(res$delta_relative_to_reference_variation-2/3)<1e-12,
    res$absolute_mean_site_alpha_reference==3,
    res$absolute_mean_site_alpha_altered==3)
  fake<-rep(res$delta_relative_to_reference_variation,8)
  est<-cluster_inference(fake,B=199,P=199)
  stopifnot(est$study_equal_delta_beta_sim>0,
            est$study_bootstrap_95_percentile_interval[1]>0)
  cat("SYNTHETIC PASS: taxon turnover, stable alpha, no species/site labels, nested study estimator\n")
}
if(identical(Sys.getenv("FOREST_PREDICTS_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=1)stop("usage: Rscript predicts_forest_turnover_original.R OUTPUT_DIR")
dest<-args[[1]];dir.create(dest,recursive=TRUE,showWarnings=FALSE)
synthetic()
cat("PHASE 1: Retrieve official original PREDICTS 2016+2022 SITE summaries.\n")
sites<-predictsr::GetSitelevelSummaries(extract=c(2016,2022))
if(!is.data.frame(sites))stop("STOP_ORIGINAL_SITE_SUMMARY_NOT_DATAFRAME")
q<-source_support(sites)
cat("Site support before reading biological outcomes: ",q$eligible_n," / ",
    q$stratum_n," study×method×taxon strata / ",q$study_n," studies\n")
if(q$baseline_n!=35738 || q$eligible_n!=1145 || q$stratum_n!=39 ||
   q$country_n!=20)stop("STOP_PREVIOUSLY_FROZEN_FOREST_SITE_SUPPORT_DRIFT")
selected<-q$rows
rm(sites);gc()
cat("PHASE 2: Fetch author-original PREDICTS diversity extract and restrict to frozen forest sites.\n")
d<-predictsr::GetPredictsData(extract=c(2016,2022))
if(!is.data.frame(d)||nrow(d)<4e6)stop("STOP_ORIGINAL_MEASUREMENT_DATA_MISSING")
needed <- c("Taxon_number","Measurement","Diversity_metric_type")
if(!all(needed %in% names(d)))stop("STOP_ORIGINAL_MEASUREMENT_SCHEMA_CHANGED")
id<-site_key(d)
ok<-id %in% selected$id
n_selected_source_records<-sum(ok)
if(n_selected_source_records<1000)stop("STOP_ORIGINAL_SITE_TO_TAXON_CROSSWALK_NOT_SUPPORTED")
rows<-d[ok,c("Taxon_number","Measurement","Diversity_metric_type"),drop=FALSE]
rows$id<-id[ok]
rm(d,id,ok);gc()
rows$measure_num<-suppressWarnings(as.numeric(as.character(rows$Measurement)))
rows$type<-norm(rows$Diversity_metric_type)
rows$taxon<-as.character(rows$Taxon_number)
allowed<-rows$type %in% c("abundance","occurrence") &
  is.finite(rows$measure_num) & rows$measure_num>=0 &
  notmissing(rows$taxon)
usable<-rows[allowed,c("id","taxon","measure_num","type")]
studymap<-selected[match(unique(usable$id),selected$id),c("id","study","group")]
names(studymap)[1]<-"id"
table_types<-split(usable$type,usable$id)
per_site_type<-vapply(table_types,function(x)paste(sort(unique(x)),collapse="|"),character(1))
outcomes<-split(seq_len(nrow(usable)),usable$id)
taxa_by_site<-lapply(outcomes,function(ix){
  unique(usable$taxon[ix][usable$measure_num[ix]>0])
})
taxa_by_site<-taxa_by_site[lengths(taxa_by_site)>0]
scores<-list();excluded<-list()
for(g in unique(selected$group)){
  sub<-selected[selected$group==g,,drop=FALSE]
  # An original study with mixed abundance/occurrence measurement at a site
  # is not automatically harmonized into a zero-inflated shared response.
  original_site_types<-unique(per_site_type[sub$id])
  original_site_types<-original_site_types[!is.na(original_site_types)]
  if(length(original_site_types)!=1 ||
     !(original_site_types %in% c("abundance","occurrence"))){
    excluded[[g]]<-"STOP_NONHOMOGENEOUS_OR_MISSING_SOURCE_METRIC"
    next
  }
  z<-group_effect(sub,taxa_by_site)
  if(is.null(z)){
    excluded[[g]]<-"STOP_FEWER_THAN_TWO_NONEMPTY_SITES_OR_UNDEFINED_BETA"
    next
  }
  scores[[g]]<-c(list(original_study=sub$study[1],source_biome=sub$biome[1]),z)
}
if(length(scores)==0)stop("STOP_NO_TAXON_LEVEL_FOREST_GROUPS_SCOREABLE")
studies<-split(vapply(scores,function(x)x$delta_relative_to_reference_variation,numeric(1)),
                vapply(scores,function(x)x$original_study,character(1)))
study_means<-vapply(studies,mean,numeric(1))
infer<-cluster_inference(study_means)
by_biome<-split(vapply(scores,function(x)x$delta_relative_to_reference_variation,numeric(1)),
               vapply(scores,function(x)x$source_biome,character(1)))
biomes<-lapply(by_biome,function(x)list(n_study_strata=length(x),
                      group_equal_delta_beta_sim=mean(x),groups_positive=sum(x>0)))
# Do not export raw group/site/species/study identifiers, original
# locations, raw measurements, or row-level source data (CC NC).
compact<-list(
  schema="structural.forest_macro_PREDICTS_within_study_reference_replacement.v1",
  original_source="NHM PREDICTS 2016+2022 public official releases via predictsr",
  observational_primary_endpoint="mean Simpson taxon replacement(modified, reference) minus mean replacement(reference,reference)",
  source_original_site_summary_rows=q$baseline_n,
  original_prevalidated_eligible_forest_sites=q$eligible_n,
  original_prevalidated_study_method_taxon_strata=q$stratum_n,
  original_prevalidated_countries=q$country_n,
  original_original_studies_represented_preoutcome=q$study_n,
  source_original_taxon_records_in_preselected_site_frame=n_selected_source_records,
  source_eligible_nonnegative_abundance_or_occurrence_taxon_measurements=nrow(usable),
  original_groups_with_valid_taxon_beta=length(scores),
  original_groups_unscoreable_after_fixed_metric_and_nonempty_rule=length(excluded),
  group_stop_reason_frequencies=as.list(table(unlist(excluded,use.names=FALSE))),
  source_original_studies_with_valid_species_identity_response=length(study_means),
  primary_study_equal_inference=infer,
  within_site_group_delta_sign_positive=sum(vapply(scores,function(x)x$delta_relative_to_reference_variation>0,logical(1))),
  within_site_group_delta_sign_negative=sum(vapply(scores,function(x)x$delta_relative_to_reference_variation<0,logical(1))),
  biome_summary_ANONYMIZED_ONLY=lapply(unname(biomes),identity),
  original_taxon_number_used_study_locally=TRUE,
  taxonomy_mixed_rank_not_called_species=TRUE,
  land_use_is_observational_cross_sectional_not_intervention=TRUE,
  site_pairwise_comparisons_not_independent_replicates=TRUE,
  real_study_not_equal_to_independent_forest_biome=TRUE,
  prior_art_PREDICTS_beta_diversity_already_explored=TRUE,
  tested_canopy_height_or_3D_vertical_niche=FALSE,
  no_independent_contemporary_2020s_forest_response=TRUE,
  no_original_source_site_species_IDs_coordinates_or_measurements_exported=TRUE,
  publisher_noncommercial_license_respected_raw_not_republished=TRUE,
  eBird_used=FALSE
)
writeLines(jsonlite::toJSON(compact,auto_unbox=TRUE,pretty=TRUE,null="null"),
           file.path(dest,"predicts_forest_reference_altered_turnover_original_aggregate.json"))
cat(jsonlite::toJSON(compact,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
