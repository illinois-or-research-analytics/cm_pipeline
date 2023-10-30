# Pipeline Modification Documentation

The CM Pipeline allows for macros and modifications that developers can insert. You will be able to modify the pipeline in the two following ways:

- Use your own clustering method
- Build your own pipeline stages

## Using your own clustering method

First, to use your own clustering method, follow both of these procedures:

### I. Inserting your clustering method into CM++

1. Navigate to `hm01/clusterers/external_clusterers/` in the repository
2. Create a clusterer object that calls your clustering method. Here is a template:

```python
from dataclasses import dataclass
from typing import List, Iterator, Dict, Union

from hm01.clusterers.abstract_clusterer import AbstractClusterer

from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph

@dataclass
class TemplateClusterer(AbstractClusterer):

    def __init__(args):
        # Create a clusterer object. Args is the arguments of the clusterer
        # Ex. Leiden-CPM would have resolution as an arg
        pass

    def cluster(self, graph: Union[Graph, RealizedSubgraph]) -> Iterator[IntangibleSubgraph]:
        # Return an iterator of intangible subgraphs representing your resultant clusters
        pass

def getclusterer(args):
    # Construct the clusterer object from the args
    return TemplateClusterer(args)

    # Ex. Leiden-CPM's clusterer would be getclusterer(resolution)
```

1. Then when you call CM++, you will create a JSON file mapping arguments to their values. Here is a template/example

```json
{
    "arg": "val",
    "resolution": 0.5 
}
```

4. Then, when you call CM++, you can do the following:

```bash
python -m hm01.cm 
    -i network.tsv 
    -e clustering.tsv
    -cfile hm01/clusterers/MyWrapper.py
    -cargs MyArguments.json
    -t 1log10
```

### II. Inserting your clustering method into the pipeline

1. Navigate to `source/clusterers/`
2. Create a python object file to wrap your clustering method. Here is a template:

```python
from source.clustering import Clustering

class LeidenModClustering(Clustering):
    def __init__(
            self, 
            data, 
            input_file, 
            network_name, 
            resolutions, 
            iterations, 
            algorithm, 
            existing_clustering, 
            working_dir, 
            index):
        super().__init__(
            data, 
            input_file, 
            network_name, 
            resolutions, 
            iterations, 
            algorithm, 
            existing_clustering, 
            working_dir, 
            index)
        
    def initialize_clustering(self):
        self.output_file = [
            # process list of parameter sets into output file names
            # For example, if Leiden CPM has parameter set 
            #   [{
            #       "res": 0.5,
            #       "i": 2
            #   }, {
            #       "res": 0.1,
            #       "i": 1
            #   }]
            # You will need two output files. One for res-0.5-i2 and one for res-0.1-i1
            for param in self.params
        ]
    
    def get_stage_commands(self, project_root, prev_file):
        # Write code that returns an array of shell commands that run your clustering method.
        # The array of commands needs to be per, and in the same order, as your params set
        # Refer to self.params
        pass
```

3. Navigate to `source/typedict.py`. In the `cluster_classes` dictionary.
4. Add a mapping from your clustering algorithm name to the object that you had created. Remember to import your clusterer! E. `'mcl': MCL`.
5. To run the pipeline with your new clusterer. Do the following:
   1. Create a json file (refer to `pipeline.json` for an example) containing the parameter set that you would like to run for your method. This set will have multiple sets of parameters if you want to have multiple runs of your pipeline.
   2. If your clusterer doesnt take any parameters, your `"params"` field will look like: `"params": [{}]`
   3. In the case that CM++ is in your pipeline, make sure your stage has `"cfile"` in the parameters. Note that you do not need a `"cargs"` parameter as the pipeline will automatically create an args json.
   4. Run `python -m main pipeline.json` from root.

### Example: Infomap

1. First, I created the infomap wrapper as shown in [this file](../hm01/clusterers/external_clusterers/infomap_wrapper.py).
   1. The cluster method simply uses python's Infomap library, and converts the outputs into hm01 `IntangibleSubgraph` objects.
   2. The `get_clusterer` method doesn't take any arguments since InfoMap doesn't require any parameters
2. Second, in [this clusterer object](../source/clusterers/infomap.py), I created a clusterer object for the pipeline.
   1. InfoMap is quite simple, it doesn't take any parameters and it doesn't have any extra requirements, so the `__init__` method doesn't need any more than it has.
   2. The `initialize_clustering` method simply sets its output file name.
      1. You want output in the relevant directory. For infomap, that was `f{self.working_dir}/infomap/`.
      2. For your method, you should refer to the `self.get_folder_name(param)` method, where `param` is the current parameter dictionary.
   3. The `get_stage_commands` method converts the stage object data into a runnable shell command by the pipeline. I have made a [run_infomap](../scripts/run_infomap.py) script that the CM pipeline can call.
