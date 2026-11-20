#!/usr/bin/env Rscript
# Original Kortmann2026 source sampling keys only, four exactly declared fields.
# The first original response-bearing diversity RDA was previously deserialized
# for schema. This script reads triplet, plot, treatment and offset ONLY;
# NO OTU, richness, taxonomy, site labels, treatment codes or offset numbers emitted.

EXPECTED <- c("triplet","plot","treatment","offset")
emit <- function(k,v) {
  stopifnot(grepl("^[a-z][a-z0-9_]*$",k),
            length(v)==1L, is.finite(as.numeric(v)))
  cat("METRIC\t",k,"\t",as.integer(v),"\n",sep="")
}

frame_check <- function(df) {
  if (!is.data.frame(df) || nrow(df)!=702L) {
    stop("SOURCE_METHOD_ORIGINAL_702_ROW_FRAME_MISMATCH",call.=FALSE)
  }
  fields <- names(df)
  if (anyDuplicated(tolower(fields))) {
    stop("SOURCE_METHOD_DUPLICATED_CASEFOLD_FIELDS",call.=FALSE)
  }
  ix <- match(EXPECTED,tolower(fields))
  if (anyNA(ix)) {
    stop("SOURCE_METHOD_REQUIRED_FOUR_FIELDS_ABSENT",call.=FALSE)
  }
  # Hard firewall: access exactly the four source METHOD columns,
  # do not access any original diversity/richness/OTU response field.
  x <- df[[ix[[1]]]]
  y <- df[[ix[[2]]]]
  z <- df[[ix[[3]]]]
  effort <- df[[ix[[4]]]]
  key <- function(v) {
    x <- as.character(v)
    if (anyNA(x) || any(!nzchar(trimws(x)))) {
      stop("SOURCE_METHOD_BLANK_OR_MISSING_KEY",call.=FALSE)
    }
    x
  }
  site <- key(x)
  plot <- key(y)
  treatment <- key(z)
  num_site <- length(unique(site))
  num_treatment <- length(unique(treatment))
  sp <- unique(data.frame(site=site,plot=plot,stringsAsFactors=FALSE))
  st <- unique(data.frame(site=site,treatment=treatment,stringsAsFactors=FALSE))
  spt <- unique(data.frame(site=site,plot=plot,treatment=treatment,
                           stringsAsFactors=FALSE))
  triplet_plot_counts <- table(site)
  # 40 site-level observed sample rows are NOT expected equal,
  # but each site must have exactly 3 original physical patch labels.
  physical_per_site <- vapply(split(sp$plot,sp$site),length,integer(1))
  treatment_per_site <- vapply(split(st$treatment,st$site),length,integer(1))
  # Every original site-treatment must point to exactly one physical plot.
  nplot_per_site_treatment <- vapply(
    split(spt$plot,interaction(spt$site,spt$treatment,drop=TRUE)),
    function(v) length(unique(v)), integer(1))
  # each site×plot has one stable treatment and up to six sampled occasions.
  ntreat_per_site_plot <- vapply(
    split(spt$treatment,interaction(spt$site,spt$plot,drop=TRUE)),
    function(v) length(unique(v)), integer(1))
  plot_rows <- as.integer(table(interaction(site,plot,drop=TRUE)))
  n_missing <- sum(6L-plot_rows)
  effort_finite <- is.numeric(effort) &&
                   all(is.finite(effort)) && !anyNA(effort)
  results <- c(
    original_observed_sampling_rows=nrow(df),
    original_site_triplets=num_site,
    original_triplet_plot_pairs=nrow(sp),
    original_source_treatment_codes=num_treatment,
    original_triplet_treatment_pairs=nrow(st),
    triplets_with_three_distinct_plots=sum(physical_per_site==3),
    triplets_with_three_treatment_codes=sum(treatment_per_site==3),
    source_site_treatment_groups_with_single_plot=sum(nplot_per_site_treatment==1),
    source_site_plot_groups_with_single_treatment=sum(ntreat_per_site_plot==1),
    sampled_rows_per_plot_min=min(plot_rows),
    sampled_rows_per_plot_max=max(plot_rows),
    physical_patches_with_six_sample_rows=sum(plot_rows==6),
    physical_patches_with_fewer_than_six_rows=sum(plot_rows<6),
    nominal_720_minus_observed_702=720L-nrow(df),
    counted_source_patch_opportunity_deficit=n_missing,
    all_offset_values_numeric_and_finite=as.integer(effort_finite)
  )
  pass <- (
    results[["original_observed_sampling_rows"]]==702 &&
    num_site==40 && nrow(sp)==120 && num_treatment==3 &&
    nrow(st)==120 && all(physical_per_site==3) &&
    all(treatment_per_site==3) &&
    all(nplot_per_site_treatment==1) &&
    all(ntreat_per_site_plot==1) &&
    all(plot_rows>=1 & plot_rows<=6) &&
    n_missing==18 && effort_finite
  )
  list(metrics=results,pass=isTRUE(pass))
}

