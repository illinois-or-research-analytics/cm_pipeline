# script that filters out small clusters after cm
# Apr 10, 2024 added a line to enforce utf8 before group and count operations, 
# which otherwise affects clusterIDs with trailing deltas. => "enc2utf8(V2)]"

## Example: Rscript postcm_filter.R post_cm_file.tsv output_file.tsv

library(data.table)
rm(list=ls())

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("Two arguments must be supplied: post_cm_file.tsv output_file.tsv", call.=FALSE)
} else if (length(args)==2) {
  print("OK 2 params supplied")
}

# Check the file size
file_size <- file.info(args[1])$size

if (file_size == 0) {
  stop("Error: Clustering is empty.")
}

# read in post-cm clustering
c <- fread(args[1], colClasses=list(character=2), encoding="UTF-8")
# convert V2 to UTF-8
# c[,V2 := enc2utf8(V2)]

# identify clusters of size 11 or greater
c_10 <- c[,.N,by='V2'][N>10]

# trim output to clusters of size 11 or greater
c <- c[V2 %in% c_10$V2]

#write to tsv
write.table(c,file=args[2],sep='\t',row.names=F,col.names=F, quote=FALSE)
