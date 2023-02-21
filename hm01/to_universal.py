from __future__ import annotations
from dataclasses import dataclass, asdict
import os
from typing import List, Optional, Sequence, Union, cast
import typing
import typer
import jsonpickle
import treeswift as ts
import numpy as np
import pandas as pd
import json
from structlog import get_logger
import sys

from hm01.graph import Graph, IntangibleSubgraph
from hm01.cm import ClusterTreeNode
from .clusterers.leiden_wrapper import LeidenClusterer


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
    label: str
    nodes: List[int]
    connectivity: int
    descendants: List[str]
    extant : bool

    @staticmethod
    def from_graphs(
        global_graph: Graph,
        graphs: List[IntangibleSubgraph],
        metadata: ClusteringMetadata,
    ) -> List[ClusteringSkeleton]:
        ans = []
        for g in graphs:
            info = metadata.find_info(g)
            assert info
            info = cast(ClusterTreeNode, info)
            descendants = []
            for n in info.traverse_leaves():
                if n.label != g.index:
                    descendants.append(n.label)
            ans.append(
                ClusteringSkeleton(
                    g.index,
                    list(g.subset),
                    (info.cut_size or 1) if info else 1,
                    descendants,
                    info.extant
                )
            )
        ans.sort(key=lambda x: (len(x.descendants), len(x.nodes)), reverse=True)
        return ans

    @staticmethod
    def write_ndjson(graphs: List[ClusteringSkeleton], filepath: str):
        use_descendants = False
        if any(g.descendants for g in graphs):
            use_descendants = True
        with open(filepath, "w+") as f:
            for g in graphs:
                d = asdict(g)
                if not use_descendants:
                    del d["descendants"]
                f.write(json.dumps(d) + "\n")

# TODO: arguments below should eventually be converted to Path types
def cm2universal(
    input,
    quiet,
    graph,
    tree,
    node2cid,
    output,
):
    """Compute two sets of statistics for a hiearchical clustering"""
    if not quiet:
        log = get_logger()

    assert os.path.exists(input)
    treepath = input + ".tree.json"
    assert os.path.exists(treepath)
    assert os.path.exists(graph_path)

    for n in tree.traverse_postorder():
        n.nodes = []
    metadata = ClusteringMetadata(tree)
    with open(input, "r") as f:
        for l in f:
            metadata.lookup[cid].nodes.append(int(node))

    if not quiet:
        log.info("loaded clustering")
        
    for c in tree.root.children:
        c.nodes = list(set.union(*[set(n.nodes) for n in c.traverse_postorder()]))
    original_clusters = [
        IntangibleSubgraph(n.nodes, n.label) for n in tree.root.children
    ]
    extant_clusters = [
        IntangibleSubgraph(n.nodes, n.label) for n in tree.traverse_leaves() if n.extant
    ]
    original_skeletons = ClusteringSkeleton.from_graphs(
        graph, original_clusters, metadata
    )
    extant_skeletons = ClusteringSkeleton.from_graphs(graph, extant_clusters, metadata)
    ClusteringSkeleton.write_ndjson(original_skeletons, output + ".before.json")
    ClusteringSkeleton.write_ndjson(extant_skeletons, output + ".after.json")