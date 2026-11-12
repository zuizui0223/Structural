#!/usr/bin/env Rscript
# 2026 published neonDivData package by Li et al.; not direct NEON API download.
# Use original-curated site, plot, year, forest NLCD and trapping effort fields,
# never species/taxon_id, value, richess or beta-diversity responses in this gate.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))
date_year<-function(x){
 a<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
 a[a<2000|a>2030]<-NA_integer_
 a
}
forest_label<-function(x){
 s<-tolower(trimws(as.character(x)))
 s[is.na(s)]<-""
 grepl("deciduous forest|evergreen forest|mixed forest",s)
}
source_gate<-function(beetle,plant,site_table,expected_version="0.2.3"){
 required_b<-c("siteID","plotID","unique_sample_id","trapID",
             "observation_datetime","nlcdClass","trappingDays","trapConditionFlag")
 required_p<-c("siteID","plotID","observation_datetime","nlcdClass","sample_area_m2")
 if(!all(required_b%in%names(beetle)))stop("STOP_BEETLE_DATA_FRAME_SCHEMA_CHANGED")
 if(!all(required_p%in%names(plant)))stop("STOP_PLANT_DATA_FRAME_SCHEMA_CHANGED")
 if(!all(c("siteID","domainID")%in%names(site_table)))
   stop("STOP_SITETABLE_DOMAIN_CROSSWALK_MISSING")
 if(as.character(utils::packageVersion("neonDivData"))!=expected_version)
   stop("STOP_PUBLISHED_DERIVATIVE_PACKAGE_VERSION_CHANGED")
 b<-beetle[,required_b,drop=FALSE]
 p<-plant[,required_p,drop=FALSE]
 b$year<-date_year(b$observation_datetime)
 p$year<-date_year(p$observation_datetime)
 b<-b[!is.na(b$year)&b$year>=2019&b$year<=2023,,drop=FALSE]
 p<-p[!is.na(p$year)&p$year>=2019&p$year<=2023,,drop=FALSE]
 if(!nrow(b)||!nrow(p))stop("STOP_SOURCE_ORIGINAL_TIMING_EMPTY")
 if(any(is.na(b$siteID)|is.na(p$siteID)))stop("STOP_ORIGINAL_SITE_KEYS_MISSING")
 b$forest<-forest_label(b$nlcdClass)
 p$forest<-forest_label(p$nlcdClass)
 sid_b<-unique(as.character(b$siteID))
 sid_p<-unique(as.character(p$siteID))
 common<-intersect(sid_b,sid_p)
 # Distinct plot-years before reading any taxon or outcome. No raw IDs exported.
 pair_b<-unique(data.frame(siteID=b$siteID,year=b$year))
 pair_p<-unique(data.frame(siteID=p$siteID,year=p$year))
 pair_b$join<-paste(pair_b$siteID,pair_b$year)
 pair_p$join<-paste(pair_p$siteID,pair_p$year)
 overlap<-intersect(pair_b$join,pair_p$join)
 bforest<-unique(data.frame(siteID=b$siteID[b$forest],year=b$year[b$forest]))
 pforest<-unique(data.frame(siteID=p$siteID[p$forest],year=p$year[p$forest]))
 strict_b<-paste(bforest$siteID,bforest$year)
 strict_p<-paste(pforest$siteID,pforest$year)
 forest_years<-intersect(intersect(strict_b,strict_p),overlap)
 forest_sites<-sub(" [0-9]{4}$","",forest_years)
 years_all<-sort(unique(c(b$year,p$year)))
 domains<-unique(data.frame(siteID=site_table$siteID,domain=site_table$domainID))
 domains<-domains[domains$siteID%in%unique(forest_sites),,drop=FALSE]
 tr <- suppressWarnings(as.numeric(as.character(b$trappingDays)))
 valid_effort<-is.finite(tr)&tr>0
 eff_keys<-unique(data.frame(siteID=b$siteID[valid_effort],
    plotID=b$plotID[valid_effort],year=b$year[valid_effort],
    sample_id=b$unique_sample_id[valid_effort]))
 forest_beetle_plotyears<-unique(paste(b$siteID[b$forest],b$plotID[b$forest],b$year[b$forest]))
 forest_plant_plotyears<-unique(paste(p$siteID[p$forest],p$plotID[p$forest],p$year[p$forest]))
 return(list(
    schema="structural.NEON_published_neonDivData_forest_beetle_plant_source_support.v1",
    source="neonDivData independently publicly distributed derivative of NEON organismal products",
    derivative_package_version=expected_version,
    original_NEON_beetle_product="DP1.10022.001",
    original_NEON_plant_product="DP1.10058.001",
    period_2019_to_2023_only=TRUE,
    published_derivative_beetle_full_rows=nrow(beetle),
    published_derivative_plant_full_rows=nrow(plant),
    derivative_beetle_2019_2023_source_rows=nrow(b),
    derivative_plant_2019_2023_source_rows=nrow(p),
    beetle_sites_with_recent_record=length(sid_b),
    plant_sites_with_recent_record=length(sid_p),
    same_site_beetle_and_plant_recorded_site_count=length(common),
    site_years_with_both_beetle_and_plant_observation_metadata=length(overlap),
    NLCD_forest_label_both_taxa_same_siteyear_count=length(forest_years),
    source_sites_with_forest_label_and_same_year_both_taxa=length(unique(forest_sites)),
    original_NLCD_forest_site_domains_WITHOUT_siteID_export=length(unique(domains$domain)),
    unique_forest_label_beetle_plotyears=length(forest_beetle_plotyears),
    unique_forest_label_plant_plotyears=length(forest_plant_plotyears),
    exact_forest_plotyear_identity_overlap_across_taxa=length(intersect(
      forest_beetle_plotyears,forest_plant_plotyears)),
    beetle_original_sample_keys_with_positive_trap_days=nrow(eff_keys),
    beetle_rows_with_missing_or_invalid_trap_days=sum(!valid_effort),
    beetle_rows_with_declared_trap_flag=sum(!is.na(b$trapConditionFlag)&
      nzchar(trimws(as.character(b$trapConditionFlag)))),
    source_NLCD_site_label_not_field_verified_plot_forest=TRUE,
    source_beetle_ground_pitfall_not_canopy_traps=TRUE,
    no_tree_height_microclimate_structure_response_join_yet=TRUE,
    source_taxon_id_name_value_data_NEVER_READ=TRUE,
    zero_catch_record_handling_NOT_ASSUMED_TRUE_ABSENCE=TRUE,
    taxonomic_resolutions_and_effort_NOT_yet_HARMONIZED=TRUE,
    selected_original_site_or_plot_IDs_locations_taxa_counts_NOT_EXPORTED=TRUE,
    same_siteyear_does_not_imply_same_plot_or_temporal_sampling_date=TRUE,
    eBird_used=FALSE
 ))
}
synthetic<-function(){
 x<-c("Deciduous Forest","Evergreen Forest","Mixed Forest","Shrub/Scrub","Pasture/Hay")
 stopifnot(identical(forest_label(x),c(TRUE,TRUE,TRUE,FALSE,FALSE)))
 stopifnot(all(is.na(date_year(c("NA","1890-01-01")))))
 cat("KNOWN-TRUTH PASS: NLCD strict labels and source year, no taxon outcome\n")
}
if(identical(Sys.getenv("NEON_DIVDATA_SYNTHETIC_ONLY"),"1")){
 synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=1)stop("usage: Rscript neon_divdata_multisite_source_gate.R OUT")
synthetic()
out<-args[1];dir.create(out,recursive=TRUE,showWarnings=FALSE)
b<-neonDivData::data_beetle
p<-neonDivData::data_plant
sites<-neonDivData::neon_sites
result<-source_gate(b,p,sites)
writeLines(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE,null="null"),
 file.path(out,"neonDivData_2019_2023_beetle_plant_forest_sourceonly.json"))
cat(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
