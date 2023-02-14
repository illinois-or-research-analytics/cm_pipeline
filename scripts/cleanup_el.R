# script to remove duplicate rows, parallel edges, and self-loops from
# an edge list that is read in using fread into a dataframe
# Input format should be two columns csv, tsv, or whitespace separated
# George Chacko 12/20/2022
# Updated 2/13/2023

## usage Rscript cleanup_el.R <input edgelist> <user_specified_output_edgelist_name.tsv>
## # output defaults to default.tsv

rm(list=ls())
library(data.table)
args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
} else if (length(args)==1) {
  # default output file
  args[2] = "default.tsv"
}

df <- fread(args[1])
print(paste('Orig Rows:',dim(df)[1]))

# remove duplicate edges
df <- unique(df)
print(paste('Minus Duplicates:',dim(df)[1]))

# remove self loops
df <- df[!V1==V2]
print(paste('Minus Selfloops:',dim(df)[1]))

# remove parallel edges
df[,less:=pmin(V1,V2)]
df[,more:=pmax(V1,V2)]
y <- df[,.N,by=c('less','more')][N>1][,.(less,more)]
dups <- merge(df,y,by.x=c('V1','V2'),by.y=c('less','more'))[,.(V1,V2)]
w=sort(df[dups, on=.(V1,V2), which=TRUE, nomatch=0])
df <- df[!w][,.(V1,V2)]
print(paste('Minus Parallel Edges:',dim(df)[1]))

# fwrite(df, file=args[2], row.names=FALSE)
write.table(df, file=args[2], sep="\t", col.names = F, row.names = F)




