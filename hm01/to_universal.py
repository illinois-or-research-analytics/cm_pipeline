from __future__ import annotations

import treeswift as ts
import numpy as np
import json

from structlog import get_logger
from dataclasses import dataclass, asdict
from typing import List, Optional, Sequence, Union, cast

from graph import Graph, IntangibleSubgraph
from cluster_tree import ClusterTreeNode
from clusterers.leiden_wrapper import LeidenClusterer


class ClusteringMetadata:
    """Metadata about a clustering as recorded in a tree."""

    def __init__(self, tree: ts.Tree):
        self.tree = tree
        self.lookup = {}
        for n in tree.traverse_postorder():
            self.lookup[n.label] = cast(ClusterTreeNode, n)

    def find_info(
        self, graph: Union[Graph, IntangibleSubgraph]
    ) -> Optional[ClusterTreeNode]:
        """Find the info for the graph"""
        return self.lookup.get(graph.index)


def summary_list(list: Sequence[Union[int, float]]) -> str:
    """Summarize a list of numbers"""
    return f"{min(list)}-{np.median(list)}-{max(list)}"


def read_clusters_from_leiden(filepath: str) -> List[IntangibleSubgraph]:
    clusterer = LeidenClusterer(1)
    return clusterer.from_existing_clustering(filepath)


@dataclass
class ClusteringSkeleton:
    """ (VR) Object containing static methods to fetch clustering info 
    
    Contains single cluster data
    ----------------------------
    label (str):                index of the cluster
    nodes (list[int]):          list of node Ids in the cluster
    connectivity (int):         mincut value
    descendants (list[str]):    (only for non-cm_valid clusters) a list of clusters resulting from cm operations (pruning, cutting) on the current cluster
    cm_valid (bool):            this value is true iff the cluster doesn't need to be operated on by cm anymore
    extant (bool):              this value is true iff it is both cm_valid and hasn't been operated on by cm
    """
    label: str
    nodes: List[int]
    connectivity: int
    descendants: List[str]
    cm_valid: bool              # (VR) Change: Add cm validity as a parameter in the json
    extant : bool

    @staticmethod
    def from_graphs(
        graphs: List[IntangibleSubgraph],
        metadata: ClusteringMetadata,
    ) -> List[ClusteringSkeleton]:
        """ (VR) Construct a list of clustering skeletons (extracting info) from a list of clusters 
        
        Parameters
        ---------- 
            graphs (list[IntangibleSubgraph]):  cluster list
            metadata (ClusteringMetadata):      wrapper for the cluster provenance tree
        """
        ans = []

        if graphs == [IntangibleSubgraph(subset=[], index='')]:
            return []
        
        for g in graphs:
            info = metadata.find_info(g)            # (VR) Get the current cluster and its location in the tree
            assert info                             # (VR) Assert that it exists
            info = cast(ClusterTreeNode, info)
            descendants = []                        # (VR) Get the list of leaves that result from this cluster
            for n in info.traverse_leaves():
                if n.label != g.index:
                    descendants.append(n.label)
            ans.append(
                ClusteringSkeleton(
                    g.index,
                    list(g.subset),
                    info.cut_size,                  # (VR) Change: We should allow json outputs to show connectivities of 0
                    # (VR) Change: (info.cut_size or 1) if info else 1,
                    descendants,
                    info.cm_valid,
                    info.extant
                )
            )
        ans.sort(key=lambda x: (len(x.descendants), len(x.nodes)), reverse=True)
        return ans

    @staticmethod
    def write_ndjson(graphs: List[ClusteringSkeleton], filepath: str):
        """ (VR) Output json from the list of clusters """
        use_descendants = False
        if any(g.descendants for g in graphs):              # (VR) If the graphs are 'before' and not 'after', output the descendants as well
            use_descendants = True

        """ (VR) Change: I altered the json format. Rather than being separate objects, the output is a single array or cluster objects 
        
        Format
        ------
        [
            {<cluster info 1>},
            ...
            {<cluster info n>}
        ]

        Why? It's because then we'll have valid json outputs
        """
        json_str = ""
        with open(filepath, "w+") as f:
            json_str += "["
            for i, g in enumerate(graphs):
                d = asdict(g)
                if not use_descendants:
                    del d["descendants"]
                if i < len(graphs) - 1:
                    json_str += json.dumps(d) + ","
                else:
                    json_str += json.dumps(d)
            json_str += "]"

            f.write(json.dumps(json.loads(json_str), indent=4))

# TODO: arguments below should eventually be converted to Path types
def cm2universal(
    quiet,
    tree,
    node2cid,
    output,
):
    """Compute two sets of statistics for a hiearchical clustering"""
    if not quiet:
        log = get_logger()

    # (VR) Initialize cluster objects
    for n in tree.traverse_postorder():
        n.nodes = []
    metadata = ClusteringMetadata(tree)
    
    # (VR) Go through the tsv and fill in the node lists for each of the clusters
    for node, cid in node2cid.items():
        metadata.lookup[cid].nodes.append(int(node))

    if not quiet:
        log.info("loaded clustering")

    # (VR) Get the node lists for the before clusters        
    for c in tree.root.children:
        c.nodes = list(set.union(*[set(n.nodes) for n in c.traverse_postorder()]))

    # (VR) Get before and after cluster lists
    original_clusters = [
        IntangibleSubgraph(n.nodes, n.label) for n in tree.root.children
    ]
    valid_clusters = [
        IntangibleSubgraph(n.nodes, n.label) for n in tree.traverse_leaves() if n.cm_valid # (VR) Change: We dont want filtration by extant clusters, rather by cm valid clusters
    ]

    # (VR) Compute the clustering skeleton lists from the above cluster lists and output the json
    original_skeletons = ClusteringSkeleton.from_graphs(original_clusters, metadata)        # (VR) Change: removed unneeded parameter, the full network
    valid_skeletons = ClusteringSkeleton.from_graphs(valid_clusters, metadata)
    ClusteringSkeleton.write_ndjson(original_skeletons, output + ".before.json")
    ClusteringSkeleton.write_ndjson(valid_skeletons, output + ".after.json")