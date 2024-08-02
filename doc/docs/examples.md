# Example Commands

## Default CM:
CM under default settings of B = 11 and threshold = log base 10 of n where n is the number of nodes in the cluster, meaning remove tree clusters and clusters below size and also ensure that each cluster has a minimum edge cut size greater than the threshold.
  
- command:
```
python -m main pipeline.json
```

- pipeline.json:
  
```
{
    "title": <custom name for this run>,
    "name": <custom name of your network>,
    "input_file": <path to your network edgelist>,
    "output_dir": <output directory>,
    "algorithm": <clustering algorithm e.g., ikc, leiden, leiden_mod>,
    "params": [
        {
            <parameter name e.g., res, i>: <parameter value>
        }
    ],
    "stages": [
        {
            "name": "cleanup"
        },
        {
            "name": "clustering",
            "parallel_limit": 2
        },
        {
            "name": "stats",
            "parallel_limit": 2
        },
        {
            "name": "filtering",
            "scripts": [
                "./scripts/subset_graph_nonetworkit_treestar.R",
                "./scripts/make_cm_ready.R"
            ]
        },
        {
            "name": "connectivity_modifier",
            "memprof": <boolean for whether to profile memory e.g., true or false>,
            "threshold": <well-connectedness threshold e.g., 1log10>,
            "nprocs": <number of processors for parallelism>,
            "quiet": <boolean whether to print outputs to console e.g., true or false>
        },
        {
            "name": "filtering",
            "scripts": [
                "./scripts/post_cm_filter.R"
            ]
        },
        {
            "name": "stats",
            "parallel_limit": 2
        }
    ]
}
```

    
## CM without removing small clusters or tree-like clusters
  
  - command:
```
python -m main pipeline.json
```

  - pipeline.json:
    
```
{
    "title": <custom name for this run>,
    "name": <custom name of your network>,
    "input_file": <path to your network edgelist>,
    "output_dir": <output directory>,
    "algorithm": <clustering algorithm e.g., ikc, leiden, leiden_mod>,
    "params": [
        {
            <parameter name e.g., res, i>: <parameter value>
        }
    ],
    "stages": [
        {
            "name": "cleanup"
        },
        {
            "name": "clustering",
            "parallel_limit": 2
        },
        {
            "name": "stats",
            "parallel_limit": 2
        },
        {
            "name": "connectivity_modifier",
            "memprof": <boolean for whether to profile memory e.g., true or false>,
            "threshold": <well-connectedness threshold e.g., 1log10>,
            "nprocs": <number of processors for parallelism>,
            "quiet": <boolean whether to print outputs to console e.g., true or false>
        },
        {
            "name": "stats",
            "parallel_limit": 2
        }
    ]
}
```

## WCC (Well Connected Components)
This is equivalent to running CM pipeline with the pre and post filtering steps turned off and not applying clustering recursively. Equivalently, each cluster is repeatedly cut until it is well-connected. The user has the option of adding in the filtering steps if desired.
    
  - command:
```
python3 -m hm01.cm -i <input network edgelist path> -e <input existing clustering path> -o <output filepath> -c nop --threshold <threshold e.g., 1log10> --nprocs <number of processors>
```


## CC (Connected Components)
Some clustering methods produce disconnected clusters. CC will take such a clustering and returns the connected components of these clusters. The user has the option of adding in the filtering steps if desired.
    
  - command:
```
python3 -m hm01.cm -i <input network edgelist path> -e <input existing clustering path> -o <output filepath> -c nop --threshold 0.1 --nprocs <number of processors>
```

## Clustering methods that can be used with CM
CM currently enables the use of Leiden optimizing the constant Potts Model, Leiden optimizing under modularity, Iterative K-Core, Markov CLustering, Infomap, and Stochastic Block Models. Example for Stochastic Block Model shown below.
    
  - command:
```
python3 -m hm01.cm -i <input network edgelist path> -e <input existing clustering path> -o <output filepath> -c external -cfile <clusterer file path e.g., path to hm01/clusterers/external_clusterers/sbm_wrapper.py> --threshold <threhsold e.g., 1log10> --nprocs <number of processors>
```

  - cargs.json:

```
{
    <param key e.g., "block_state">: <param value e.g., "non_nested_sbm", "planted_partition_model">
    <param key 2 e.g., "degree_corrected">: <param value e.g. true, false>
}
```
