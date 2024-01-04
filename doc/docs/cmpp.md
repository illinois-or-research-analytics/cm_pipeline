# CM++ Usage

## Basic Usage

``` bash
python -m hm01.cm
  -i {input network}
  -e {existing clustering (optional)}
  -c {clustering algorithm}
  -t {connectivity threshold}
  -n {number of processors (optional)}
  -o {output file}
```

- **`-i` Input Network**: The input .tsv edgelist filename.
- **`-e` Existing Clustering**: The existing clustering filename. This is a .tsv with each line being 'node_id cluster_id' format. If this isn't provided, CM++ will run an initial clustering on its own.
- **`-c` Clustering Algorithm**: The clustering paradigm to be used by CM++. Can choose from `leiden`, `leiden_mod`, `ikc`, and `external`.
- **`-t` Connectivity Threshold**: The connectivity threshold that every cluster must have at least to be considered 'well-connected'. This threshold can be a static integer e.g. `2` or a linear combination of:
  - `log10`: $log10(n)$ where $n$ is the number of nodes in the cluster
  - `k`: the k-core value of the cluster
  - `mcd`: the minimum degree value
  - e.g. `1log10`, `1log10+1mcd+2k`.
- **`-n` Number of Processors**: The number of cores to run CM++ in parallel. This defaults to 4.
- **`-o` Output File**: The output clustering file path. This is a 'node_id cluster_id' .tsv.

For example, you can run:

`python -m hm01.cm -i network.tsv -e clustering.tsv -c leiden -g 0.01 -t 1log10 -n 32 -o output.tsv`

## External Clusterers

If you want to use an external clustering algorithm, use the following command format:

``` bash
python -m hm01.cm
  -i     {input network}
  -e     {existing clustering (optional)}
  -c     external
  -cargs {clustering arguments json}
  -cfile {clustering algorithm code}
  -t     {connectivity threshold}
  -n     {number of processors (optional)}
  -o     {output file}
```

- **`-cargs`: Clustering Arguments JSON**: This is a json file containing argument names being mapped to their values. If the custom clusterer doesn't take any arguments (e.g. Infomap). The json will look like the following
  ```
  {}
  ```
  Else, here is an example arguments json for Markov Clustering (MCL):
  ```json
  {
    "inflation": 1.8
  }
  ```
- **`-cfile`: Clustering Algorithm Code**: Path to your Python wrapper for the clustering algorithm. See this wrapper for example: [Infomap](../hm01/clusterers/external_clusterers/infomap_wrapper.py). For instructions on writing your own wrapper, see [here](pipeline_customization.md#i-inserting-your-clustering-method-into-cm).
