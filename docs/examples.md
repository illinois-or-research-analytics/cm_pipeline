# Example Commands

## CM++

- `python3 -m hm01.cm -i network.tsv -e clustering.tsv -o output.tsv -c leiden -g 0.5 --threshold 1log10 --nprocs 4 --quiet`
  - Runs CM++ on a Leiden with resolution 0.5 clustering with connectivity threshold $log_{10}(n)$ (Every cluster with connectivity over the log of the number of nodes is considered "well-connected")
- `python3 -m hm01.cm -i network.tsv -e clustering.tsv -o output.tsv -c ikc -k 10 --threshold 1log10 --nprocs 4 --quiet`
  - Similar idea but with IKC having hyperparameter $k=10$.

## CM Pipeline

- Then from the root of this repository run:
  - `python -m main pipeline.json`
