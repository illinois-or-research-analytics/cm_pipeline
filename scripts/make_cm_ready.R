# script that reduces clustering to non-treeclusters and generates an edgelist that is compatible with CM

# usage "Rscript make_cm_ready.R <original clustering> <annotated_cluster_file> <user_specified_output_clustering.tsv>
# use the output of subset_graph_nonnetworkit_treestar.R
# which has the string "treestarcounts.tsv" suffixed in the filename

# **** Example: 
# Rscript make_cm_ready.R ../open_citations/oc_leiden.5.tsv  oc_leiden.5_annotated_treestarcounts.tsv oc_leiden.5_cm_ready.tsv
# ****

library(data.table)
rm(list=ls())

args = commandArgs(trailingOnly=TRUE)

# if (length(args)< 2) {
#   stop("At least two arguments must be supplied (input file).n", call.=FALSE)
# } 

# print(getwd())
# print(args[1])
# print(args[2])

if (length(args)==0) {
  stop("Three arguments must be supplied: parent_network, clustering, and output_text_tag ", call.=FALSE)
} else if (length(args)==3) {
  print("OK 3 params supplied")
}


x <- fread(args[2])

# filter out trees and stars
x <- x[type=='non_tree']

# probably unnecessary
set.seed(12345)

#import original clustering
original_clustering <- fread(args[1])
# subset clustering using clusters in sample
cm_ready_clustering <- original_clustering[V2 %in% x$cluster_id]

# write.table(x,file=paste0('non_tree_clustering_',args[2]),sep='\t',row.names=F,col.names=F)
# write.table(cm_ready_clustering,file=paste0('cm_ready_clustering_',args[2]),sep='\t',row.names=F,col.names=F)
write.table(cm_ready_clustering,file=args[3],sep="\t",row.names=F,col.names=F)
