# Features

## CM Pipeline Features

The CM Pipeline is a modular pipeline for community detection that contains the following modules:

**Graph Cleaning**: Removal of parallel and duplicate edges as well as self loops

**Community Detection**: Clusters an input network with one of Leiden, IKC, and InfoMap. 

**Cluster Filtration**: A pre-processing stage that allows users to filter out clusters that are trees or have size below a given threshold.

**Community Statistics Reporting**: Generates node and edge count, modularity score, Constant Potts Model score, conductance, and edge-connectivity at multiple stages.

**Extensibility**: Developers can design new stages and wire in new algorithms. Please see [the following document](pipeline_customization.md) for instructions on how to expand the list of supported clustering algorithms as a developer.

**CM++**

## CM++ Features

CM++ is a module within the CM Pipeline, having the following features:

**Function**: CM++ refines your existing graph clustering by carving them into well-connected clusters with high minimum cut values.

**Flexibility**: Users can accompany their definition of a good community with well-connectedness. CM++ works with any clustering algorithm and presently provides build in support for Leiden, IKC, and Infomap.

**Dynamic Thresholding**: Connectivity thresholds can be constants, or functions of the number of nodes in the cluster, or the minimum node degree of the cluster.

**Multi-processing**: For better performance, users can specify a larger number of cores to process clusters concurrently.