# JSON Input Documentation
The following document will go over the different parameters for each stage as well as rules and limitations for each stage. To view a valid pipeline with all parameters included, refer to [`pipeline_template.json`](pipeline_template.json).
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
- **output_dir**: The directory to store pipeline outputs. Must be an existing directory.
- **algorithm**: The name of the algorithm. Can choose from `"leiden"`, `"leiden_mod"`, and `"ikc"`.
- **iterations**: The number of iterations to run the clustering algorithm, Can either be an int or an array of ints. If it is an array, the pipeline will generate multiple clusterings for each iteration value.
- **stages**: An array of [stage](#stages) objects.
  
The following is only required if the algorithm is `"leiden"`:
- **resolution**: The resolution parameters for Leiden. Can either be a single float or an array of floats. If it is an array, the pipeline will generate multiple clusterings for each resolution value. If iterations is also an array, the pipeline will generate a clustering for every iteration-resolution pair.
## Stages
### Cleanup 
This stage removes any self loops (i.e. edges $(u, u)$ ) and parallel edges (i.e. duplicate edges $(u, v)$ with more than one occurrence in the edge list). This stage does not take any extra parameters and has the following syntax. Add the following object in the stages array:
```json
{
    "name": "cleanup"
}
```
**Limitations**: The cleanup stage must be the first stage (**TODO** allow pipeline to start from any point). This stage cannot come after a stage that outputs a clustering (ex. filtering, connectivity_modifier).
