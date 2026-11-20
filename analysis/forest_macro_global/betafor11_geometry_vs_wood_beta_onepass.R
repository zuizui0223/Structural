#!/usr/bin/env Rscript
# Original Rothacher BETA-FOR 99-patch one-pass, original author-corrected OTU
# incidence, landscape nesting, Simpson beta. Original biological source rows
# may be read only after the prior frozen original source and design passes.
# Raw IDs, OTU data, coordinates, sequences or patch-level effects NEVER exit.
# Protocol frozen in FOREST_MACRO_BETAFOR11_GEOMETRY_VS_WOOD_BETA_PRIMARY_FREEZE_20261120.md

halt <- function(code) stop(paste0("SCIENCE_STOP_", code), call.=FALSE)
site_order <- c("B04","B05","B06","B07","U01","U02","U03","P08","H09","S10","L11")
region_for_site <- c(B04="R1", B05="R1", B06="R1", B07="R1",
                     U01="R2", U02="R2", U03="R2", P08="R3",
                     H09="R4", S10="R5", L11="R6")
treatments <- c("CC", "AW","AL","AS","AB","DW","DL","DS","DB")
active_codes <- c("AW","AL","AS","AB","DW","DL","DS","DB")
wood_codes <- c("W","L","S","B")

b_sim <- function(a,b) {
  if (length(a)!=length(b)) halt("BETA_VECTOR_LENGTH_MISMATCH")
  if (anyNA(a) || anyNA(b)) halt("BETA_UNOBSERVED_PATCH")
  n.shared <- sum(a & b)
  n.only_a <- sum(a & !b)
  n.only_b <- sum(!a & b)
  denom <- n.shared + min(n.only_a,n.only_b)
  if (denom<=0) halt("BETA_SIM_UNESTIMABLE_ZERO_DENOMINATOR")
  min(n.only_a,n.only_b)/denom
}

forest_gwd <- function(named_comm) {
  if (!setequal(names(named_comm),active_codes)) halt("FOREST_TREATMENT_UNIVERSE_INCOMPLETE")
  canopy <- vapply(wood_codes,function(w) b_sim(named_comm[[paste0("A",w)]],
                                               named_comm[[paste0("D",w)]]),0.0)
  pairs <- combn(wood_codes,2)
  wood_a <- vapply(seq_len(ncol(pairs)),function(i) {
    v <- pairs[,i]
    b_sim(named_comm[[paste0("A",v[1])]],named_comm[[paste0("A",v[2])]])
  },0.0)
  wood_d <- vapply(seq_len(ncol(pairs)),function(i) {
    v <- pairs[,i]
    b_sim(named_comm[[paste0("D",v[1])]],named_comm[[paste0("D",v[2])]])
  },0.0)
  g <- mean(canopy)
  w <- (mean(wood_a)+mean(wood_d))/2
  c(G=g,W=w,D=g-w)
}

# Full author singletons estimator; R set.seed(1) globally ONCE.
singleton_correction <- function(mat) {
  set.seed(1)
  removed <- 0L
  changed <- 0L
  estimated_above_observed <- 0L
  for (j in seq_len(ncol(mat))) {
    counts <- mat[,j]
    positive <- counts[counts>0]
    os <- sum(positive==1)
    f2 <- sum(positive==2)
    f3 <- sum(positive==3)
    f4 <- sum(positive==4)
    if (f3==0L) f3 <- 1L
    if (f4==0L) f4 <- 1L
    x <- 2*f2^2/(3*f3)
    estimated <- round(x+max(0,x-f2*f3/(2*f4)))
    if (!is.finite(estimated) || estimated<0 || estimated>nrow(mat)*1e4) {
      halt("SINGLETON_ESTIMATE_NUMERIC_INVALID")
    }
    if (estimated>os) estimated_above_observed <- estimated_above_observed+1L
    if (estimated<os) {
      # Intentional exact original R sample(which(...), size=..., replace=F)
      # semantics, including global seed progression across sample columns.
      original_singletons <- which(counts==1)
      to_zero <- sample(original_singletons,size=os-estimated,replace=FALSE)
      mat[to_zero,j] <- 0
      removed <- removed+(os-estimated)
      changed <- changed+1L
    }
  }
  retained <- rowSums(mat)>0
  list(mat=mat[retained,,drop=FALSE], removed=removed, changed=changed,
       estimated_above_observed=estimated_above_observed,
       remaining_otus=sum(retained))
}