3. In the [typedict file](../source/typedict.py), I have added keys for infomap

## Creating your own pipeline stage

1. Navigate to `source/`
2. Create an empty stage object. Start with this template. Replace names according to your preferences:

```python
from source.stage import Stage


class MyStage(Stage):
    def __init__(
            self,
            data,
            input_file,
            network_name,
            resolutions,
            iterations,
            algorithm,
            existing_clustering,
            working_dir,
            index
    ):
        super().__init__(
            data, 
            input_file, 
            network_name,
            resolutions,
            iterations,
            algorithm,
            existing_clustering,
            working_dir,
            index)
    
    def initialize(self, data):        
        # This method sets required parameters of your stage
        # The data argument is the stage data in the json (dict)

        self.chainable = # Can the outputs of this stage be used as an input for the next?
        self.outputs_clustering = # Does this stage output a clustering or something else?

        self.output_file = # What filename does this stage output?

    def get_stage_commands(self, project_root, prev_file):
        # Return an array of commands that the pipeline will execute when it reaches this stage
```

3. Navigate to `source/typedict.py`
4. In `stage_classes`, modify the disctionary to map a string representing your stage, to the object you created. Make sure to import your code!
5. Now, when writing your `pipeline.json`, simply add your stage in the `"stages"` array. Use the name specified in the previous step, and the arguments processed in your code.

### Mincut Filter

**TODO: This should be tested, and documented here**

## The Stage and Clusterer Objects

### Extensions of `AbstractClusterer`

To view source code for the abstract class, see [here](../hm01/clusterers/abstract_clusterer.py). Objects extending the `AbstractClusterer` object must have the following:

- Object variables containing the clusterer parameters:

```python
@dataclass
class IkcClusterer(AbstractClusterer):
    k: int
```

- A `cluster` method that runs the clustering algorithm and returns clusters in the form of `IntangibleSubgraph` objects in hm01. This is really just a set of vertices.
  - This method can also call other class helper methods

- Your file containing the object extending the `AbstractClusterer` must contain a `get_clusterer` method taking in arguments for the clusterer, and returning the clusterer object. This is so that CM can generalize to use your clustering method

### Extensions of `Stage`

To view the abstract class, click [here](../source/stage.py). Any extension of Stage must contain the following:

- The `__init__` can simply super the abstract class.
- An `initialize(self, data)` method to set the following:
  - The `data` parameter is a dictionary representing the stage object in the json.
  - `self.outputs_clustering`: A boolean on whether your stage outputs a cluatering or something else
    - For example `cleanup` and `stats` outputs a graph and statistics respectively, both of which are not clusterings.
  - `self.chainable`: A boolean on whether you stage's outputs can be used by the next stage
    - For example, if your stage outputs an aggregated graph that can be reclustered, it is chainable
  - `self.output_file`
    - If your stage outputs one file, this is a string
    - If your stage outputs a file per parameter set, this is an array following the same order as the params specified in the json.
    - Output files should be stored in the appropriate directory.
      - Use `self.get_folder_name(param)` to get the folder name for the parameter dictionary used.
      - This means that the correct folder for a param set `param` would be in `f'{self.working_dir}/{self.get_folder_name(param)}/`
  - Any parameters that are specific to your clusterer can be assigned here
    - E.g. `self.scripts` for the filtration stage
- A `get_stage_commands(self, project_root, prev_file)`.
  - The `project_root` is the root folder for this repository
  - The `prev_file` is the filename (as a string or array of strings per parameter set).
  - This command should return an array of commands to execute when this stage is reached. These command must address all the parameter sets, and return files per each parameter set.

### Extensions of `Clustering`

Clustering is already an extension of Stage. To view the parent object, see the code [here](../source/clustering.py). Any extension of the clustering object should have:

- `__init__` can simply super the clustering object
- `initialize_clustering(self)`. Set the output file when this clusterer is run. This is similar to setting the stage output file.
- `get_stage_commands(self, project_root, previous file)`. This returns a set of commands when your clustering method is run. 
  - You should have an executable for your clustering that is runnable via shell. If it is a python module (like infomap or Leiden), please make a runnable script [(like this one)](../scripts/run_leiden.py). If you want to submit your changes, keep your scripts in the [scripts/](../scripts/) folder.

## Submitting your Changes

To make your new stages and clustering methods a  part of the official repo:

1. Create a fork of this repository
2. Insert your new clustering methods and stages
3. Create a pull request and we will review and approve it
