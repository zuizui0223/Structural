#!/usr/bin/env Rscript
# Original Kortmann OTU matrix FIRST schema/method sample-ID audit.
# RData deserialization reads response-bearing objects into memory.
# Do NOT inspect OTU abundances, detection, richness, taxa or ecological effects.
SAFE_METHOD_ID_FIELDS <- c(
  "sample","sampleid","sample_id","samplingid","sampling_id",
  "samplecode","sample_code","samplekey","sample_key",
  "eventid","event_id","recordid","record_id","id"
)
METHOD_FIELDS <- c("triplet","plot","treatment","offset")
MAX_OBJECTS <- 12L
MAX_MATRIX_CELLS <- 50000000
is_auto_index <- function(v) {
  length(v)>0L && identical(as.character(v),as.character(seq_along(v)))
}
valid_ids <- function(v, n_expected=702L) {
  if (length(v)!=n_expected || anyNA(v)) return(FALSE)
  vv<-as.character(v)
  if (anyNA(vv) || any(!nzchar(trimws(vv))) ||
      anyDuplicated(vv) || is_auto_index(vv)) return(FALSE)
  TRUE
}
check_complete_source_method <- function(method) {
  if (!is.data.frame(method) || nrow(method)!=702L) {
    stop("SOURCE_METHOD_OBJECT_POPULATION_DRIFT",call.=FALSE)
  }
  names_lower<-tolower(names(method))
  if (anyDuplicated(names_lower) || !all(METHOD_FIELDS %in% names_lower)) {
    stop("SOURCE_METHOD_FOUR_ORIGINAL_KEYS_MISSING",call.=FALSE)
  }
  site<-as.character(method[[match("triplet",names_lower)]])
  plot<-as.character(method[[match("plot",names_lower)]])
  treatment<-as.character(method[[match("treatment",names_lower)]])
  effort<-method[[match("offset",names_lower)]]
  if (anyNA(site) || anyNA(plot) || anyNA(treatment) ||
      !is.numeric(effort) || any(!is.finite(effort))) {
    stop("SOURCE_METHOD_ORIGINAL_FIELD_VALUES_INVALID",call.=FALSE)
  }
  sites<-unique(site)
  complete<-vapply(sites,function(s) {
    ix<-site==s
    length(unique(plot[ix]))==3L &&
    length(unique(treatment[ix]))==3L &&
    nrow(unique(data.frame(plot=plot[ix],treatment=treatment[ix])))==3L
  },logical(1))
  keep<-site %in% sites[complete]
  if (length(sites)!=40L || sum(complete)!=39L || sum(keep)!=690L ||
      length(unique(paste(site,plot,sep="\034")))!=119L) {
    stop("SOURCE_39_COMPLETE_POPULATION_DRIFT",call.=FALSE)
  }
  keep
}
method_id_candidates <- function(method) {
  lower<-tolower(names(method))
  ix<-which(lower %in% SAFE_METHOD_ID_FIELDS)
  arrays<-list()
  for (j in ix) {
    v<-as.character(method[[j]])
    if (valid_ids(v)) arrays[[length(arrays)+1L]]<-v
  }
  rn<-rownames(method)
  if (valid_ids(rn)) arrays[[length(arrays)+1L]]<-as.character(rn)
  # Several representations of one IDENTICAL source ID vector are one
  # unambiguous sample identity, not multiple independent source keys.
  unique_values<-list()
  for (a in arrays) {
    if (!any(vapply(unique_values,identical,logical(1),a))) {
      unique_values[[length(unique_values)+1L]]<-a
    }
  }
  list(vectors=unique_values,method_matching_field_count=length(ix),
       candidate_vectors_before_dedup=length(arrays))
}
simple_type <- function(x) {
  if (is.matrix(x) && length(dim(x))==2L) return("matrix")
  if (is.data.frame(x)) return("data.frame")
  if (is.array(x) && length(dim(x))==2L) return("array")
  if (is.list(x)) return("list")
  "other"
}
inspect_otu <- function(method, otu_env, otu_keys) {
  keep<-check_complete_source_method(method)
  candidates<-method_id_candidates(method)
  if (length(otu_keys)<1L || length(otu_keys)>MAX_OBJECTS ||
      anyDuplicated(otu_keys)) {
    stop("SOURCE_OTU_OBJECT_COUNT_DRIFT",call.=FALSE)
  }
  objects<-list();match_count<-0L;max_overlap<-0L;chosen<-NULL
  for (i in seq_along(otu_keys)) {
    x<-get(otu_keys[[i]],envir=otu_env,inherits=FALSE)
    typ<-simple_type(x)
    has_dim<-typ %in% c("matrix","data.frame","array")
    nr<-if (has_dim) nrow(x) else 0L
    nc<-if (has_dim) ncol(x) else 0L
    if (has_dim && (is.null(nr) || is.null(nc) ||
        !is.finite(nr) || !is.finite(nc) ||
        nr<0L || nc<0L || nr>150000L || nc>150000L ||
        as.double(nr)*as.double(nc)>MAX_MATRIX_CELLS)) {
      stop("SOURCE_OTU_OBJECT_SHAPE_NOT_ADMITTED",call.=FALSE)
    }
    rows<-if (has_dim) rownames(x) else NULL
    cols<-if (has_dim) colnames(x) else NULL
    objects[[length(objects)+1L]]<-c(index=i,type=typ,nrow=nr,ncol=nc,
                               n_rownames=length(rows),n_colnames=length(cols))
    # Match original sample IDs against OTU row or column NAME SETS only.
    # NEVER use row-order indices or inspect numeric OTU values.
    if (has_dim) for (axis in c("rows","columns")) {
      labels<-if (axis=="rows") rows else cols
      if (!valid_ids(labels)) next
      for (v in candidates$vectors) {
        overlap<-sum(v %in% labels)
        max_overlap<-max(max_overlap,overlap)
        if (overlap==702L && setequal(v,labels)) {
          match_count<-match_count+1L
          chosen<-c(object=i,axis=axis,matched_retained=sum(v[keep] %in% labels),
                    matched_excluded=sum(v[!keep] %in% labels))
        }
      }
    }
  }
  ready<-match_count==1L && !is.null(chosen) &&
          chosen[["matched_retained"]]==690L &&
          chosen[["matched_excluded"]]==12L
  list(ready=ready,objects=objects,
       method_candidate_fields=as.integer(candidates$method_matching_field_count),
       method_candidate_vectors=as.integer(length(candidates$vectors)),
       exact_702_matches=as.integer(match_count),
       maximum_anonymous_identifier_overlap=as.integer(max_overlap),
       matched_39_retained=if (ready) 690L else 0L,
       matched_excluded_12=if (ready) 12L else 0L)
}
emit <- function(x) {
  cat("KORTMANN_OTU_ID_SCHEMA_V1\n")
  for (i in seq_along(x$objects)) {
    z<-x$objects[[i]]
    cat("OBJECT\t",z[["index"]],"\t",z[["type"]],"\t",
        z[["nrow"]],"\t",z[["ncol"]],"\t",
        z[["n_rownames"]],"\t",z[["n_colnames"]],"\n",sep="")
  }
  metrics<-list(method_id_eligible_fields=x$method_candidate_fields,
    method_candidate_distinct_vectors=x$method_candidate_vectors,
    exact_702_named_axis_matches=x$exact_702_matches,
    max_unique_source_sample_label_overlap=x$maximum_anonymous_identifier_overlap,
    matched_39_retained_sample_keys=x$matched_39_retained,
    matched_12_excluded_sample_keys=x$matched_excluded_12)
  for (key in names(metrics)) {
    cat("METRIC\t",key,"\t",as.integer(metrics[[key]]),"\n",sep="")
  }
  cat("STATUS\t",if(x$ready) "SOURCE_OTU_702_KEY_MATCH_690_RETAINED_READY_NO_COUNTS"
      else "SOURCE_OTU_SAMPLE_LINK_HOLD","\n",sep="")
  cat("ORIGINAL_OTU_NUMERIC_CELLS_ACCESSED\t0\n")
  cat("ORIGINAL_TAXON_OR_SAMPLE_ID_EXPORTED\t0\n")
  cat("BIOLOGICAL_EFFECTS_FITTED\t0\n")
  cat("OTU_RESPONSE_OBJECT_DESERIALIZED_SCHEMA_ONLY\t1\n")
}
synthetic <- function() {
  d<-expand.grid(round=1:6,state=1:3,site=1:40,KEEP.OUT.ATTRS=FALSE)
  patch<-(d$site-1)*3+d$state
  d<-d[!(patch==1 | (patch %in% 2:13 & d$round==6)),,drop=FALSE]
  stopifnot(nrow(d)==702L)
  m<-data.frame(triplet=paste0("PRIVATE_SITE_",d$site),
    plot=paste0("PRIVATE_PATCH_",d$state),
    treatment=paste0("PRIVATE_TREATMENT_",d$state),
    offset=rep(1.5,702),sample_id=sprintf("PRIV_SAMPLE_%04d",1:702),
    richness=rep(1000000,702),stringsAsFactors=FALSE)
  otu<-matrix(0,nrow=3,ncol=702,dimnames=list(
      c("PRIVATE_TAXON_A","PRIVATE_TAXON_B","PRIVATE_TAXON_C"),
      rev(m$sample_id)))
  e<-new.env(parent=baseenv());assign("PRIVATE_ORIGINAL_OTU",otu,envir=e)
  z<-inspect_otu(m,e,ls(e))
  stopifnot(z$ready,z$exact_702_matches==1L,z$matched_39_retained==690L)
  # Default sequential record positions are not defensible source IDs.
  m2<-m;m2$sample_id<-NULL
  colnames(otu)<-as.character(seq_len(702))
  assign("PRIVATE_ORIGINAL_OTU",otu,envir=e)
  stopifnot(!inspect_otu(m2,e,ls(e))$ready)
  # A duplicate OTU sample label cannot certify one-to-one matching.
  colnames(otu)<-rev(m$sample_id)
  colnames(otu)[2]<-colnames(otu)[1]
  assign("PRIVATE_ORIGINAL_OTU",otu,envir=e)
  stopifnot(!inspect_otu(m,e,ls(e))$ready)
  cat("SYNTHETIC_KORTMANN_OTU_SAMPLE_ID_ONLY_NO_COUNTS_PASS\n")
}
args<-commandArgs(trailingOnly=TRUE)
if (length(args)==1L && args[[1]]=="--synthetic") {
  synthetic()
} else if(length(args)==2L) {
  if(basename(args[[1]])!="diversity_satellite.rda" ||
     basename(args[[2]])!="otu_matrix.rda") {
    stop("SOURCE_RDA_EXPECTED_ORIGINAL_MEMBER_ROLE_ONLY",call.=FALSE)
  }
  a<-new.env(parent=baseenv());b<-new.env(parent=baseenv())
  mk<-tryCatch(load(args[[1]],envir=a),error=function(e)
              stop("SOURCE_METHOD_RDA_PARSE_STOP",call.=FALSE))
  ok<-tryCatch(load(args[[2]],envir=b),error=function(e)
              stop("SOURCE_OTU_RDA_PARSE_STOP",call.=FALSE))
  if(length(mk)!=1L || length(ok)<1L || length(ok)>MAX_OBJECTS) {
    stop("SOURCE_RDATA_OBJECT_COUNT_OR_METHOD_DRIFT",call.=FALSE)
  }
  method<-get(mk[[1]],envir=a,inherits=FALSE)
  emit(inspect_otu(method,b,ok))
} else stop("USAGE_KORTMANN_OTU_METADATA_IDENTITY_ONLY",call.=FALSE)
