python3 ../cm.py \
        --quiet \
        -i /shared/rsquared/cen_cleaned.tsv \
        -c leiden \
        -g 0.01 \
        -t 1log10 \
        -e ~/cen_leiden.01_nontree_n10_clusters.tsv \
        -o cen_leiden.01_nontree_n10_clusters_cm.txt