"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations
from dataclasses import dataclass
import typer
from enum import Enum
from typing import List, Optional, Tuple, Union, Dict, Deque, cast
import math
import time
from collections import deque
from itertools import chain
import treeswift as ts
import networkit as nk
from structlog import get_logger
import jsonpickle

from hm01.clusterers.abstract_clusterer import AbstractClusterer
from hm01.clusterers.ikc_wrapper import IkcClusterer
from hm01.clusterers.leiden_wrapper import LeidenClusterer, Quality
from hm01.context import context
from hm01.mincut_requirement import MincutRequirement
from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph
#from hm01.pruner import prune_graph

import sys
import sqlite3
import pickle as pkl

class ClustererSpec(str, Enum):
    """ Container for Clusterer Specification """  
    leiden = "leiden"
    ikc = "ikc"
    leiden_mod = "leiden_mod"

def algorithm_g(global_graph: Graph,
    graphs: List[IntangibleSubgraph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:
    """ Main algorithm in hm01 """
    pass

def main(
    input: str = typer.Option(..., "--input", "-i"),
    existing_clustering: str = typer.Option(..., "--existing-clustering", "-e"),
    quiet: Optional[bool] = typer.Option(False, "--quiet", "-q"),
    working_dir: Optional[str] = typer.Option("", "--working-dir", "-d"),
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),
    threshold: str = typer.Option("", "--threshold", "-t"),
    output: str = typer.Option("", "--output", "-o")
):
    """ Connectivity-Modifier (CM). Take a network and cluster it ensuring cut validity
    """
    # Setting a really high recursion limit to prevent stack overflow errors
    sys.setrecursionlimit(1231231234)

    # Check -g and -k parameters for Leiden and IKC respectively
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1, "Leiden requires resolution"
        clusterer: Union[LeidenClusterer, IkcClusterer] = LeidenClusterer(resolution)
    elif clusterer_spec == ClustererSpec.leiden_mod:
        assert resolution == -1, "Leiden with modularity does not support resolution"
        clusterer = LeidenClusterer(resolution, quality=Quality.modularity)
    else:
        assert k != -1, "IKC requires k"
        clusterer = IkcClusterer(k)

    # Start hm01
    if not quiet:
        log = get_logger()
        context.with_working_dir(input + "_working_dir" if not working_dir else working_dir)
        log.info(
            f"starting hm01",
            input=input,
            working_dir=context.working_dir,
            clusterer=clusterer,
        )

    # Parse mincut threshold specification
    requirement = MincutRequirement.try_from_str(threshold)
    if not quiet:
        log.info(f"parsed connectivity requirement", requirement=requirement)

    time1 = time.time()

    # Load full graph into Graph object
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(input)
    log.info(
        f"loaded graph",
        n=nk_graph.numberOfNodes(),
        m=nk_graph.numberOfEdges(),
        elapsed=time.time() - time1,
    )
    root_graph = Graph(nk_graph, "")

    # Load clustering
    if not quiet:
        log.info(f"loading existing clustering before algorithm-g", clusterer=clusterer)
    clusters = clusterer.from_existing_clustering(existing_clustering)
    if not quiet:
        log.info(
            f"first round of clustering obtained",
            num_clusters=len(clusters),
            summary=summarize_graphs(clusters),
        )

    # Call the main CM algorithm
    new_clusters, labels, tree = algorithm_g(
        root_graph, clusters, clusterer, requirement
    )

    # Retrieve output
    '''
    with open(output, "w+") as f:
        for n, cid in labels.items():
            f.write(f"{n} {cid}\n")
    with open(output + ".tree.json", "w+") as f:
        f.write(cast(str, jsonpickle.encode(tree)))
    '''

def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