inspect <- function(f) {
  if (basename(f)!="diversity_satellite.rda" || !file.exists(f)) {
    stop("SOURCE_ORIGINAL_MEMBER_NOT_EXPECTED",call.=FALSE)
  }
  e<-new.env(parent=baseenv())
  n<-tryCatch(load(f,envir=e),error=function(err)
    stop("SOURCE_RDA_RELOAD_STOP",call.=FALSE))
  candidates<-Filter(function(q) {
    obj<-get(q,envir=e,inherits=FALSE)
    is.data.frame(obj) && nrow(obj)==702L &&
      all(EXPECTED %in% tolower(names(obj)))
  },n)
  if (length(candidates)!=1) {
    stop("SOURCE_ORIGINAL_SINGLE_702ROW_FOUR_METHOD_FIELD_OBJECT_NOT_FOUND",
         call.=FALSE)
  }
  # Reader is shape/schema-exposed; no other original field is selected.
  result<-frame_check(get(candidates[[1]],envir=e,inherits=FALSE))
  cat("ORIGINAL_METHOD_FRAME_V1\n")
  for (nm in names(result$metrics)) emit(nm,result$metrics[[nm]])
  cat("SOURCE_METHOD_FRAME_STATUS\t",
      if (result$pass) "SOURCE_ORIGINAL_TRIPLET_3STATE_702_FRAME_COUNT_READY_NO_OTU"
      else "SOURCE_ORIGINAL_METHOD_FRAME_HOLD","\n",sep="")
  cat("ORIGINAL_SOURCE_ID_OR_TREATMENT_LABEL_EXPORTED\t0\n")
  cat("ORIGINAL_BIOLOGICAL_EFFECT_ESTIMATED\t0\n")
  cat("SOURCE_RDA_PREVIOUSLY_DESERIALIZED_RESPONSE_BEARING\t1\n")
}

args<-commandArgs(trailingOnly=TRUE)
if (length(args)==1L && args[[1]]=="--synthetic") {
  d<-expand.grid(
    sample=seq_len(6), state=seq_len(3), site=seq_len(40),
    KEEP.OUT.ATTRS=FALSE
  )
  # Drop the sixth sampled occasion in the first 18 anonymous patches.
  patchnum<-(d$site-1)*3+d$state
  d<-d[!(patchnum<=18 & d$sample==6),,drop=FALSE]
  stopifnot(nrow(d)==702L)
  fake<-data.frame(triplet=paste0("PRIVATE_SITE_",d$site),
     plot=paste0("PRIVATE_PLOT_",d$state),treatment=paste0("STATE_",d$state),
     offset=rep(1.5,nrow(d)), rich=d$sample,stringsAsFactors=FALSE)
  result<-frame_check(fake)
  stopifnot(result$pass, result$metrics[["original_site_triplets"]]==40,
     result$metrics[["counted_source_patch_opportunity_deficit"]]==18)
  cat("SYNTHETIC_KORTMANN_40_TRIPLET_18_MISSING_SOURCE_METHOD_PASS\n")
} else if (length(args)==1L) {
  inspect(args[[1]])
} else {
  stop("USAGE_KORTMANN_SOURCE_METHOD_FRAME",call.=FALSE)
}
