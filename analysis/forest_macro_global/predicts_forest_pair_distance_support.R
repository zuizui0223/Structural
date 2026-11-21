#!/usr/bin/env Rscript
# Source-site-only forest macro geographic comparability gate.
# No PREDICTS taxon measurement, species names, biomass or abundance accessed.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(predictsr))
norm <- function(x){
 y <- tolower(trimws(as.character(x)));y[is.na(y)] <- ""
 gsub("[[:space:]]+"," ",y)
}
key <- function(d){
 if ("SSBS" %in% names(d))return(as.character(d$SSBS))
 paste(as.character(d$Source_ID),as.character(d$Study_number),
       as.character(d$Block),as.character(d$Site_number),sep="|")
}
study <- function(d){
 if ("SS" %in% names(d))return(as.character(d$SS))
 paste(as.character(d$Source_ID),as.character(d$Study_number),sep="|")
}
sites <- function(data){
 req <- c("Source_ID","Study_number","Habitat_as_described",
 "Predominant_land_use","Use_intensity","Biome","Sampling_method",
 "Study_common_taxon","Latitude","Longitude","Country")
 if(!all(req %in% names(data)))stop("STOP_ORIGINAL_SITE_METADATA_SCHEMA_DRIFT")
 k<-key(data);u<-norm(data$Predominant_land_use)
 strict<-grepl("forest|taiga|woodland",norm(data$Biome))&
   grepl("forest|woodland|mangrove|laurel",norm(data$Habitat_as_described))&
   grepl("^primary vegetation|^secondary vegetation|^plantation forest",u)
 refs<-strict & grepl("^primary vegetation",u) &
   grepl("minimal|light",norm(data$Use_intensity))
 alt<-strict & grepl("^secondary vegetation|^plantation forest",u)
 g<-paste(study(data),norm(data$Sampling_method),
          norm(data$Study_common_taxon),sep="|||")
 z<-data.frame(k=k,g=g,study=study(data),ref=refs,alt=alt,
    lat=suppressWarnings(as.numeric(as.character(data$Latitude))),
    lon=suppressWarnings(as.numeric(as.character(data$Longitude))),
    cm=if("Coordinates_method" %in% names(data))norm(data$Coordinates_method) else "",
    stringsAsFactors=FALSE)
 z<-z[!duplicated(z$k)&strict,,drop=FALSE]
 good<-vapply(split(z,z$g),function(v)sum(v$ref)>=2 && sum(v$alt)>=2,logical(1))
 z<-z[z$g %in% names(good)[good],,drop=FALSE]
 if(nrow(z)!=1145 || length(unique(z$g))!=39 ||
    length(unique(z$study))!=39)
   stop("STOP_FROZEN_MATCHED_FOREST_SITE_UNIVERSE_DRIFT")
 z
}
distance <- function(a,b){
 p1<-a[1]*pi/180;p2<-b[1]*pi/180
 dlat<-(b[1]-a[1])*pi/180;dlon<-(b[2]-a[2])*pi/180
 h<-sin(dlat/2)^2+cos(p1)*cos(p2)*sin(dlon/2)^2
 6371.0088*2*asin(pmin(1,sqrt(h)))
}
geom_group <- function(x){
 rf<-x[x$ref,,drop=FALSE];al<-x[x$alt,,drop=FALSE]
 if(nrow(rf)<2 || nrow(al)<2)return(NULL)
 points<-rbind(rf,al)
 xy<-as.matrix(points[,c("lat","lon")])
 valid<-all(is.finite(xy[,1])&is.finite(xy[,2])&
             abs(xy[,1])<=90&abs(xy[,2])<=180)
 if(!valid)return(list(geographic_source_support=FALSE))
 rr<-combn(seq_len(nrow(rf)),2,FUN=function(ii)
   distance(xy[ii[1],],xy[ii[2],]))
 ar<-unlist(lapply(seq_len(nrow(al)),function(i)
   vapply(seq_len(nrow(rf)),
      function(j)distance(xy[nrow(rf)+i,],xy[j,]),numeric(1))),
   use.names=FALSE)
 # The following criteria are source-geometry-only, frozen independently
 # of the previously observed biological beta endpoint.
 gap<-vapply(ar,function(v)min(abs(log((v+.05)/(rr+.05)))),numeric(1))
 matchable<-which(gap<=log(1.5))
 modified_indices<-rep(seq_len(nrow(al)),each=nrow(rf))
 reference_indices<-rep(seq_len(nrow(rf)),times=nrow(al))
 common_support<-(nrow(rf)>=3 && length(rr)>=3 &&
   length(matchable)>=5 &&
   length(unique(modified_indices[matchable]))>=2 &&
   length(unique(reference_indices[matchable]))>=2)
 # Protect from division by zero if all reference points share a centroid.
 list(geographic_source_support=TRUE,
   original_ar_pairs_within_1p5x_of_a_source_rr_distance=length(matchable),
   original_AR_modified_sites_with_distance_match=length(unique(modified_indices[matchable])),
   original_AR_reference_sites_with_distance_match=length(unique(reference_indices[matchable])),
   geometry_only_fixed_distance_common_support=common_support,
   mean_ref_ref_km=mean(rr),mean_alt_ref_km=mean(ar),
   median_ref_ref_km=median(rr),median_alt_ref_km=median(ar),
   delta_altref_minus_refref_km=mean(ar)-mean(rr),
   log_ratio_of_mean_geographic_distances=
     log((mean(ar)+.001)/(mean(rr)+.001)),
   original_geographic_reference_pair_count_DEPENDENT=length(rr),
   original_geographic_alt_reference_pair_count_DEPENDENT=length(ar),
   source_original_sites=nrow(x),
   source_coordinate_method_all_from_metadata=
     all(x$cm %in% c("","original","original coordinates","from author","field coordinates")),
   missing_coordinate_method_rows=sum(x$cm==""),
   original_coordinate_method_distinct_levels=length(unique(x$cm)))
}
synthetic<-function(){
 q<-data.frame(ref=c(TRUE,TRUE,FALSE,FALSE),
    alt=c(FALSE,FALSE,TRUE,TRUE),
    lat=c(0,0,0,0),lon=c(0,1,3,4),cm="original")
 res<-geom_group(q)
 stopifnot(res$mean_alt_ref_km>res$mean_ref_ref_km,
    !res$geometry_only_fixed_distance_common_support,
    res$original_geographic_reference_pair_count_DEPENDENT==1,
    res$original_geographic_alt_reference_pair_count_DEPENDENT==4,
    abs(distance(c(0,0),c(0,1))-111.195)<.01)
 q$lon[4]<-NA_real_
 stopifnot(!geom_group(q)$geographic_source_support)
 cat("SYNTHETIC SUCCESS: source-site distance pair hierarchy and missing location STOP\n")
}
if(identical(Sys.getenv("FOREST_PREDICTS_GEOGRAPHY_SYNTHETIC_ONLY"),"1")){
 synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=1)stop("usage: Rscript predicts_forest_pair_distance_support.R OUTDIR")
