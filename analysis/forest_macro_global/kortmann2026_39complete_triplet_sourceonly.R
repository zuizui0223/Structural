#!/usr/bin/env Rscript
# Kortmann original 39 complete source triplets ONLY, without OTU/alpha/beta.
# Source RData is already response-bearing schema-exposed; only 4 method columns
# are selected, no source literal IDs/labels or biological values leave the run.
fields <- c("triplet","plot","treatment","offset")

summarize_frame <- function(df) {
  stopifnot(is.data.frame(df),nrow(df)==702L)
  n <- tolower(names(df))
  if (anyDuplicated(n))stop("DUPLICATE_METHOD_FIELDS",call.=FALSE)
  idx<-match(fields,n)
  if (anyNA(idx))stop("FOUR_METHOD_FIELDS_MISSING",call.=FALSE)
  ids <- lapply(idx[1:3],function(i) as.character(df[[i]]))
  if (any(vapply(ids,function(a) anyNA(a)||any(!nzchar(trimws(a))),logical(1))))
    stop("MISSING_METHOD_IDS",call.=FALSE)
  site<-ids[[1]];plot<-ids[[2]];state<-ids[[3]]
  offset<-df[[idx[4]]]
  effort_ok<-is.numeric(offset) && all(is.finite(offset))
  tp<-unique(data.frame(site=site,plot=plot,stringsAsFactors=FALSE))
  ts<-unique(data.frame(site=site,state=state,stringsAsFactors=FALSE))
  tps<-unique(data.frame(site=site,plot=plot,state=state,stringsAsFactors=FALSE))
  sites<-unique(site)
  # Each original triplet must have exactly one original physical plot for
  # each of the 3 globally observed source treatment states.
  full_treatments<-unique(state)
  elig<-vapply(sites,function(s) {
    pts<-tp[tp$site==s,,drop=FALSE]
    sts<-ts[ts$site==s,,drop=FALSE]
    local<-tps[tps$site==s,,drop=FALSE]
    nrow(pts)==3 && nrow(sts)==3 &&
    setequal(sts$state,full_treatments) &&
    nrow(local)==3 && !anyDuplicated(local$state) &&
    !anyDuplicated(local$plot)
  },logical(1))
  retained<-sites[elig]
  keep<-site %in% retained
  se<-site[keep];pe<-plot[keep];te<-state[keep]
  patches<-interaction(se,pe,drop=TRUE)
  tab<-as.integer(table(patches))
  sort_state_counts<-sort(as.integer(table(te)))
  n_retained <-sum(keep)
  old_patches<-nrow(tp)
  new_patches<-length(tab)
  n_missing <-39L*3L*6L-n_retained
  result<-c(
    original_observed_rows=length(site),
    original_distinct_triplets=length(sites),
    original_source_three_treatment_codes=length(full_treatments),
    original_sampled_patches=old_patches,
    retained_complete_triplets=length(retained),
    excluded_incomplete_triplets=sum(!elig),
    retained_original_observed_rows=n_retained,
    excluded_triplet_observed_rows=length(site)-n_retained,
    retained_sampled_patches=new_patches,
    retained_patches_with_six_records=sum(tab==6),
    retained_patches_with_five_records=sum(tab==5),
    retained_patch_samples_min=min(tab),
    retained_patch_samples_max=max(tab),
    retained_nominal_missing_rounds=n_missing,
    all_original_offsets_finite_numeric=as.integer(effort_ok),
    retained_treatment_count_sorted_first=sort_state_counts[[1]],
    retained_treatment_count_sorted_second=sort_state_counts[[2]],
    retained_treatment_count_sorted_third=sort_state_counts[[3]]
  )
  pass <- (length(site)==702 && length(sites)==40 &&
       length(full_treatments)==3 && old_patches==119 &&
       length(retained)==39 && sum(!elig)==1 &&
       new_patches==117 && n_retained>=690 && n_retained<=692 &&
       length(sort_state_counts)==3 && all(tab %in% 5:6) &&
       n_missing>=10 && n_missing<=12 && effort_ok)
  list(metrics=result,pass=isTRUE(pass))
}

emit <- function(q) {
  cat("KORTMANN_39_METHOD_V1\n")
  for(n in names(q$metrics)) {
    stopifnot(grepl("^[a-z][a-z0-9_]*$",n))
    cat("METRIC\t",n,"\t",as.integer(q$metrics[[n]]),"\n",sep="")
  }
  cat("STATUS\t",
      if(q$pass) "SOURCE_39_COMPLETE_TRIPLETS_METHOD_READY_NO_OTU"
      else "SOURCE_39_TRIPLET_METHOD_HOLD","\n",sep="")
  cat("NO_SOURCE_SITE_TREATMENT_OR_OFFSET_VALUES_EXPORTED\t1\n")
  cat("NO_SPECIES_OTU_BIOLOGICAL_EFFECT_SCORED\t1\n")
  cat("ORIGINAL_40_TRIPLET_STRICT_GATE_STILL_HOLD\t1\n")
}

args<-commandArgs(trailingOnly=TRUE)
if(length(args)==1L && identical(args[[1]],"--synthetic")) {
  d<-expand.grid(sample=1:6,state=1:3,site=1:40,
                 KEEP.OUT.ATTRS=FALSE)
  patch<-(d$site-1)*3+d$state
  # one full six-round patch loss + twelve other single-period losses
  d<-d[!(patch==1 | (patch %in% 2:13 & d$sample==6)),,drop=FALSE]
  stopifnot(nrow(d)==702L)
  fake<-data.frame(
    triplet=paste0("PRIVATE_SITE_",d$site),
    plot=paste0("P_",d$state),
    treatment=paste0("PRIVATE_STATE_",d$state),
    offset=rep(1.25,nrow(d)),
    private_richness=rep(987654,nrow(d)),
    stringsAsFactors=FALSE)
  q<-summarize_frame(fake)
  stopifnot(q$pass, q$metrics[["retained_complete_triplets"]]==39,
            q$metrics[["excluded_incomplete_triplets"]]==1,
            q$metrics[["retained_original_observed_rows"]] %in% 690:692)
  cat("SYNTHETIC_KORTMANN_39_COMPLETE_SOURCE_ONLY_PASS\n")
} else if (length(args)==1L) {
  f<-args[[1]]
  if(basename(f)!="diversity_satellite.rda"||!file.exists(f))
    stop("ORIGINAL_SOURCE_FILE_ROLE_STOP",call.=FALSE)
  e<-new.env(parent=baseenv())
  keys<-tryCatch(load(f,envir=e),error=function(err)stop("RDA_PARSE_STOP",call.=FALSE))
  qualified<-Filter(function(s) {
    x<-get(s,envir=e,inherits=FALSE)
    is.data.frame(x)&&nrow(x)==702&&all(fields%in%tolower(names(x)))
  },keys)
  if(length(qualified)!=1L)stop("SOURCE_FRAME_AMBIGUOUS",call.=FALSE)
  emit(summarize_frame(get(qualified[[1]],envir=e,inherits=FALSE)))
} else stop("USAGE_KORTMANN_39_SOURCE_ONLY",call.=FALSE)
