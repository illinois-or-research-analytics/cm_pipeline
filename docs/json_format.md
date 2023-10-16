# JSON Input Documentation

The following document will go over the different parameters for each stage as well as rules and limitations for each stage. To view a valid pipeline with all parameters included, refer to [`pipeline_template.json`](pipeline_template.json).

- [JSON Input Documentation](#json-input-documentation)
  - [Overall Parameters](#overall-parameters)
  - [Algorithmic Parameters](#algorithmic-parameters)
    - [Leiden-CPM](#leiden-cpm)
    - [Leiden-Mod](#leiden-mod)
    - [IKC](#ikc)
    - [Infomap](#infomap)
    - [Your Own Clustering Method](#your-own-clustering-method)
  - [Stages](#stages)
    - [Cleanup](#cleanup)
    - [Clustering](#clustering)
    - [Filtering](#filtering)
    - [Connectivity Modifier](#connectivity-modifier)
    - [Stats](#stats)
  - [Using an Existing Clustering](#using-an-existing-clustering)
  - [Examples](#examples)

## Overall Parameters

The following is a general overview of the overall parameters that don't belong to a single stage but rather the entire pipeline:

```json
    "title": "cit-new-pp-output",
    "name": "cit_patents",
    "input_file": "/data3/chackoge/networks/cit_patents_cleaned.tsv",
    "output_dir": "samples/",
    "algorithm": "leiden",
    "params": [
        {
            "res": 0.5,
            "i": 2
        },
        {  
            "res": 0.1,
            "i": 2
        },
        {
            "res": 0.01,
            "i": 2
        }
    ]
    "stages": ["..."]
```

All of the following parameter values are required:

- **title**: The name of the run, can be any string that is descriptive of the pipeline
- **name**: The name of the network, again can be any string that is descriptive of the network
- **input_file**: The filename of the input network. Is an edgelist .tsv.
- **output_dir**: The directory to store pipeline outputs.
- **algorithm**: The name of the algorithm. Can choose from `"leiden"`, `"leiden_mod"`, and `"ikc"`.
- **stages**: An array of [stage](#stages) objects.
- **params**: A list of dictionaries mapping algorithm parameters to their values.

**NOTE** Paths must be relative to the json file, or absolute.  

## Algorithmic Parameters

The `params` field contains dictionaries mapping parameter values to their values. These field names will vary based on the algorithm being used.

### Leiden-CPM

As shown above, Leiden-CPM takes resolution and iterations parameters. Designated in the json as `"res"` and `"i"` fields.

```json
{
    "res": 0.5,
    "i": 2
}
```

### Leiden-Mod

Leiden-Mod doesn't need to use a resolution parameter since it optimizes modularity and not CPM. Therefore, only an iterations parameter needs to be passed.

```json
{
    "i": 2
}
```

### IKC

IKC only needs a k-core value passed as a parameter, designated as `"k"`.

```json
{
    "k": 10
}
```

### Infomap

Infomap doesn't take ay parameters, so its dictionary is always empty. However, to fit the style constraints of the pipeline, any algorithm that doesnt take any parameters should use an empty dictionary as follows.

```json
{}
```

Since you can't have multiple runs of the same parameter set, the overall `"params"` field in the json will look like this:

```json
"params": [{}]
```

### Your Own Clustering Method

Refer to the [customization documentation](pipeline_customization.md) for more details on how to create your own clustering. You will be able to assign parameter names for your own clustering using this pipeline.

Supposing you create a pipeline with two parameters `"a"` and `"b"` with integer values, you will be able to designate them in the pipeline file.

```json
{
    "a": 1,
    "b": 2
}
```

## Stages

### Cleanup

This stage removes any self loops (i.e. edges $(u, u)$ ) and parallel edges (i.e. duplicate edges $(u, v)$ with more than one occurrence in the edge list). This stage does not take any extra parameters and has the following syntax. Add the following object in the stages array:

```json
{
    "name": "cleanup"
}
```

**Limitations**: This stage cannot come after a stage that outputs a clustering (ex. filtering, connectivity_modifier).

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

**Required Paramters**:

- **scripts**: This is an array of script file names. If you only want to run one script, the array will have one element with the script name. The following are scripts in the repository that can be used for filtration:
  - `"subset_graph_nonetworkit_treestar.R"`
  - `"make_cm_ready.R"`
  - `"post_cm_filter.R"`
  
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
}
```

**Required Parameter**:

- **threshold**: The connectivity threshold. This is a string representing a linear combination between `log10`, `mcd` (minimum core degree), `k` (IKC only), and a constant. The following are valid thresholds
  - `1log10`
  - `1log10+4mcd+1k+4`
  - `mcd`
  
**Optional Parameters**:

- **memprof**: Profile the memory usage per process over time as CM++ is running. If this is ommitted or set to false, memory profiling will not run.
- **nprocs**: Number of cores to run CM++. If omitted, this defaults to 4.
- **quiet**: Silence output to terminal. If omitted, this defaults to false.
  
**Limitations**: This must come after a stage that outputs a clustering.  

- **NOTE: If using IKC, it's recommended to run no more than 4 processors on CM**

### Stats

This stage reports statistics of a clustering that was outputted by a stage preceding it. For more information on the statistics reporting ans its outputs. The code for the stage is the following:

```json
{
    "name": "stats",
    "noktruss": true,
    "parallel_limit": 2,
    "universal_before": false,
    "summarize": false
}
```

**Optional Parameters**:

- **parallel_limit**: This is the same as for the clustering stage
- **noktruss**: Silence k-truss computations in the stats script. This is simply because k-truss computation uses a lot of runtime.
- **universal_before**: Output extra details on which clusters were split by CM. If ommitted, this defaults to `false`.
- **summarize**: Output more detailed summary statistics for the clustering overall.
  
**Limitations**:

- This stage must come after a stage that outputs a clustering.
- If `universal_before` is a field, CM must appear sometime before this stats stage (*NOTE*: Not necessarily one stage before, can be at any point preceding this stats stage).

## Using an Existing Clustering

```json
{
    "title": "cit-new-pp-output-leiden-skipstage",
    "name": "cit_patents",
    "input_file": "/data3/chackoge/networks/cit_patents_cleaned.tsv",
    "output_dir": "samples/",
    "algorithm": "leiden",
    "params": [
        {
            "res": 0.5,
            "i": 2,
            "existing_clustering": "samples/cit-new-pp-output-leiden_mod-20230614-23:55:59/res-0.5-i2/S2_cit_patents_leiden.0.5_i2_clustering.tsv"
        },
        {
            "res": 0.1,
            "i": 2,
            "existing_clustering": "samples/cit-new-pp-output-leiden_mod-20230614-23:55:59/res-0.1-i2/S2_cit_patents_leiden.0.1_i2_clustering.tsv"
        }
    ],
    "stages": ["..."]
}
```

To use an existing clustering, add a value `"existing_clustering"` per parameter entry in your json header. This is applicable for any clustering method.

## Examples

View the following folder to check out examples: [examples/](../examples/)
