# script that reduces the size of a large graph to allow find_trees.py to run more efficiently.
# Updated to add annotations for stars
# George Chacko Jan 16, 2023

# usage "Rscript subset_graph.R  <parent_network> <input clustering file> <output_edgelist_string>
# parent_network: edgelist as tsv without headers
# input clustering file: node+id, cluster_id without headers
# output_edgelist_string: a text tag such as oc_l5_trimmed


## Example: Rscript subset_graph.R oc_integer_el.tsv oc_leiden.5.tsv oc_l5_trimmed

library(data.table)
library(feather)
rm(list=ls())

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("Three arguments must be supplied: parent_network, clustering, and output_text_tag ", call.=FALSE)
} else if (length(args)==3) {
  print("OK 3 params supplied")
}

# parent network
g <- fread(args[1])
# clustering
c <- fread(args[2])

# reduce clustering to those clusters of size 11 or greater
c_10 <- c[,.N,by='V2'][N>10]
# use node_ids from c_10 to subset clustering
sized_clusters <- c[V2 %in% c_10$V2]

# resize graph to only those edges where the endpoints map to the 
# clusters in sized_clusters

g1 <- g[(V1 %in% sized_clusters$V1) & (V2 %in% sized_clusters$V1)]

# add cluster info to each node in g1
temp <- merge(g1,sized_clusters,by.x='V1',by.y='V1')
colnames(temp) <- c('V1','V2','V1_clus')

temp2 <- merge(temp,sized_clusters,by.x='V2',by.y='V1')
colnames(temp2) <- c("V2","V1","V1_clus","V2_clus")

# enforce endpoints in same cluster
trimmed_g <- temp2[V1_clus==V2_clus]

# edge counts 
ec <- trimmed_g[,.N,by=c('V1_clus','V2_clus')][,.(cluster_id=V1_clus,edge_count=N)]

# merge with c_10 to get node counts
temp <- merge(c_10,ec,by.x='V2',by.y='cluster_id')
colnames(temp) <- c('cluster_id','node_count','edge_count')

#annotate for tree/non_tree
temp[node_count!=edge_count+1,type:='non_tree']
temp[node_count==edge_count+1,type:='tree']

# calculate degrees of nodes in trimmed_g
small_g <- trimmed_g[,.(V1,V2,cluster_id=V1_clus)]
# calculate indegree and outdegree
t1 <- small_g[,.N,by="V1"]
t2 <- small_g[,.N,by="V2"]
t1t2 <- merge(t1,t2,by.x='V1',by.y="V2",all.x=T,all.y=T)
# replace NAs with 0
t1t2[is.na(t1t2)] <-0
t1t2 <- t1t2[,.(node_id=V1,degree=N.x+N.y)]

# merge t1t2 with clustering data c_10 
t3 <- merge(t1t2, sized_clusters,by.x="node_id",by.y="V1")

# select maxdegree
# funky Arun Srinivasan expression for data.table
# https://stackoverflow.com/questions/24558328/select-the-row-with-the-maximum-value-in-each-group
t4 <- t3[t3[, .I[which.max(degree)], by=V2]$V1]

# merge into temp
t5 <- merge(temp,t4,by.x='cluster_id',by.y='V2')[,.(cluster_id,node_count,edge_count,max_deg=degree,type)]
# convert tree to star where applicable
t5[type=='tree' & max_deg==node_count-1,type :='star']

#write to tsv
write.table(t5,file=paste0(args[3],'_treestarcounts.tsv'),sep='\t',row.names=F)
# write trimmed graph
write_feather(trimmed_g,paste0(args[3],'_g.feather'))
# write trimmed clustering
write_feather(sized_clusters,paste0(args[3],'_clus.feather'))
