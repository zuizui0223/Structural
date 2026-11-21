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
  length(v)>0L && setequal(as.character(v),as.character(seq_along(v)))
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
  if (any(vapply(list(site,plot,treatment),function(v)
        anyNA(v) || any(!nzchar(trimws(v))),logical(1))) ||
      !is.numeric(effort) || any(!is.finite(effort))) {
    stop("SOURCE_METHOD_ORIGINAL_FIELD_VALUES_INVALID",call.=FALSE)
  }
  sites<-unique(site)
  treatments<-unique(treatment)
  complete<-vapply(sites,function(s) {
    ix<-site==s
    length(unique(plot[ix]))==3L &&
    length(unique(treatment[ix]))==3L && setequal(treatment[ix],treatments) &&
    nrow(unique(data.frame(plot=plot[ix],treatment=treatment[ix])))==3L
  },logical(1))
  keep<-site %in% sites[complete]
  patch_sizes<-function(ss) unlist(lapply(ss,function(s)
    as.integer(table(plot[site==s]))),use.names=FALSE)
  retained_sizes<-patch_sizes(sites[complete])
  excluded_sizes<-patch_sizes(sites[!complete])
  treatment_sizes<-as.integer(table(treatment[keep]))
  if (length(sites)!=40L || length(treatments)!=3L ||
      sum(complete)!=39L || sum(keep)!=690L || sum(!keep)!=12L ||
      nrow(unique(data.frame(site=site,plot=plot)))!=119L ||
      length(retained_sizes)!=117L || sum(retained_sizes==6L)!=105L ||
      sum(retained_sizes==5L)!=12L || length(excluded_sizes)!=2L ||
      any(excluded_sizes!=6L) || length(treatment_sizes)!=3L ||
      any(treatment_sizes!=230L)) {
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
  rn<-row.names(method)
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
  explicit_class<-attr(x,"class",exact=TRUE)
  if (is.data.frame(x) && identical(explicit_class,"data.frame"))
    return("data.frame")
  if (is.matrix(x) && is.atomic(x) &&
      (is.null(explicit_class) || identical(explicit_class,c("matrix","array"))))
    return("matrix")
  if (is.list(x)) return("list")
  "other"
}
inspect_otu <- function(method, otu_env, otu_keys) {
  keep<-check_complete_source_method(method)
  candidates<-method_id_candidates(method)
  objects<-list();match_count<-0L;max_overlap<-0L;chosen<-NULL
  schema_hold<-FALSE
  result<-function() {
    ready<-!schema_hold && match_count==1L && !is.null(chosen) &&
            chosen[["matched_retained"]]==690L &&
            chosen[["matched_excluded"]]==12L
    list(ready=ready,schema_hold=schema_hold,objects=objects,
         loaded_otu_object_count=length(otu_keys),
         method_candidate_fields=as.integer(candidates$method_matching_field_count),
         method_candidate_vectors=as.integer(length(candidates$vectors)),
         exact_702_matches=as.integer(match_count),
         maximum_anonymous_identifier_overlap=as.integer(max_overlap),
         matched_39_retained=if (ready) 690L else 0L,
         matched_excluded_12=if (ready) 12L else 0L)
  }
  if (length(otu_keys)<1L || length(otu_keys)>MAX_OBJECTS ||
      anyDuplicated(otu_keys)) {
    schema_hold<-TRUE
    return(result())
  }
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
      # Omit an unadmitted shape, without a misleading truncated dimension.
      schema_hold<-TRUE;objects<-list();match_count<-0L;max_overlap<-0L
      return(result())
    }
    square_candidate<-has_dim && nr==702L && nc==702L
    if (!has_dim || square_candidate) schema_hold<-TRUE
    # Do not access the noncandidate (possibly taxon) axis labels at all.
    # A square sample-sized container is held before either accessor.
    rows<-if (has_dim && !square_candidate && nr==702L) {
      if(typ=="data.frame") row.names(x) else attr(x,"dimnames",exact=TRUE)[[1L]]
    } else NULL
    cols<-if (has_dim && !square_candidate && nc==702L) {
      if(typ=="data.frame") names(x) else attr(x,"dimnames",exact=TRUE)[[2L]]
    } else NULL
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
  result()
}
emit <- function(x) {
  cat("KORTMANN_OTU_ID_SCHEMA_V1\n")
  for (i in seq_along(x$objects)) {
    z<-x$objects[[i]]
    cat("OBJECT\t",z[["index"]],"\t",z[["type"]],"\t",
        z[["nrow"]],"\t",z[["ncol"]],"\t",
        z[["n_rownames"]],"\t",z[["n_colnames"]],"\n",sep="")
  }
  metrics<-list(loaded_otu_object_count=x$loaded_otu_object_count,
    method_id_eligible_fields=x$method_candidate_fields,
    method_candidate_distinct_vectors=x$method_candidate_vectors,
    exact_702_named_axis_matches=x$exact_702_matches,
    max_unique_source_sample_label_overlap=x$maximum_anonymous_identifier_overlap,
    matched_39_retained_sample_keys=x$matched_39_retained,
    matched_12_excluded_sample_keys=x$matched_excluded_12)
  for (key in names(metrics)) {
    cat("METRIC\t",key,"\t",as.integer(metrics[[key]]),"\n",sep="")
  }
  cat("STATUS\t",if(x$schema_hold) "SOURCE_OTU_OBJECT_SCHEMA_HOLD"
      else if(x$ready) "SOURCE_OTU_702_KEY_MATCH_690_RETAINED_READY_NO_COUNTS"
      else "SOURCE_OTU_SAMPLE_LINK_HOLD","\n",sep="")
  cat("ORIGINAL_OTU_NUMERIC_CELLS_ACCESSED\t0\n")
  cat("ORIGINAL_TAXON_OR_SAMPLE_ID_EXPORTED\t0\n")
  cat("BIOLOGICAL_EFFECTS_FITTED\t0\n")
  cat("OTU_RESPONSE_OBJECT_DESERIALIZED_SCHEMA_ONLY\t1\n")
}
read_original <- function(method_path,otu_path,stage_path) {
  if(basename(method_path)!="diversity_satellite.rda" ||
     basename(otu_path)!="otu_matrix.rda" || file.exists(stage_path)) {
    stop("SOURCE_RDA_EXPECTED_MEMBER_ROLE_OR_FRESH_STAGE_REQUIRED",call.=FALSE)
  }
  a<-new.env(parent=baseenv());b<-new.env(parent=baseenv())
  mk<-tryCatch(load(method_path,envir=a),error=function(e)
              stop("SOURCE_METHOD_RDA_PARSE_STOP",call.=FALSE))
  if(length(mk)!=1L) stop("SOURCE_METHOD_OBJECT_COUNT_DRIFT",call.=FALSE)
  method<-get(mk[[1]],envir=a,inherits=FALSE)
  check_complete_source_method(method)
  # Closing each append persists a fixed, label-free phase marker.
  cat("METHOD_VALIDATED_BEFORE_OTU_LOAD\n",file=stage_path,append=TRUE)
  cat("OTU_LOAD_STARTED\n",file=stage_path,append=TRUE)
  ok<-tryCatch(load(otu_path,envir=b),error=function(e)
              stop("SOURCE_OTU_RDA_PARSE_STOP",call.=FALSE))
  cat("OTU_DESERIALIZED_SCHEMA_ONLY\n",file=stage_path,append=TRUE)
  inspect_otu(method,b,ok)
}
synthetic <- function() {
  d<-expand.grid(round=1:6,state=1:3,site=1:40,KEEP.OUT.ATTRS=FALSE)
  patch<-(d$site-1)*3+d$state
  # The excluded first triplet has two complete six-record patches.
  # Twelve missing rounds belong to the retained population only.
  d<-d[!(patch==1 | (patch %in% 4:15 & d$round==6)),,drop=FALSE]
  stopifnot(nrow(d)==702L)
  m<-data.frame(triplet=paste0("PRIVATE_SITE_",d$site),
    plot=paste0("PRIVATE_PATCH_",d$state),
    treatment=paste0("PRIVATE_TREATMENT_",d$state),
    offset=rep(1.5,702),sample_id=sprintf("PRIV_SAMPLE_%04d",1:702),
    richness=rep(1000000,702),stringsAsFactors=FALSE)
  otu<-matrix(0,nrow=3,ncol=702,dimnames=list(
      c("PRIVATE_TAXON_A","PRIVATE_TAXON_B","PRIVATE_TAXON_C"),m$sample_id))
  e<-new.env(parent=baseenv())
  put<-function(x) assign("PRIVATE_ORIGINAL_OTU",x,envir=e)
  put(otu)
  z<-inspect_otu(m,e,ls(e))
  stopifnot(z$ready,z$exact_702_matches==1L,z$matched_39_retained==690L,
            z$matched_excluded_12==12L)
  # Exact identities remain valid under sample order and matrix orientation.
  otu<-otu[,rev(seq_len(702)),drop=FALSE];put(otu)
  z<-inspect_otu(m,e,ls(e))
  stopifnot(z$ready,z$objects[[1]][["n_rownames"]]==0L,
            z$objects[[1]][["n_colnames"]]==702L)
  put(t(otu));stopifnot(inspect_otu(m,e,ls(e))$ready)
  # Duplicate representations of the same key are harmless.
  m_same<-m;m_same$samplecode<-m$sample_id;put(otu)
  stopifnot(inspect_otu(m_same,e,ls(e))$ready)
  # Two different row-to-key assignments sharing a set are ambiguous.
  m_amb<-m;m_amb$samplecode<-rev(m$sample_id)
  stopifnot(!inspect_otu(m_amb,e,ls(e))$ready)
  # Both ordered and shuffled default row positions must be rejected.
  for (labels in list(as.character(1:702),as.character(702:1))) {
    mi<-m;mi$sample_id<-labels;rownames(mi)<-labels
    oi<-otu;colnames(oi)<-labels;put(oi)
    stopifnot(!inspect_otu(mi,e,ls(e))$ready)
  }
  # Missing explicit method keys cannot be replaced by row-order joining.
  m2<-m;m2$sample_id<-NULL;put(otu)
  stopifnot(!inspect_otu(m2,e,ls(e))$ready)
  # Duplicate/blank sample labels cannot certify one-to-one matching.
  for (replacement in list(colnames(otu)[1],"",NA_character_)) {
    oi<-otu;colnames(oi)[2]<-replacement;put(oi)
    stopifnot(!inspect_otu(m,e,ls(e))$ready)
  }
  # Unknown objects and two possible sample axes require schema HOLD.
  put(matrix(vector("list",702),1,702,dimnames=list(NULL,m$sample_id)))
  stopifnot(isTRUE(inspect_otu(m,e,ls(e))$schema_hold))
  alien<-otu;class(alien)<-c("alien","matrix","array");put(alien)
  stopifnot(isTRUE(inspect_otu(m,e,ls(e))$schema_hold))
  # A plain data.frame row accessor must not evaluate the other axis names.
  odf<-as.data.frame(t(otu));put(odf)
  invisible(capture.output(suppressMessages(trace("dimnames.data.frame",
    where=baseenv(),print=FALSE,tracer=quote({
      if (ncol(x)==3L) stop("NONCANDIDATE_AXIS_ACCESS",call.=FALSE)
    })))))
  df_ready<-tryCatch(inspect_otu(m,e,ls(e))$ready,
    finally=invisible(capture.output(suppressMessages(
      untrace("dimnames.data.frame",where=baseenv())))))
  stopifnot(isTRUE(df_ready))
  put(otu);assign("PRIVATE_EXTRA",list(1),envir=e)
  stopifnot(isTRUE(inspect_otu(m,e,ls(e))$schema_hold),
            !inspect_otu(m,e,ls(e))$ready)
  rm("PRIVATE_EXTRA",envir=e)
  put(matrix(0,702,702,dimnames=list(m$sample_id,m$sample_id)))
  stopifnot(isTRUE(inspect_otu(m,e,ls(e))$schema_hold))
  put(matrix(0,1,150001))
  oversized<-inspect_otu(m,e,ls(e))
  stopifnot(isTRUE(oversized$schema_hold),oversized$loaded_otu_object_count==1L,
            length(oversized$objects)==0L)
  many<-new.env(parent=baseenv())
  for(i in 1:13) assign(paste0("PRIVATE_OBJECT_",i),matrix(0,1,1),envir=many)
  overcount<-inspect_otu(m,many,ls(many))
  stopifnot(isTRUE(overcount$schema_hold),overcount$loaded_otu_object_count==13L,
            length(overcount$objects)==0L)
  # Coarse 39/690/119 totals alone do not qualify the fixed population.
  must_stop<-function(mm) {
    stopped<-tryCatch({check_complete_source_method(mm);FALSE},
                       error=function(err) TRUE)
    stopifnot(stopped)
  }
  bad<-m
  ix<-which(bad$triplet=="PRIVATE_SITE_2" & bad$plot=="PRIVATE_PATCH_1")[1]
  bad$triplet[ix]<-"PRIVATE_SITE_3";must_stop(bad)
  bad<-m;bad$triplet[bad$triplet=="PRIVATE_SITE_1"]<-" ";must_stop(bad)
  bad<-m
  ix<-bad$triplet=="PRIVATE_SITE_2" & bad$treatment=="PRIVATE_TREATMENT_1"
  bad$treatment[ix]<-"PRIVATE_TREATMENT_FOURTH";must_stop(bad)
  bad<-m
  ix<-which(bad$triplet=="PRIVATE_SITE_1" & bad$plot=="PRIVATE_PATCH_2")[1]
  bad$plot[ix]<-"PRIVATE_PATCH_3";must_stop(bad)
  # Real save/load roundtrip on artificial data exercises the phase markers.
  tmp<-tempfile("synthetic_identity_");dir.create(tmp)
  on.exit(unlink(tmp,recursive=TRUE),add=TRUE)
  mp<-file.path(tmp,"diversity_satellite.rda")
  op<-file.path(tmp,"otu_matrix.rda")
  sp<-file.path(tmp,"stage")
  save(m,file=mp);save(otu,file=op)
  loaded<-read_original(mp,op,sp)
  stages<-c("METHOD_VALIDATED_BEFORE_OTU_LOAD","OTU_LOAD_STARTED",
            "OTU_DESERIALIZED_SCHEMA_ONLY")
  stopifnot(loaded$ready,identical(readLines(sp),stages))
  unlink(c(sp,op));bad<-m[-1,,drop=FALSE];save(bad,file=mp)
  err<-tryCatch({read_original(mp,op,sp);"NO_ERROR"},
                error=function(e) conditionMessage(e))
  stopifnot(identical(err,"SOURCE_METHOD_OBJECT_POPULATION_DRIFT"),
            !file.exists(sp))
  save(m,file=mp)
  err<-tryCatch(suppressWarnings({read_original(mp,op,sp);"NO_ERROR"}),
                error=function(e) conditionMessage(e))
  stopifnot(identical(err,"SOURCE_OTU_RDA_PARSE_STOP"),
            identical(readLines(sp),stages[1:2]))
  # Exercise the actual output boundary with sentinel private names.
  out<-capture.output(emit(z))
  stopifnot(!any(grepl("PRIVATE_|PRIV_|1000000",out)),
            out[[1]]=="KORTMANN_OTU_ID_SCHEMA_V1")
  cat(paste(out,collapse="\n"),"\n",sep="")
  cat("SYNTHETIC_KORTMANN_OTU_SAMPLE_ID_ONLY_NO_COUNTS_PASS\n")
}
args<-commandArgs(trailingOnly=TRUE)
if (length(args)==1L && args[[1]]=="--synthetic") {
  synthetic()
} else if(length(args)==3L) {
  emit(read_original(args[[1]],args[[2]],args[[3]]))
} else stop("USAGE_KORTMANN_OTU_METADATA_IDENTITY_ONLY",call.=FALSE)
