python3 ../cm.py \
        --quiet \
        -i /data3/chackoge/modularity_clustering/cen_cleaned.tsv \
        -c leiden \
        -d working_dir_test2 \
        -g 0.0001 \
        -t 1log10 \
        -e /data3/vikramr2/benchmarks/S3.2_cm_ready_cen_leiden.0.0001_i2_nontree_n10.tsv \
        -o cen_leiden.01_nontree_n10_clusters_cm.txt