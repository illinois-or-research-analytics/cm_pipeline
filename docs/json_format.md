# JSON Input Documentation
The following document will go over the different parameters for each stage as well as rules and limitations for each stage. To view a valid pipeline with all parameters included, refer to [`pipeline_template.json`](pipeline_template.json).
- [JSON Input Documentation](#json-input-documentation)
  - [Overall Parameters](#overall-parameters)
  - [Stages](#stages)
    - [Cleanup](#cleanup)
    - [Clustering](#clustering)
    - [Filtering](#filtering)
    - [Connectivity Modifier](#connectivity-modifier)
    - [Stats](#stats)
## Overall Parameters
The following is a general overview of the overall parameters that don't belong to a single stage but rather the entire pipeline:
```json
    "title": "cit-new-pp-output",
    "name": "cit_patents",
    "input_file": "/data3/chackoge/networks/cit_patents_cleaned.tsv",
    "output_dir": "samples/",
    "algorithm": "leiden",
    "resolution": [0.5, 0.01],
    "iterations": 2,
    "stages": ["..."]
```
All of the following parameter values are required:
- **title**: The name of the run, can be any string that is descriptive of the pipeline
- **name**: The name of the network, again can be any string that is descriptive of the network
- **input_file**: The filename of the input network. Is an edgelist .tsv.
- **output_dir**: The directory to store pipeline outputs.
- **algorithm**: The name of the algorithm. Can choose from `"leiden"`, `"leiden_mod"`, and `"ikc"`.
- **iterations**: The number of iterations to run the clustering algorithm, Can either be an int or an array of ints. If it is an array, the pipeline will generate multiple clusterings for each iteration value.
- **stages**: An array of [stage](#stages) objects.
  
The following is only required if the algorithm is `"leiden"`:
- **resolution**: The resolution parameters for Leiden. Can either be a single float or an array of floats. If it is an array, the pipeline will generate multiple clusterings for each resolution value. If iterations is also an array, the pipeline will generate a clustering for every iteration-resolution pair.  
  
**NOTE** Paths must be relative to the json file, or absolute.  
## Stages
### Cleanup 
This stage removes any self loops (i.e. edges $(u, u)$ ) and parallel edges (i.e. duplicate edges $(u, v)$ with more than one occurrence in the edge list). This stage does not take any extra parameters and has the following syntax. Add the following object in the stages array:
```json
{
    "name": "cleanup"
}
```
**Limitations**: The cleanup stage must be the first stage (**TODO** allow pipeline to start from any point). This stage cannot come after a stage that outputs a clustering (ex. filtering, connectivity_modifier).
### Clustering
This stage uses the clustering algorithm specified in the overall parameters to cluster a cleaned network. If resolutions and/or iterations are arrays, multiple clusterings are outputted. To add this stage, add the following to the stages array. Modify the parameters as needed:
```json
{
    "name": "clustering",
    "parallel_limit": 2
}
```
**Optional Parameter**:
- **parallel_limit**: The number of clustering jobs that can be run in parallel. This is useful if resolutions or iterations are arrays. In the example above, clustering jobs will be run in pairs of twos.
  - If the limit is 1, clustering jobs will be run sequentially.
  - If no limit is specified, all clustering jobs will be run in parallel.
  
**Limitations**: This stage cannot come after a stage that outputs a clustering.
### Filtering
This stage takes a clustering and filters it according to a script, or series of scripts. To add this stage, add the following to the stages array. Modify the scripts as needed.:
```json
{
    "name": "filtering",
    "scripts": [
        "./scripts/subset_graph_nonetworkit_treestar.R",
        "./scripts/make_cm_ready.R"
    ]
}
```
**Required Paramter**
- **scripts**: This is an array of script file names. If you only want to run one script, the array will have one element with the script name. The following are scripts in the repository that can be used for filtration:
  - `"./scripts/subset_graph_nonetworkit_treestar.R"`
  - `"./scripts/make_cm_ready.R"`
  - `"./scripts/post_cm_filter.R"`
  
**Limitations**: This stage must come after a stage that outputs a clustering.
### Connectivity Modifier
This is the stage that applies CM++ to a clustering to ensure connectivity requirements in clusters. To add the stage, simply add the following to the stages array. Change the parameters as needed. If the parameters are optional, they can be deleted from this template:
```json
{
    "name": "connectivity_modifier",
    "memprof": true,
    "threshold": "1log10",
    "nprocs": 32,
    "quiet": true,
    "firsttsv": true
}
```
**Required Parameter**
- **threshold**: The connectivity threshold. This is a string representing a linear combination between `log10`, `mcd` (minimum core degree), `k` (IKC only), and a constant. The following are valid thresholds
  - `1log10`
  - `1log10+4mcd+1k+4`
  - `mcd`
  
**Optional Parameters**
- **memprof**: Profile the memory usage per process over time as CM++ is running. If this is ommitted or set to false, memory profiling will not run.
- **nprocs**: Number of cores to run CM++. If omitted, this defaults to 4.
- **quiet**: Silence output to terminal. If omitted, this defaults to false.
- **firsttsv**: Output the original clustering output before CM2Universal is run. If omitted, this defaults to false.
  
**Limitations**: This must come after a stage that outputs a clustering.
### Stats
This stage reports statistics of a clustering that was outputted by a stage preceding it. For more information on the statistics reporting ans its outputs. Refer to the following [repository](https://github.com/vikramr2/cluster-statistics). The code for the stage is the following:
```json
{
    "name": "stats",
    "noktruss": true,
    "parallel_limit": 2
}
```
**Optional Parameters**
- **parallel_limit**: This is the same as for the clustering stage
- **noktruss**: Silence k-truss computations in the stats script. This is simply because k-truss computation uses a lot of runtime.
  
**Limitations**: This stage must come after a stage that outputs a clustering.