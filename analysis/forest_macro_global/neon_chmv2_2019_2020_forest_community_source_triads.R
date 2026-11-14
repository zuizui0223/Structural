#!/usr/bin/env Rscript
# Source-metadata-only NEON forest patch spatial sampling eligibility against
# one static Meta/WRI CHMv2 p90 per original plot: 2019-2020 surveys only.
# NO beetle/plant taxon_id, taxon_name, value or previous response accessed.
suppressPackageStartupMessages(library(jsonlite))
suppressPackageStartupMessages(library(neonDivData))
YEARS<-2019:2020
fields_beetle<-c("siteID","plotID","observation_datetime","nlcdClass",
                 "trappingDays","trapConditionFlag","unique_sample_id","trapID")
fields_plant<-c("siteID","plotID","observation_datetime","nlcdClass",
                "sample_area_m2","unique_sample_id","subplotID")
source_date<-function(x)suppressWarnings(as.Date(substr(as.character(x),1,10)))
year<-function(x){
  z<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  z[!(z%in%YEARS)]<-NA_integer_;z
}
valid<-function(x)!is.na(x)&nzchar(trimws(as.character(x)))
isforest<-function(x){
  x<-tolower(gsub("[[:space:]_/-]+","",as.character(x)))
  x[is.na(x)]<-"";x%in%c("deciduousforest","evergreenforest","mixedforest")
}
ratio<-function(x,y)is.finite(x)&&is.finite(y)&&x>0&&y>0&&x/y>=.5&&x/y<=2
earth_km<-function(a,b) {
  # Coordinates are original basePlot centroid; no polygons inferred.
  lat1<-a[1]*pi/180;lat2<-b[1]*pi/180
  dy<-(b[1]-a[1])*pi/180;dx<-(b[2]-a[2])*pi/180
  h<-sin(dy/2)^2+cos(lat1)*cos(lat2)*sin(dx/2)^2
  6371.0088*2*asin(min(1,sqrt(h)))
}
qualified_plotyear<-function(bb,pp) {
  if(!nrow(bb)||!nrow(pp))return(NULL)
  x<-unique(paste(bb$siteID,bb$plotID,year(bb$observation_datetime),sep="|"))
  y<-unique(paste(pp$siteID,pp$plotID,year(pp$observation_datetime),sep="|"))
  if(length(x)!=1||length(y)!=1||x!=y||anyNA(year(bb$observation_datetime))||
     anyNA(year(pp$observation_datetime)))
    stop("SCIENTIFIC_STOP_SOURCE_SITE_PLOT_YEAR_MIXING")
  pp<-pp[isforest(pp$nlcdClass),,drop=FALSE]
  ps<-suppressWarnings(as.numeric(as.character(pp$sample_area_m2)))
  pd<-source_date(pp$observation_datetime)
  pv<-is.finite(ps)&abs(ps-1)<1e-9&
      valid(pp$unique_sample_id)&valid(pp$subplotID)&!is.na(pd)
  if(!any(pv))return(NULL)
  earliest<-min(pd[pv])
  pl<-pp[pv&abs(as.numeric(pd-earliest))<=7,,drop=FALSE]
  pn<-length(unique(as.character(pl$subplotID)))
  bb<-bb[isforest(bb$nlcdClass),,drop=FALSE]
  bd<-source_date(bb$observation_datetime)
  beff<-suppressWarnings(as.numeric(as.character(bb$trappingDays)))
  flags<-as.character(bb$trapConditionFlag)
  bgood<-is.finite(beff)&beff>0&valid(bb$unique_sample_id)&valid(bb$trapID)&
      (is.na(flags)|!nzchar(trimws(flags)))&!is.na(bd)&
      abs(as.numeric(bd-earliest))<=30
  b<-bb[bgood,,drop=FALSE]
  if(!nrow(b))return(NULL)
  effort<-split(suppressWarnings(as.numeric(as.character(b$trappingDays))),
                as.character(b$unique_sample_id))
  if(any(vapply(effort,function(z)length(unique(z))!=1,logical(1))))
    stop("SCIENTIFIC_STOP_ORIGINAL_TRAP_SAMPLE_EFFORT_CONFLICT")
  if(length(effort)<4||pn<4)return(NULL)
  list(
    site=as.character(b$siteID[1]),
    plot=as.character(b$plotID[1]),
    year=year(b$observation_datetime[1]),
    first_plant=earliest,
    total_beetle_trapdays=sum(vapply(effort,function(z)z[1],numeric(1))),
    recorded_plant_subplots=pn,
    unflagged_beetle_samples=length(effort))
}
compatible<-function(a,b){
  ratio(a$total_beetle_trapdays,b$total_beetle_trapdays)&&
    ratio(a$recorded_plant_subplots,b$recorded_plant_subplots)&&
    abs(as.numeric(a$first_plant-b$first_plant))<=30
}
choose_complete_clique<-function(rows) {
  if(length(rows)<3)return(NULL)
  if(length(rows)>20)stop("SCIENTIFIC_STOP_SOURCE_TOO_MANY_FOREST_PLOTS_PER_SITEYEAR")
  rows<-rows[order(names(rows))]  # sort key–value pairs together, never relabel plot measurements
  keys<-names(rows)
  ok<-matrix(FALSE,nrow=length(keys),ncol=length(keys))
  diag(ok)<-TRUE
  for(i in seq_along(keys))for(j in seq_along(keys)){
    if(i>=j)next
    ok[i,j]<-compatible(rows[[keys[i]]],rows[[keys[j]]])
    ok[j,i]<-ok[i,j]
  }
  # Search complete compatible plot sets by decreasing size, deterministic
  # original plot name order. An incomplete graph is not a plot-clique.
  for(n in seq(length(keys),3L,by=-1L)){
    tuples<-combn(seq_along(keys),n)
    for(col in seq_len(ncol(tuples))){
      sub<-tuples[,col]
      if(!all(ok[sub,sub,drop=FALSE]))next
      heights<-vapply(rows[keys[sub]],function(x)x$CHM_p90_m,numeric(1))
      if(length(unique(heights))<2)next
      return(keys[sub])
    }
  }
  NULL
}
source_gate<-function(beetle,plant,plotgeo,chm,site) {
  if(as.character(utils::packageVersion("neonDivData"))!="0.3.1"||
     !all(fields_beetle%in%names(beetle))||!all(fields_plant%in%names(plant)))
    stop("SCIENTIFIC_STOP_PUBLISHED_ORGANISMAL_SOURCE_SCHEMA_DRIFT")
  if(nrow(site)!=81||!all(c("site_id","domain_id")%in%names(site)))
    stop("SCIENTIFIC_STOP_ORIGINAL_NEON_81SITE_DOMAIN_SCHEMA_DRIFT")
  if(nrow(plotgeo)!=952||!all(c("siteID","plotID","source_year","lat","lon")%in%names(plotgeo)))
    stop("SCIENTIFIC_STOP_PREVIOUS_952_ORIGINAL_PLOTYEAR_GEO_FRAME_DRIFT")
  if(nrow(chm)!=232||!all(c("siteID","plotID","CHM_p90_m",
        "positive_fraction","source_tile_acq_start","source_tile_acq_end")%in%names(chm)))
    stop("SCIENTIFIC_STOP_PREVIOUS_CHMv2_232_40M_PLOT_QA_DRIFT")
  good_chm<-paste(chm$siteID,chm$plotID,sep="|")
  if(anyDuplicated(good_chm))stop("SCIENTIFIC_STOP_DUPLICATE_STATIC_CHM_PLOT")
  if(any(!is.finite(as.numeric(chm$CHM_p90_m))|as.numeric(chm$CHM_p90_m)<=0))
    stop("SCIENTIFIC_STOP_CHMv2_POSITIVE_P90_NONFINITE")
  original<-plotgeo[plotgeo$source_year %in% YEARS,,drop=FALSE]
  if(nrow(original)!=395)stop("SCIENTIFIC_STOP_FROZEN_395_NEON_2019_2020_PLOTYEAR_SOURCE_DRIFT")
  original_ids<-paste(original$siteID,original$plotID,sep="|")
  match_chm<-original_ids%in%good_chm
  if(sum(match_chm)!=388)stop("SCIENTIFIC_STOP_FROZEN_388_CHMv2_QA_FIELD_PLOTYEAR_FRAME_DRIFT")
  ids<-paste(original$siteID,original$plotID,original$source_year,sep="|")
  available<-ids[match_chm]
  b<-beetle[,fields_beetle,drop=FALSE];p<-plant[,fields_plant,drop=FALSE]
  by<-year(b$observation_datetime);py<-year(p$observation_datetime)
  bid<-paste(b$siteID,b$plotID,by,sep="|")
  pid<-paste(p$siteID,p$plotID,py,sep="|")
  b<-b[!is.na(by)&bid%in%available,,drop=FALSE]
  p<-p[!is.na(py)&pid%in%available,,drop=FALSE]
  bi<-split(seq_len(nrow(b)),paste(b$siteID,b$plotID,year(b$observation_datetime),sep="|"))
  pi<-split(seq_len(nrow(p)),paste(p$siteID,p$plotID,year(p$observation_datetime),sep="|"))
  common<-intersect(names(bi),names(pi))
  if(length(common)!=388)stop("STOP_388_ORIGINAL_FOREST_BIO_METADATA_CROSSJOIN_DRIFT")
  original_chm<-setNames(seq_len(nrow(chm)),good_chm)
  orig_geo<-setNames(seq_len(nrow(original)),ids)
  qualified<-list()
  for(k in common) {
    x<-qualified_plotyear(b[bi[[k]],,drop=FALSE],p[pi[[k]],,drop=FALSE])
    if(is.null(x))next
    chmindex<-original_chm[[paste(x$site,x$plot,sep="|")]]
    geoindex<-orig_geo[[k]]
    x$CHM_p90_m<-as.numeric(chm$CHM_p90_m[chmindex])
    x$lat<-as.numeric(original$lat[geoindex]);x$lon<-as.numeric(original$lon[geoindex])
    x$scene_start<-as.Date(chm$source_tile_acq_start[chmindex])
    x$scene_end<-as.Date(chm$source_tile_acq_end[chmindex])
    if(!all(is.finite(c(x$lat,x$lon))))stop("STOP_ORIGINAL_CHM_PLOT_POSITION_MISSING")
    qualified[[k]]<-x
  }
  groups<-split(names(qualified),vapply(qualified,function(x)
       paste(x$site,x$year,sep="|"),character(1)))
  grouped_source<-list();possible_years<-character()
  for(ky in names(groups)){
    ks<-groups[[ky]]
    if(length(ks)<3)next
    s<-qualified[ks]
    names(s)<-vapply(s,function(x)x$plot,character(1))
    s<-s[order(names(s))]
    clique<-choose_complete_clique(s)
    if(is.null(clique))next
    if(length(clique)<3)stop("STOP_CLIQUE_SOURCE_GRAIN_NOT_GE3")
    values<-s[clique]
    positions<-lapply(values,function(v)c(v$lat,v$lon))
    distances<-combn(seq_along(positions),2,FUN=function(ix)
       earth_km(positions[[ix[1]]],positions[[ix[2]]]))
    if(any(!is.finite(distances))||any(distances<0))stop("STOP_PRIVATE_ORIGINAL_GEO_DISTANCE")
    scene_window<-vapply(values,function(v)
      v$scene_start<=as.Date(paste0(v$year,"-12-31")) &&
      v$scene_end>=as.Date(paste0(v$year,"-01-01")),logical(1))
    grouped_source[[ky]]<-list(
      site=values[[1]]$site,year=values[[1]]$year,
      compatible_clique_original_plots=length(clique),
      source_CHMv2_p90_range_metres=diff(range(vapply(values,
              function(v)v$CHM_p90_m,numeric(1)))),
      original_pairwise_earth_distance_km_median=median(distances),
      original_pairwise_zero_distance_count=sum(distances==0),
      number_original_selected_plots_with_source_CHM_TILE_window_overlapping_sample_year=sum(scene_window))
  }
  original_siteyear<-names(grouped_source)
  unique_site<-unique(vapply(grouped_source,function(x)x$site,character(1)))
  dom<-unique(site$domain_id[match(unique_site,site$site_id)])
  if(anyNA(dom))stop("STOP_SELECTED_FOREST_SITE_DOMAIN")
  # Primary future sample is one source year/site chosen by 2020 preference
  # when both 2020 and 2019 have a complete triad; never by beta outcome.
  selection<-list()
  for(si in unique_site) {
    keys<-names(grouped_source)[vapply(grouped_source,function(x)x$site==si,logical(1))]
    priority<-order(-vapply(grouped_source[keys],function(x)x$year,integer(1)))
    selection[[si]]<-keys[priority[1]]
  }
  allpairs<-sum(vapply(grouped_source,function(x)
    choose(x$compatible_clique_original_plots,2),numeric(1)))
  eligible_source_plotyear<-sum(vapply(grouped_source,function(x)
    x$compatible_clique_original_plots,numeric(1)))
  gate<-length(unique_site)>=10&&length(dom)>=6&&length(original_siteyear)>=12
  list(
     schema="structural.NEON_MetaCHMv2_2019_2020_35site_forest_patch_beetle_plant_spatial_source_triads.v1",
     independent_satellite_CHMv2_fixed_static_40m_source_not_annual_LiDAR=TRUE,
     original_source_NEON_2019_2020_forest_patch_plot_years_before_CHM_QA=nrow(original),
     original_NEON_2019_2020_plotyears_with_CHMv2_232plot_pixel_QA=sum(match_chm),
     original_two_taxon_plotyear_same_source_metadata_keys=length(common),
     original_plotyear_keys_4plus_beetle_samples_4plus_1m2_recorded_plants_during_common_season=length(qualified),
     original_same_siteyear_groups_with_at_least_three_preclique_qualified_forest_plots=sum(lengths(groups)>=3),
     original_siteyear_groups_with_complete_effort_and_date_comparable_three_plot_source_CHM_contrasts=length(original_siteyear),
     original_independent_NEON_sites_with_forest_plot_source_triads=length(unique_site),
     original_NEON_ecoclimatic_domains_with_source_triads=length(dom),
     original_CHM_exposure_plots_in_complete_source_triads_NONINDEPENDENT=eligible_source_plotyear,
     original_CHM_source_forest_plot_pairs_in_triads_NONINDEPENDENT=allpairs,
     original_source_triads_2020_preferred_siteyear_selected_one_per_site=length(selection),
     source_CHM_positive_40m_p90_range_median_in_qualified_triads=if(length(grouped_source))
       median(vapply(grouped_source,function(x)x$source_CHMv2_p90_range_metres,numeric(1))) else NULL,
     source_original_pairwise_median_geographic_distance_km_in_siteyear_triads=if(length(grouped_source))
       median(vapply(grouped_source,function(x)x$original_pairwise_earth_distance_km_median,numeric(1))) else NULL,
     source_original_zero_distance_plot_pairs_in_qualified_triads=sum(vapply(grouped_source,function(x)
       x$original_pairwise_zero_distance_count,numeric(1))),
     source_selected_plots_where_TILE_DATE_WINDOW_overlaps_ORIGINAL_NEON_YEAR_NONPROOF=sum(vapply(grouped_source,function(x)
       x$number_original_selected_plots_with_source_CHM_TILE_window_overlapping_sample_year,numeric(1))),
     source_original_site_years_by_calendar_year=as.list(table(factor(
        vapply(grouped_source,function(x)as.character(x$year),character(1)),levels=as.character(YEARS)))),
     metadata_frozen_10sites_6domains_12siteyears_source_gate_PASS=gate,
     gate_status=if(gate) "CHMV2_2019_2020_FOREST_SPATIAL_SAMPLE_METADATA_ELIGIBLE_TAXA_UNOPENED" else
        "SCIENTIFIC_STOP_NEON_CHMV2_SPATIAL_FOREST_PLOT_TRIAD_SUPPORT",
     original_source_plot_names_coordinates_height_taxa_values_not_exported=TRUE,
     source_CHMv2_p90_date_tile_window_NOT_neon_pixel_sameyear_proof=TRUE,
     plant_1m2_observed_subplots_not_complete_zero_survey_effort=TRUE,
     source_original_beetle_plant_taxon_species_abundance_values_NOT_READ=TRUE,
     NEON_2019_2023_VST_12siteyear_SCIENTIFIC_STOP_UNCHANGED=TRUE,
     previous_PREDICTS_and_NEON_temporal_biodiversity_results_sealed=TRUE,
     eBird_used=FALSE
  )
}
synthetic<-function(){
  df<-list()
  for(i in seq_len(4)){
     df[[paste0("plot",i)]]<-list(plot=paste0("plot",i),site="S001",year=2020,
       CHM_p90_m=12+i,total_beetle_trapdays=14,
       recorded_plant_subplots=8,
       first_plant=as.Date("2020-06-10")+i)
  }
  q<-choose_complete_clique(df)
  stopifnot(length(q)==4,all(names(df)%in%q))
  df$plot4$total_beetle_trapdays<-1000
  stopifnot(length(choose_complete_clique(df))==3)
  df$plot2$recorded_plant_subplots<-1
  stopifnot(is.null(choose_complete_clique(df)))
  stopifnot(earth_km(c(0,0),c(0,1))>110,
    isforest(c("mixedForest","evergreenForest"))[1],
    is.na(year("2023-09-12")))
  cat("CHMv2 FOREST SPATIAL source-only complete plot triad, original effort/date pair QA synthetic PASS\n")
}
if(identical(Sys.getenv("NEON_CHM_SPATIAL_TRIADS_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=4)stop("usage: Rscript neon_chmv2_2019_2020_forest_community_source_triads.R OFFICIAL_NEON_CSV ORIGINAL_952_PLOTYEAR_COORDINATES_CSV PRIVATE_CHM_232_PLOT_HEIGHTS_CSV AGGREGATE_OUTPUT")
synthetic()
official<-read.csv(args[1],stringsAsFactors=FALSE)
geo<-read.csv(args[2],stringsAsFactors=FALSE)
chm<-read.csv(args[3],stringsAsFactors=FALSE)
result<-source_gate(neonDivData::data_beetle,neonDivData::data_plant,
                    geo,chm,official)
dir.create(args[4],recursive=TRUE,showWarnings=FALSE)
file<-file.path(args[4],"NEON_CHMv2_2019_2020_forest_spatial_community_source_eligible_groups.json")
writeLines(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE,null="null"),file)
cat(jsonlite::toJSON(result,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
