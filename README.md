# CM++ Pipeline

[![DOI](https://joss.theoj.org/papers/10.21105/joss.06073/status.svg)](https://doi.org/10.21105/joss.06073)
[![DOI](https://zenodo.org/badge/599799149.svg)](https://zenodo.org/doi/10.5281/zenodo.10076513)

Customizable modular pipeline for testing an improved version of CM for generating well-connected clusters. Image below from arXiv preprint: Park et. al. (2023). https://github.com/illinois-or-research-analytics/cm_pipeline/tree/main

- [CM++ Pipeline](#cm-pipeline)
  - [Documentation](#documentation)
  - [Overview](#overview)
    - [Main Features](#main-features)
    - [CM Pipeline Overview](#cm-pipeline-overview)
    - [CM++ Overview](#cm-overview)
    - [Requirements](#requirements)
    - [Installation and Setup](#installation-and-setup)
      - [Installation via Cloning](#installation-via-cloning)
      - [Installation via pip install](#installation-via-pip-install)
  - [Example Commands](#example-commands)
    - [CM++](#cm)
    - [CM Pipeline](#cm-pipeline-1)
  - [For Developers](#for-developers)
    - [Loading a Developer Environment](#loading-a-developer-environment)
    - [Customizing the Pipeline](#customizing-the-pipeline)
  - [Manuscript Data](#manuscript-data)
  - [Output Files](#output-files)
  - [Archive](#archive)
  - [Citations](#citations)

![cm_pipeline Overview](figures/cm_pp_overview.png)

## Documentation

For the full documentation see [here](https://illinois-or-research-analytics.github.io/cm_pipeline/)

## Overview

### Main Features
By default, CM modifies an input clustering to ensure that each cluster is well-connected. CM does this by doing rounds of mincut and clustering. It is also possible to run CM in a way that does not recursively cluster (CC and WCC).

#### Default CM:
CM under default settings (remove small clusters and tree-like clusters with B=10 and threshold= $\log_{10}{n}$ )
<details>
<summary><sub>Click to expand example command </sub></summary>
  
- command: `python -m main pipeline.json`
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
</details>
    
#### CM without removing small clusters or tree-like clusters
  <details>
  <summary><sub>Click to expand example command </sub></summary>
  
  - command: `python -m main pipeline.json`
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
  </details>

#### WCC
Only obtain well-connected components without re-clustering
  <details>
  <summary><sub>Click to expand example command </sub></summary>
    
  - command: `python3 -m hm01.cm -i <input network edgelist path> -e <input existing clustering path> -o <output filepath> -c nop --threshold <threshold e.g., 1log10> --nprocs <number of processors>`
  </details>

#### CC
Only obtain connected components
  <details>
  <summary><sub>Click to expand example command </sub></summary>
    
  - command: `python3 -m hm01.cm -i <input network edgelist path> -e <input existing clustering path> -o <output filepath> -c nop --threshold 0.1 --nprocs <number of processors>`
  </details>


### CM Pipeline Overview

The CM Pipeline is a modular pipeline for community detection that contains the following modules:

- **Graph Cleaning**: Removal of parallel and duplicate edges as well as self loops

- **Community Detection**: Clusters an input network with one of Leiden, IKC, and InfoMap. 

- **Cluster Filtration**: A pre-processing stage that allows users to filter out clusters that are trees or have size below a given threshold.

- **Community Statistics Reporting**: Generates node and edge count, modularity score, Constant Potts Model score, conductance, and edge-connectivity at multiple stages.

- **Extensibility**: Developers can design new stages and wire in new algorithms. Please see [the following document](pipeline_customization.md) for instructions on how to expand the list of supported clustering algorithms as a developer.

- **CM++**

### CM++ Overview

CM++ is a module within the CM Pipeline, having the following features:

- **Function**: CM++ refines your existing graph clustering by carving them into well-connected clusters with high minimum cut values.

- **Flexibility**: Users can accompany their definition of a good community with well-connectedness. CM++ works with any clustering algorithm and presently provides build in support for Leiden, IKC, and Infomap.

- **Dynamic Thresholding**: Connectivity thresholds can be constants, or functions of the number of nodes in the cluster, or the minimum node degree of the cluster.

- **Multi-processing**: For better performance, users can specify a larger number of cores to process clusters concurrently.

### Requirements

- MacOS or Linux operating system
- `python3.9` or higher (**UPDATE: We are looking into adding support for python3.12. For the time being, please use 3.9<=python<=3.11**)
- `cmake 3.2.0` or higher
- `gcc@10` or higher
- `R` with the following packages:
  -  `data.table`
  -  `feather`

### Installation and Setup

There are several strategies for installation

#### Installation via Cloning

- Clone the cm_pipeline repository
- Activate the venv which has the necessary packages
- Run `pip install -r requirements.txt && pip install .`
- Make sure everything installed properly by running `cd tests && pytest`

#### Installation via pip install

Simply run `pip install git+https://github.com/illinois-or-research-analytics/cm_pipeline`. **This will install CM++, but to use pipeline functionality, please setup via cloning.**

## Example Commands

### CM++

- `python3 -m hm01.cm -i network.tsv -e clustering.tsv -o output.tsv -c leiden -g 0.5 --threshold 1log10 --nprocs 4 --quiet`
  - Runs CM++ on a Leiden with resolution 0.5 clustering with connectivity threshold $log_{10}(n)$ (Every cluster with connectivity over the log of the number of nodes is considered "well-connected")
- `python3 -m hm01.cm -i network.tsv -e clustering.tsv -o output.tsv -c ikc -k 10 --threshold 1log10 --nprocs 4 --quiet`
  - Similar idea but with IKC having hyperparameter $k=10$.
- `python3 -m hm01.cm -i network.tsv -e clustering.tsv -o output.tsv -c nop --threshold 0.1 --nprocs 4 --quiet`
  - Similar idea but with a nop clusterer, meaning it won't recursively cluster, and only ensure that every cluster is connected. This is sometimes called CM-cc or just -cc for short.
- `python3 -m hm01.cm -i network.tsv -e clustering.tsv -o output.tsv -c nop --threshold 1log10 --nprocs 4 --quiet`
  - Similar idea but with a nop clusterer, meaning it won't recursively cluster, and only ensure that every cluster is well-connected by performing repeated mincuts. This is sometimes called CM-wcc or just -wcc for short.

### CM Pipeline

- Suppose you have a pipeline like the one [here](examples/leiden.json). Call it `pipeline.json`
- Then from the root of this repository run:
  - `python -m main pipeline.json`

## For Developers

### Loading a Developer Environment

To quickly set up a developer environment for the CM++ Pipeline, simply run the following commands. (**NOTE: Make sure you have Conda installed**)

```bash
conda env create -f environment.yml
conda activate 
```

### Customizing the Pipeline

- The CM++ Pipeline also allows for users to add their own pipeline stages and clustering methods.
- Please refer to the [customization documentation](docs/pipeline_customization.md) on how to modify the code to allow for your own pipeline stages and .

## Manuscript Data

The data used to generate the speedup curve in the manuscript can be found in the [Illinois Databank](https://databank.illinois.edu/datasets/IDB-0908742). In all runs, we followed the command:

```python3 -m hm01.cm -i (network file) -e (clustering file) -t 1log10 -g 0.001 -c leiden -q -n (1|2|4|8|16|32)```

- CEN: cen_pipeline.tar.gz
  - Network: cen_cm_quiet_pipeline/cen-cm-new-pp-output-20230227-22:50:52/S1_cen_cleaned.tsv
  - Clustering: cen_cm_quiet_pipeline/cen-cm-new-pp-output-20230227-22:50:52/res-0.001/S2_cen_leiden.0.001.tsv
- CIT_Patents: cit_patents_networks.tar.gz
  - Network: cit_patents_processed_cm/cit_patents_cleaned.tsv
  - Clustering: cit_patents_processed_cm/cit_patents_leiden.001.tsv
- Orkut:
  - [Network](https://doi.org/10.6084/m9.figshare.24859140.v1)
  - [Clustering](https://doi.org/10.6084/m9.figshare.24860562.v1)

## Output Files

- The commands executed during the workflow are captured in `{output_dir}/{run_name}-{timestamp}/commands.sh`. This is the shell script generated by the pipeline that is run to generate outputs.
- The output files generated during the workflow are stored in the folder `{output_dir}/{run_name}-{timestamp}/`
- The descriptive analysis files can be found in the folder `{output_dir}/{run_name}-{timestamp}/analysis` with the `*.csv` file for each of the resolution values.

## Archive

- [View Old Release Notes](https://github.com/illinois-or-research-analytics/cm_pipeline/releases)

## Citations

If you use CM++ in your research, please use the following citation:

```bibtex
@article{Ramavarapu2024,
  doi = {10.21105/joss.06073},
  url = {https://doi.org/10.21105/joss.06073},
  year = {2024},
  publisher = {The Open Journal},
  volume = {9},
  number = {93},
  pages = {6073},
  author = {Vikram Ramavarapu and Fábio Jose Ayres and Minhyuk Park and Vidya Kamath Pailodi and João Alfredo Cardoso Lamy and Tandy Warnow and George Chacko},
  title = {CM++ - A Meta-method for Well-Connected Community Detection},
  journal = {Journal of Open Source Software}
}
```

### Other Citations

```bibtex
@software{vikram_ramavarapu_2024_10501118,
  author={Vikram Ramavarapu and Fabio Jose Ayres and Minhyuk Park and Vidya Kamath P and João Alfredo Cardoso Lamy and Tandy Warnow and George Chacko},
  title={{CM++ - A Meta-method for Well-Connected Community Detection}},
  month=jan,
  year=2024,
  publisher={Zenodo},
  version={v4.0.1},
  doi={10.5281/zenodo.10501118},
  url={https://doi.org/10.5281/zenodo.10501118}
}

@misc{park2023wellconnected,
  title={Well-Connected Communities in Real-World and Synthetic Networks}, 
  author={Minhyuk Park and Yasamin Tabatabaee and Vikram Ramavarapu and Baqiao Liu and Vidya Kamath Pailodi and Rajiv Ramachandran and Dmitriy Korobskiy and Fabio Ayres and George Chacko and Tandy Warnow},
  year={2023},
  eprint={2303.02813},
  archivePrefix={arXiv},
  primaryClass={cs.SI}
}

@misc{cm2022,
  author = {Baqiao Liu and Minhyuk Park},
  title = {Connectivity Modifier},
  howpublished = {\url{https://github.com/RuneBlaze/connectivity-modifier}},
  year={2022},
}
```
