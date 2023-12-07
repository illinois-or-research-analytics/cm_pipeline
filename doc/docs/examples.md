# Example Commands

## CM++

```bash
python3 -m hm01.cm 
  -i network.tsv 
  -e clustering.tsv 
  -o output.tsv 
  -c leiden 
  -g 0.5 
  -t 1log10 
  --nprocs 4 
  --quiet
```

- Runs CM++ on a Leiden with resolution 0.5 clustering with connectivity threshold `log10(n)` (Every cluster with connectivity over the log of the number of nodes `n` is considered "well-connected")

```bash
python3 -m hm01.cm 
  -i network.tsv 
  -e clustering.tsv 
  -o output.tsv 
  -c ikc
  -k 10 
  -t 1log10 
  --nprocs 4 
  --quiet
```

- Similar idea but with IKC having hyperparameter `k=10`.

## CM Pipeline

- Suppose we have a network and a clustering
    - [network.tsv](network.tsv)
    - [clustering.tsv](clustering.tsv)
- We can then construct the following `pipeline.json`:
```json
{
    "title": "example",
    "name": "example",
    "input_file": "network.tsv",
    "output_dir": "samples/",
    "algorithm": "leiden",
    "params": [{
        "res": 0.5,
        "i": 2,
        "existing_clustering": "clustering.tsv"
    }],
    "stages": [
        {
            "name": "connectivity_modifier",
            "memprof": false,
            "threshold": "1log10",
            "nprocs": 1,
            "quiet": true
        }
    ]
}
```
- Then from the root of this repository run:
    - `python -m main pipeline.json`
