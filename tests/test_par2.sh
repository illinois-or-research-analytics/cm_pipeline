mprof run --include-children python3 ../cm.py \
        -n 16 \
        -i /shared/rsquared/cit_patents_cleaned.tsv \
        -c leiden \
        -d working_dir_test_simple2 \
        -g 0.01 \
        -t 1log10 \
        -e /shared/rsquared/cit_patents_leiden.5_nontree_n10_clusters.tsv \
        -o cit_patents_leiden.5_nontree_n10_clusters_cm_simple2.txt

mprof plot --flame