out<-args[[1]];dir.create(out,recursive=TRUE,showWarnings=FALSE)
synthetic()
cat("ORIGINAL source-site only geospatial support audit starting, no taxon data download.\n")
raw<-predictsr::GetSitelevelSummaries(extract=c(2016,2022))
if(!is.data.frame(raw)||nrow(raw)!=35738)stop("STOP_SITE_SOURCE_SIZE_DRIFT")
z<-sites(raw)
metric<-lapply(split(z,z$g),geom_group)
okay<-vapply(metric,function(v)isTRUE(v$geographic_source_support),logical(1))
eligible<-metric[okay]
study_equal_ratio<-vapply(eligible,function(v)v$log_ratio_of_mean_geographic_distances,numeric(1))
study_equal_difference<-vapply(eligible,function(v)v$delta_altref_minus_refref_km,numeric(1))
common<-sum(vapply(eligible,function(v)isTRUE(v$geometry_only_fixed_distance_common_support),logical(1)))
i<-list(
 schema="structural.PREDICTS_39forest_source_site_geographic_support.v2",
 source="NHM PREDICTS original 2016+2022 site summaries only",
 previous_observed_positive_beta_difference_unaltered=0.0942,
 original_source_summaries=nrow(raw),
 original_forest_sites_eligible=nrow(z),
 original_study_method_taxon_comparisons=length(metric),
 study_contexts_with_finite_original_site_coordinates=length(eligible),
 study_contexts_without_original_comparable_coordinates=sum(!okay),
 original_studies_altref_geographically_farther_than_refref=sum(study_equal_difference>0),
 original_studies_altref_geographically_nearer_than_refref=sum(study_equal_difference<0),
 original_studies_equal_distance_zero=sum(study_equal_difference==0),
 original_studies_passing_frozen_geographic_overlap_rule=common,
 fixed_geographic_overlap_rule="3+ reference sites; >=5 AR pairs with log distance ratio within log1.5 of a RR pair; >=2 altered and >=2 reference sites; distances offset +0.05km",
 second_biological_sensitivity_study_count_gate_ge10=common>=10,
 second_biological_sensitivity_still_NOT_RUN=TRUE,
 study_equal_mean_log_ratio_altref_refref=if(length(eligible))mean(study_equal_ratio) else NULL,
 study_equal_median_distance_difference_km=if(length(eligible))median(study_equal_difference) else NULL,
 study_equal_median_reference_reference_distance_km=if(length(eligible))median(vapply(eligible,function(v)v$mean_ref_ref_km,numeric(1))) else NULL,
 study_equal_median_altered_reference_distance_km=if(length(eligible))median(vapply(eligible,function(v)v$mean_alt_ref_km,numeric(1))) else NULL,
 original_coordinate_methods_not_equivalent_to_gps_precision=TRUE,
 no_causal_geography_adjusted_biodiversity_inference=TRUE,
 no_taxon_species_or_abundance_biological_response_read=TRUE,
 original_source_site_IDs_coordinates_or_reference_spatial_pairs_not_exported=TRUE,
 original_PREDICTS_observational_39_study_result_not_rescored=TRUE,
 source_site_pairs_are_DEPENDENT_and_not_independent_forests=TRUE,
 possible_spatial_distance_decay_confounding_remains=TRUE,
 eBird_used=FALSE
)
writeLines(jsonlite::toJSON(i,auto_unbox=TRUE,pretty=TRUE,null="null"),
 file.path(out,"predicts_forest_39study_source_only_distance_support.json"))
cat(jsonlite::toJSON(i,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
