# Pipeline Modification Documentation

The CM Pipline allows for macros and modifications that developers can insert. You will be able to modify the pipeline in the two following ways:

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

3. Then when you call CM++, you will create a JSON file mapping arguments to their values. Here is a template/example

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

## Creating your own pipeline stage

## Submitting your Changes

To make your new stages and clustering methods a  part of the official repo:

1. Create a fork of this repository
2. Insert your new clustering methods and stages
3. Create a pull request and we will review and approve it