# Compute a patch-distance matrix once, then randomize the treatment labels
# only, preserving one 8-patch treatment universe inside each physical forest.
pair_indices <- rbind(t(combn(1:4,2)),t(combn(5:8,2)))
pair_g <- cbind(1:4,5:8)
mat_gwd <- function(betas,assignment=seq_len(8)) {
  g <- mean(betas[cbind(assignment[pair_g[,1]],assignment[pair_g[,2]])])
  w <- mean(betas[cbind(assignment[pair_indices[,1]],assignment[pair_indices[,2]])])
  c(G=g,W=w,D=g-w)
}

test_synthetic <- function() {
  one <- function(ix, n=8) seq_len(n)%in%ix
  a <- one(c(1,2)); b <- one(c(1,3))
  stopifnot(isTRUE(all.equal(b_sim(a,b),0.5)))
  stopifnot(isTRUE(all.equal(b_sim(one(c(1,2)),one(c(1,2,3))),0)))
  stopifnot(isTRUE(all.equal(b_sim(one(c(1)),one(c(2))),1)))
  # Geometry only: all A use one taxon, all D use a different taxon.
  positive <- setNames(vector("list",length(active_codes)),active_codes)
  for (nm in active_codes) positive[[nm]] <- one(if (substr(nm,1,1)=="A") 1 else 2)
  p <- forest_gwd(positive)
  stopifnot(isTRUE(all.equal(unname(p["G"]),1)),
            isTRUE(all.equal(unname(p["W"]),0)),
            isTRUE(all.equal(unname(p["D"]),1)))
  # Wood only: each wood channel has a distinct taxon, A/D share it.
  negative <- setNames(vector("list",length(active_codes)),active_codes)
  for (nm in active_codes) negative[[nm]] <- one(match(substr(nm,2,2),wood_codes))
  q <- forest_gwd(negative)
  stopifnot(isTRUE(all.equal(unname(q["G"]),0)),
            isTRUE(all.equal(unname(q["W"]),1)),
            isTRUE(all.equal(unname(q["D"]),-1)))
  null <- setNames(replicate(8,one(1),simplify=FALSE),active_codes)
  z <- forest_gwd(null)
  stopifnot(all(z==0))
  all.inc <- setNames(lapply(active_codes,function(nm) negative[[nm]]),active_codes)
  bm <- matrix(NA_real_,8,8)
  for (i in 1:8) for (j in 1:8) {
    bm[i,j] <- if(i==j) 0 else b_sim(all.inc[[i]],all.inc[[j]])
  }
  stopifnot(isTRUE(all.equal(unname(mat_gwd(bm)[["D"]]),unname(q[["D"]]))))
  # Frozen author's singleton formula: f2=1,f3=f4=1, os=10 -> es=1
  fixture <- matrix(c(rep(1,10),2,3,4,0),ncol=1)
  corrected <- singleton_correction(fixture)
  stopifnot(corrected$removed==9L,
            sum(corrected$mat>0)==4,
            corrected$changed==1L)
  cat("SYNTHETIC_BETAFOR11_GWD_KNOWNTRUTH_POS_NEG_NULL_SINGLETON_PASS\n")
}

as_key <- function(value) format(value, digits=16, scientific=FALSE, trim=TRUE)
out_write <- function(out,values) {
  if(any(grepl("[\n\t]",names(values)))) halt("RESULT_FIELD_NAME_UNSAFE")
  d <- data.frame(metric=names(values),value=unname(values),stringsAsFactors=FALSE)
  write.table(d,file=out,sep="\t",row.names=FALSE,col.names=TRUE,
              quote=FALSE,na="",fileEncoding="UTF-8")
}

