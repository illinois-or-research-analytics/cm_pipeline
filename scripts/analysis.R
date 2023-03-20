
## usage Rscript analysis_el.R <cleaned_edge_list> <user-specified-analyis.csv> <file_1.tsv> <file_2.tsv> ...<file_n.tsv>
## tsv files without header and containing two columns, node_id and cluster_id
rm(list=ls())
library(data.table)
args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("At least three arguments must be supplied: parent_network_cleaned.tsv user-specified-analysis.csv file_1.tsv", call.=FALSE)
} else if (length(args)==3) {
  print("OK 3 params supplied")
}

# read parent_network_cleaned.tsv
dt_workaround <- function(edgelist) {
x <- fread(edgelist)
dt1 <- x[,.(V1)]
dt2 <- x[,.(V2)]
dt1 <- unique(dt1)
dt2 <- unique(dt2)
dt3 <- rbind(dt1,dt2,use.names=FALSE)
nc_denom <-  dt3[,uniqueN(V1)]
return(nc_denom)
}
nc_denom <- dt_workaround(args[1])

# list of all tsv files to analyse
algo_res <- tail(args, -2)
algo_list_res <- list()
for (i in 1:length(algo_res)) {
    algo_list_res[[i]] <- fread(algo_res[i])
 }

# get only the .tsv base file names by removing the file paths
names(algo_list_res) <- lapply(algo_res, FUN=function(x) tail(strsplit(x, "/")[[1]], 1))
t <- lapply(algo_list_res, FUN=function(x) x[,.N,by='V2'][N>1,.(cc=length(N),nc=sum(N)/nc_denom,count=sum(N),min=min(N),med=median(N),max=max(N))])
t <- cbind(names(t),rbindlist(t))[,.(Rx=V1,clus_ct=cc,node_cov=round(100*nc,1),node_count=count,min,med,max)]
write.table(t, file=args[2], sep=",", col.names=TRUE, row.names=F)

