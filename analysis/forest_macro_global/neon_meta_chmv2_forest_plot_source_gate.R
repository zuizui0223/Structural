#!/usr/bin/env Rscript
# Public Meta/WRI CHMv2 static canopy-height tile provenance: source metadata
# only. This is NOT annual NEON AOP LiDAR, a sampled original plot footprint
# or a 2019–2023 time series of canopy heights.
# No beetle/plant taxon names, species/abundance, previous effect estimates,
# measured woody heights or source plot/site coordinates enter public exports.
suppressPackageStartupMessages(library(neonDivData))
suppressPackageStartupMessages(library(jsonlite))

YEARS<-2019:2023
FOREST<-c("deciduousforest","evergreenforest","mixedforest")
norm<-function(x){
  z<-tolower(gsub("[[:space:]_/-]+","",as.character(x)))
  z[is.na(z)]<-""
  z
}
is_forest<-function(x)norm(x)%in%FOREST
is_id<-function(x)!is.na(x)&nzchar(trimws(as.character(x)))
get_year<-function(x){
  z<-suppressWarnings(as.integer(substr(as.character(x),1,4)))
  z[!(z%in%YEARS)]<-NA_integer_;z
}
location_centres<-function(loc,site_plot){
  req<-c("siteID","plotID","latitude","longitude")
  if(!all(req%in%names(loc)))stop("STOP_NEON_LOCATION_PLOT_GEO_SCHEMA")
  use<-loc[,intersect(c(req,"location_id"),names(loc)),drop=FALSE]
  use$key<-paste(use$siteID,use$plotID,sep="|")
  use<-use[use$key%in%site_plot,,drop=FALSE]
  use$latitude<-suppressWarnings(as.numeric(as.character(use$latitude)))
  use$longitude<-suppressWarnings(as.numeric(as.character(use$longitude)))
  okay<-is.finite(use$latitude)&is.finite(use$longitude)&
        abs(use$latitude)<=85.05112878&abs(use$longitude)<=180
  use<-use[okay,,drop=FALSE]
  byplot<-split(seq_len(nrow(use)),use$key)
  data<-list()
  for(k in names(byplot)){
    a<-use[byplot[[k]],,drop=FALSE]
    iscanonical<-if("location_id"%in%names(a)){
       grepl("basePlot[.]all$",as.character(a$location_id),ignore.case=TRUE)
    } else rep(FALSE,nrow(a))
    selected<-if(any(iscanonical))a[iscanonical,,drop=FALSE] else a
    if(nrow(selected)==0)next
    spread_m<-if(nrow(selected)<2)0 else {
       # Approximate distance bounds solely for coordinate-grain QC.
       lat_m<-(max(selected$latitude)-min(selected$latitude))*111200
       lon_m<-(max(selected$longitude)-min(selected$longitude))*
         111200*cos(median(selected$latitude)*pi/180)
       sqrt(lat_m^2+lon_m^2)
    }
    # No centroid if conflicting author canonical centre coordinates >10m.
    status<-if(any(iscanonical)){
       if(spread_m<=10)"AUTHOR_ORIGINAL_BASEPLOT_CENTRE" else "STOP_MULTIPLE_INCONSISTENT_CANONICAL_CENTRES"
    } else {
       if(spread_m<=50)"NONCANONICAL_LOCATION_MEDIAN_SPREAD_LE50M" else "STOP_NO_CANONICAL_PLOT_CENTRE_SPREAD_GT50M"
    }
    data[[k]]<-data.frame(original_siteplot_key=k,
      latitude=median(selected$latitude),
      longitude=median(selected$longitude),
      coordinate_source_status=status,
      source_location_rows=nrow(a),stringsAsFactors=FALSE)
  }
  if(!length(data))return(data.frame(original_siteplot_key=character(),
    latitude=numeric(),longitude=numeric(),coordinate_source_status=character(),
    source_location_rows=integer()))
  do.call(rbind,data)
}
source <- function(beetle,plant,loc,site) {
  req_b<-c("siteID","plotID","observation_datetime","nlcdClass",
           "trappingDays","trapConditionFlag","unique_sample_id","trapID")
  req_p<-c("siteID","plotID","observation_datetime","nlcdClass",
           "sample_area_m2","unique_sample_id")
  if(!all(req_b%in%names(beetle))||!all(req_p%in%names(plant))||
     !all(c("site_id","domain_id")%in%names(site))||nrow(site)!=81)
     stop("STOP_NEON_ORIGINAL_ORGANISMAL_SOURCE_SCHEMA")
  if(as.character(packageVersion("neonDivData"))!="0.3.1")
     stop("STOP_NEON_DERIVATIVE_VERSION_DRIFT")
  b<-beetle[,req_b,drop=FALSE]
  p<-plant[,req_p,drop=FALSE]
  b$year<-get_year(b$observation_datetime)
  p$year<-get_year(p$observation_datetime)
  days<-suppressWarnings(as.numeric(as.character(b$trappingDays)))
  areas<-suppressWarnings(as.numeric(as.character(p$sample_area_m2)))
  flags<-as.character(b$trapConditionFlag)
  b<-b[!is.na(b$year)&is_forest(b$nlcdClass)&
    is_id(b$siteID)&is_id(b$plotID)&is_id(b$unique_sample_id)&
    is_id(b$trapID)&is.finite(days)&days>0&
    (is.na(flags)|!nzchar(trimws(flags))),,drop=FALSE]
  p<-p[!is.na(p$year)&is_forest(p$nlcdClass)&
    is_id(p$siteID)&is_id(p$plotID)&is_id(p$unique_sample_id)&
    is.finite(areas)&abs(areas-1)<1e-9,,drop=FALSE]
  makekey<-function(x)paste(x$siteID,x$plotID,x$year,sep="|")
  keys<-intersect(unique(makekey(b)),unique(makekey(p)))
  plots<-unique(sub("\\|[0-9]{4}$","",keys))
  src_sites<-unique(sub("\\|[^|]+\\|[0-9]{4}$","",keys))
  if(length(keys)!=952||length(src_sites)!=35)
    stop("STOP_FROZEN_NEON_2019_2023_FOREST_PATCH_COHORT_952_35_DRIFT")
  ref<-location_centres(loc,plots)
  m<-match(sub("\\|[0-9]{4}$","",keys),ref$original_siteplot_key)
  valid<-!is.na(m)&!grepl("^STOP",ref$coordinate_source_status[m])
  aligned<-data.frame(
    siteID=src_sites[match(sub("\\|[^|]+\\|[0-9]{4}$","",keys),src_sites)],
    plotID=sub("^.*\\|","",sub("\\|[0-9]{4}$","",keys)),
    source_year=as.integer(sub("^.*\\|","",keys)),
    lat=ifelse(!is.na(m),ref$latitude[m],NA_real_),
    lon=ifelse(!is.na(m),ref$longitude[m],NA_real_),
    coordinate_source=ifelse(!is.na(m),ref$coordinate_source_status[m],"NO_ORIGINAL_PLOT_LOCATION"),
    stringsAsFactors=FALSE
  )
  # plotID must be reconstructed exactly from site|plot keys;
  # do not include a "plot" with a guessed identifier.
  aligned$plotID<-substring(sub("\\|[0-9]{4}$","",keys),
      nchar(aligned$siteID)+2)
  if(anyNA(aligned$siteID)||any(!nzchar(aligned$plotID)))
     stop("STOP_PRIVATE_NEON_SITE_PLOT_KEY_PARSE")
  d<-site$domain_id[match(aligned$siteID,site$site_id)]
  if(anyNA(d))stop("STOP_OFFICIAL_SITE_DOMAIN_NOT_FOUND")
  statuses<-table(factor(aligned$coordinate_source,levels=c(
    "AUTHOR_ORIGINAL_BASEPLOT_CENTRE","NONCANONICAL_LOCATION_MEDIAN_SPREAD_LE50M",
    "STOP_MULTIPLE_INCONSISTENT_CANONICAL_CENTRES",
    "STOP_NO_CANONICAL_PLOT_CENTRE_SPREAD_GT50M",
    "NO_ORIGINAL_PLOT_LOCATION")))
  meta<-list(
    schema="structural.NEON_forest_patch_META_CHMv2_original_plot_centroid_source.v1",
    source_neon_organismal_derivative_version="0.3.1",
    original_2019_2023_forest_plot_years_held_fixed=length(keys),
    original_2019_2023_forest_sites_held_fixed=length(src_sites),
    original_siteplot_key_count=length(plots),
    original_siteplot_keys_with_any_source_NEON_location=nrow(ref),
    original_forest_plotyears_with_valid_original_location_coords=sum(valid),
    original_forest_sites_with_valid_original_location_coords=length(unique(aligned$siteID[valid])),
    original_NEON_domains_with_valid_plot_locations=length(unique(d[valid])),
    original_plotyear_coordinate_source_status_counts=as.list(statuses),
    source_year_2019_2020_plotyear_window_count=sum(aligned$source_year<=2020),
    source_year_2021_2023_plotyear_window_count=sum(aligned$source_year>2020),
    META_CHMv2_source_imagery_time_NOT_assumed_same_as_NEON_year=TRUE,
    no_original_species_or_plant_value_or_woody_height_revisited=TRUE,
    no_original_site_plot_lat_lon_IDs_in_public_outputs=TRUE,
    location_point_is_not_exact_40m_NEON_plot_footprint=TRUE,
    previous_2019_2023_10siteyear_height_gate_STOP_preserved=TRUE,
    eBird_used=FALSE
  )
  list(rows=aligned[valid,,drop=FALSE],meta=meta)
}
synthetic<-function(){
  loc<-data.frame(siteID=c("S001","S001","S001","S002"),
    plotID=c("S001_001","S001_001","S001_001","S002_001"),
    location_id=c("S001_001.basePlot.all","S001_001.nw","S001_001.se",
                  "S002_001.subplot"),
    latitude=c(39.00,39.00004,38.99995,42),
    longitude=c(-105,-105.00005,-104.9999,-106))
  r<-location_centres(loc,c("S001|S001_001","S002|S002_001"))
  stopifnot(r$coordinate_source_status[r$original_siteplot_key=="S001|S001_001"]==
     "AUTHOR_ORIGINAL_BASEPLOT_CENTRE",
     r$coordinate_source_status[r$original_siteplot_key=="S002|S002_001"]==
     "NONCANONICAL_LOCATION_MEDIAN_SPREAD_LE50M",
     is_forest("evergreenForest"),!is_forest("shrubScrub"),
     get_year("2019-07-22")==2019,is.na(get_year("2024-07-22")))
  cat("NEON geolocation original plot centre forest-class/source-window synthetic PASS\n")
}
if(identical(Sys.getenv("NEON_META_CHMV2_COORDINATE_SYNTHETIC_ONLY"),"1")){
  synthetic();quit(status=0)
}
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=3)stop("usage: Rscript neon_meta_chmv2_forest_plot_source_gate.R OFFICIAL_81_CSV PRIVATE_CENTROIDS_CSV PUBLIC_META_JSON")
synthetic()
official<-read.csv(args[1],check.names=FALSE,stringsAsFactors=FALSE)
res<-source(neonDivData::data_beetle,neonDivData::data_plant,
            neonDivData::neon_location,official)
dir.create(dirname(args[2]),recursive=TRUE,showWarnings=FALSE)
dir.create(dirname(args[3]),recursive=TRUE,showWarnings=FALSE)
write.csv(res$rows,args[2],row.names=FALSE)
writeLines(jsonlite::toJSON(res$meta,auto_unbox=TRUE,pretty=TRUE,null="null"),
           args[3])
cat(jsonlite::toJSON(res$meta,auto_unbox=TRUE,pretty=TRUE,null="null"),"\n")