main <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  if(identical(args, "--test")) {test_synthetic();return(invisible(NULL))}
  if(length(args)!=3L) halt("USAGE_METHOD_OTU_AND_SUMMARY_OUTPUT_REQUIRED")
  test_synthetic()
  method_file <- args[[1]]
  otu_file <- args[[2]]
  out <- args[[3]]

  # Do not treat the order of original OTU table rows as source species IDs.
  info <- read.delim(method_file, sep=";", header=TRUE, check.names=FALSE,
                     stringsAsFactors=FALSE,fileEncoding="UTF-8")
  if(!identical(names(info),c("patch","sample","firstday","lastday",
                             "meanday","treatment","X","Y"))) halt("METHOD_COLUMNS_CHANGED")
  if(nrow(info)!=594L || length(unique(info$patch))!=99L ||
     anyDuplicated(info$sample)>0 || anyDuplicated(info[c("patch","sample")])>0) {
    halt("METHOD_594_SAMPLE_99_PATCH_GRAMMAR_CHANGED")
  }
  info$site <- substr(info$patch,1,3)
  if(!setequal(unique(info$site),site_order) ||
     any(substr(info$patch,5,6)!=info$treatment)) halt("METHOD_SOURCE_TREATMENTS_DRIFT")
  by_patch <- split(info,info$patch)
  if(any(vapply(by_patch,nrow,0L)!=6L) ||
     any(vapply(by_patch,function(x) length(unique(x$treatment)),0L)!=1L)) {
    halt("METHOD_SOURCE_SIX_SAMPLE_OPPORTUNITIES_NOT_VERIFIED")
  }
  patch_meta <- info[!duplicated(info$patch),c("patch","site","treatment")]
  for (s in site_order) {
    treatments_here <- patch_meta$treatment[patch_meta$site==s]
    if(!setequal(treatments_here,treatments) || length(treatments_here)!=9L) {
      halt("METHOD_ORIGINAL_11_FOREST_9_TREATMENT_UNIVERSE_CHANGED")
    }
  }
  orig <- read.delim(otu_file,sep=";",header=TRUE,check.names=FALSE,
                     stringsAsFactors=FALSE,fileEncoding="UTF-8")
  if(ncol(orig)!=598L || nrow(orig)<1000L ||
     !identical(names(orig)[2:4],c("OTUNr","Family","Order")) ||
     !(names(orig)[1]%in%c("","X"))) halt("OTU_ORIGINAL_FOUR_META_ROLE_OR_DIMENSION_DRIFT")
  original_otu_id <- as.character(orig[["OTUNr"]])
  if(anyNA(original_otu_id) || any(!nzchar(original_otu_id)) ||
     anyDuplicated(original_otu_id)>0) halt("OTU_SOURCE_ID_DUPLICATE_OR_EMPTY")
  measurement_names <- names(orig)[5:598]
  if(anyDuplicated(measurement_names)>0 ||
     !setequal(measurement_names,info$sample)) halt("OTU_594_SAMPLE_LABEL_LINKAGE_CHANGED")
  data <- orig[,5:598,drop=FALSE]
  if(!all(vapply(data,is.numeric,FALSE))) halt("OTU_ORIGINAL_COUNT_COLUMN_NONNUMERIC")
  mat <- as.matrix(data)
  rm(data,orig)
  if(anyNA(mat) || any(!is.finite(mat)) || any(mat<0) ||
     any(mat!=round(mat))) halt("OTU_SOURCE_NA_NEGATIVE_OR_NONINTEGER_COUNTS")
  sample_sums <- colSums(mat)
  if(any(sample_sums<=0)) halt("OTU_SOURCE_ZERO_SEQUENCE_DEPTH_SAMPLES")
  original_otu_count <- nrow(mat)
  original_total_reads <- sum(sample_sums)
  corrected <- singleton_correction(mat)
  mat <- corrected$mat
  singleton_removed <- corrected$removed
  singleton_changed <- corrected$changed
  rm(corrected)
  if(nrow(mat)<100L) halt("OTU_SOURCE_TOO_FEW_CORRECTED_TAXA")
  patch_names <- patch_meta$patch
  n_t <- nrow(mat)
  patch_inc <- matrix(FALSE,nrow=n_t,ncol=99L)
  patch_reads <- numeric(99L)
  patch_detected <- integer(99L)
  for(i in seq_along(patch_names)) {
    sid <- info$sample[info$patch==patch_names[[i]]]
    j <- match(sid,measurement_names)
    if(length(j)!=6L || anyNA(j)) halt("OTU_CORRECTED_SAMPLE_PATCH_KEY_MISSING")
    patch_inc[,i] <- rowSums(mat[,j,drop=FALSE]>0)>0
    patch_reads[i] <- sum(sample_sums[j])
    patch_detected[i] <- sum(patch_inc[,i])
  }
  if(any(patch_detected<5L)) halt("OTU_PATCH_LT_FIVE_DETECTED_AFTER_AUTHOR_SINGLETON")
  rm(mat)
  forest_g <- forest_w <- forest_d <- numeric(length(site_order))
  all_pair_mat <- vector("list",length(site_order))
  names(forest_d) <- names(forest_g) <- names(forest_w) <- site_order
  for (i in seq_along(site_order)) {
    site <- site_order[[i]]
    df <- patch_meta[patch_meta$site==site,]
    ids <- match(df$patch,patch_names)
    cmeta <- setNames(lapply(seq_along(ids),function(j) patch_inc[,ids[[j]]]),df$treatment)
    if(!setequal(names(cmeta),treatments)) halt("FOREST_SOURCE_TREATMENT_ROLE_DRIFT")
    cc <- cmeta[active_codes]
    actual <- forest_gwd(cc)
    forest_g[[i]] <- actual[["G"]]
    forest_w[[i]] <- actual[["W"]]
    forest_d[[i]] <- actual[["D"]]
    bet <- matrix(0,8,8)
    for (j in 1:7) for(k in (j+1):8) {
      bet[j,k] <- b_sim(cc[[j]],cc[[k]])
      bet[k,j] <- bet[j,k]
    }
    if(abs(mat_gwd(bet)[["D"]]-forest_d[[i]])>1e-10) {
      halt("INDEPENDENT_MATRIX_COMPARATOR_INCONSISTENT")
    }
    all_pair_mat[[i]] <- bet
  }
  names(all_pair_mat) <- site_order
  mean_by_region <- function(values) {
    unname(vapply(paste0("R",1:6),function(r) {
      keys <- site_order[region_for_site[site_order]==r]
      mean(values[keys])
    },0.0))
  }
  region_d <- mean_by_region(forest_d)
  region_g <- mean_by_region(forest_g)
  region_w <- mean_by_region(forest_w)
  primary <- mean(region_d)
  sign_flips <- as.matrix(expand.grid(rep(list(c(-1,1)),6)))
  flipped <- as.vector(sign_flips %*% region_d)/6
  exact_p <- mean(abs(flipped)>=(abs(primary)-1e-12))
  set.seed(20261120)
  draws <- replicate(4000L,mean(sample(region_d,size=6,replace=TRUE)))
  ci <- as.numeric(quantile(draws,c(0.025,0.975),names=FALSE,type=7))
  # Source treatment-label permutation: independent of R singleton seed.
  set.seed(20261121)
  perm <- numeric(999L)
  for(t in seq_along(perm)) {
    d <- numeric(length(site_order))
    names(d) <- site_order
    for (i in seq_along(site_order)) {
      d[[i]] <- mat_gwd(all_pair_mat[[i]],assignment=sample(1:8,8))[[ "D" ]]
    }
    perm[[t]] <- mean(mean_by_region(d))
  }
  perm_p <- (1+sum(abs(perm)>=abs(primary)-1e-12))/(length(perm)+1)

  # Source sample read-depth imbalance: indicates observational caveat, not a
  # post-outcome filter. No sample, patch, forest or OTU IDs exported.
  sample_canopy <- substr(info$treatment,1,1)
  sample_read_depth <- sample_sums[match(info$sample,measurement_names)]
  mean_a <- mean(sample_read_depth[sample_canopy=="A"])
  mean_d <- mean(sample_read_depth[sample_canopy=="D"])
  supported <- (primary!=0 && ci[[1]]*ci[[2]]>0 && exact_p<0.05)
  result <- c(
    status=if(supported) "EXPLORATORY_REGION_EQUAL_GWD_DIRECTIONALLY_SUPPORTED" else
                       "EXPLORATORY_REGION_EQUAL_GWD_NOT_SUPPORTED",
    original_counted_OTU_rows=as_key(original_otu_count),
    original_author_singleton_corrected_OTU_rows=as_key(n_t),
    original_sample_columns=as_key(length(measurement_names)),
    original_patches=as_key(length(patch_names)),
    original_parent_forests=as_key(length(site_order)),
    original_geographic_regions="6",
    original_OTU_total_read_counts=as_key(original_total_reads),
    author_singleton_correction_removed_counts=as_key(singleton_removed),
    author_singleton_correction_changed_samples=as_key(singleton_changed),
    original_patch_corrected_detected_OTU_min=as_key(min(patch_detected)),
    original_patch_corrected_detected_OTU_median=as_key(median(patch_detected)),
    original_patch_corrected_detected_OTU_max=as_key(max(patch_detected)),
    original_sample_raw_readdepth_median=as_key(median(sample_sums)),
    original_A_sample_mean_readdepth=as_key(mean_a),
    original_D_sample_mean_readdepth=as_key(mean_d),
    primary_region_equal_G_simpson=as_key(mean(region_g)),
    primary_region_equal_W_simpson=as_key(mean(region_w)),
    primary_region_equal_D_geometry_minus_wood=as_key(primary),
    six_region_mean_D_sorted_anonymous=paste(vapply(sort(region_d),as_key,""),collapse=","),
    forest_equal_D_secondary=as_key(mean(forest_d)),
    forest_positive_D_count=as_key(sum(forest_d>0)),
    forest_negative_D_count=as_key(sum(forest_d<0)),
    forest_zero_D_count=as_key(sum(forest_d==0)),
    region_positive_D_count=as_key(sum(region_d>0)),
    region_negative_D_count=as_key(sum(region_d<0)),
    region_zero_D_count=as_key(sum(region_d==0)),
    six_region_exact_signed_two_sided_p=as_key(exact_p),
    six_region_bootstrap_4000_CI_lower=as_key(ci[[1]]),
    six_region_bootstrap_4000_CI_upper=as_key(ci[[2]]),
    within_forest_999_label_permutation_2sided_p=as_key(perm_p),
    original_source_6_samples_each_patch="true",
    original_source_Simpson_replacement_not_total_Sorensen="true",
    biological_response_source_row_values_EXPORTED="false",
    original_OTU_species_and_patch_IDs_EXPORTED="false",
    all_prior_biological_results_unmodified="true",
    not_an_independent_cross_biome_replication="true"
  )
  out_write(out,result)
  cat("BETAFOR11_ONEPASS_ECOLOGICAL_RESULT:",unname(result[["status"]]),"\n")
  cat("PRIMARY_REGION_EQUAL_GWD:",unname(result[["primary_region_equal_D_geometry_minus_wood"]]),"\n")
  cat("EXACT_SIX_REGION_P:",unname(result[["six_region_exact_signed_two_sided_p"]]),"\n")
  cat("ORIGINAL_SOURCE_IDS_AND_OTU_ROWS_NOT_EXPORTED\n")
}

tryCatch(main(),error=function(e) {
  message(conditionMessage(e))
  quit(save="no",status=2L)
})
