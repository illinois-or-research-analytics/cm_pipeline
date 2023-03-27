"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations

from typing import List, Optional, Tuple, Union, Dict, Deque, cast
from dataclasses import dataclass
from collections import deque
from enum import Enum
from itertools import chain
from structlog import get_logger

import os
import typer
import math
import time
import treeswift as ts
import networkit as nk
import multiprocessing as mp
import jsonpickle
import functools

from clusterers.abstract_clusterer import AbstractClusterer
from clusterers.ikc_wrapper import IkcClusterer
from clusterers.leiden_wrapper import LeidenClusterer, Quality
from context import context
from mincut_requirement import MincutRequirement
from graph import Graph, IntangibleSubgraph, RealizedSubgraph
from pruner import prune_graph
from to_universal import cm2universal
from cluster_tree import ClusterTreeNode

import sys
import sqlite3
import pickle as pkl

class ClustererSpec(str, Enum):
    """ (VR) Container for Clusterer Specification """  
    leiden = "leiden"
    ikc = "ikc"
    leiden_mod = "leiden_mod"

def annotate_tree_node(
    node: ClusterTreeNode, graph: Union[Graph, IntangibleSubgraph, RealizedSubgraph]
):
    """ (VR) Labels a ClusterTreeNode with its respective cluster """
    node.label = graph.index
    node.graph_index = graph.index
    node.num_nodes = graph.n()
    node.extant = False

def update_cid_membership(
    subgraph: Union[Graph, IntangibleSubgraph, RealizedSubgraph],
    node2cids: Dict[int, str],
):
    """ (VR) Set nodes within current cluster to its respective cluster id """
    for n in subgraph.nodes():
        node2cids[n] = subgraph.index

def summarize_graphs(graphs: List[IntangibleSubgraph]) -> str:
    """ (VR) Summarize graphs for logging purposes """
    if not graphs:
        return "[](empty)"
    if len(graphs) > 3:
        return f"[{graphs[0].index}, ..., {graphs[-1].index}]({len(graphs)})"
    else:
        return f"[{', '.join([g.index for g in graphs])}]({len(graphs)})"

def print_msg_with_lock(print_lock, msg):
    print_lock.acquire()
    print(msg)
    print_lock.release()

def par_task(
    queue, 
    node2cids, 
    requirement, 
    clusterer,
    global_graph,
    ans,
    print_lock=None):
    print_msg = functools.partial(print_msg_with_lock, print_lock)
    my_pid = os.getpid()
    print_msg(f'Hi, I\'m process {my_pid}, ready to work')

    while True:
        # print_msg(f'I\'m pid {my_pid}, the queuelength is {queue.qsize()}')
        intangible_subgraph = queue.get()
        if intangible_subgraph is None:
            print_msg(f'I\'m pid {my_pid}, I have been set free!')
            queue.task_done()
            break

        # (VR) Mark nodes in popped cluster with their respective cluster ID
        update_cid_membership(intangible_subgraph, node2cids)

        # (VR) If the current cluster is a singleton or empty, move on
        if intangible_subgraph.n() <= 1:
            queue.task_done()
            continue
        
        # (VR) Realize the set of nodes contained by the graph (i.e. construct its adjacency list)
        subgraph = intangible_subgraph.realize(global_graph)

        # (VR) Get minimum node degree in current cluster
        original_mcd = subgraph.mcd()

        # (VR) Pruning: Remove singletons with node degree under threshold until there exists none
        num_pruned = prune_graph(subgraph, requirement, clusterer)
        if num_pruned > 0:
            subgraph.index = f"{subgraph.index}δ"
            update_cid_membership(subgraph, node2cids)
        
        # (VR) If the current cluster post pruning is a singleton or empty, move on
        if subgraph.n() <= 1:
            queue.task_done()
            continue

        # (VR) Compute the mincut of the cluster
        # print_msg(f'{my_pid}: pre-mincut')
        mincut_res = subgraph.find_mincut()

        # print_msg(f'{my_pid}: getting validity threshold')
        # is a cluster "cut-valid" -- having good connectivity?
        valid_threshold = requirement.validity_threshold(clusterer, subgraph)

        # (VR) If the cut size is below validity, split!
        if mincut_res.get_cut_size() <= valid_threshold and mincut_res.get_cut_size() > 0:
            print_msg(f'{my_pid}: splitting graph')
            # (VR) Split partitions and set them as children nodes
            p1, p2 = subgraph.cut_by_mincut(mincut_res)
            print_msg(f'{my_pid}: splitting done')
            # (VR) Cluster both partitions
            subp1 = list(clusterer.cluster_without_singletons(p1))
            subp2 = list(clusterer.cluster_without_singletons(p2))

            # (VR) Add the new clusters to the stack
            print_msg(f'{my_pid}: subp1 len: {len(subp1)}, subp2 len: {len(subp2)}')
            for g in subp1 + subp2:
                queue.put(g)
        else:
            # print_msg(f"{my_pid}: mincut_res: {mincut_res.get_cut_size()}, thresh: {valid_threshold}")
            # (VR) Compute the modularity of the cluster
            candidate = subgraph.to_intangible(global_graph)
            mod = global_graph.modularity_of(candidate)

            # (VR) Check if the modularity value is valid so that the answer can include the modified cluster
            if not isinstance(clusterer, IkcClusterer) or mod > 0:
                ans.append(candidate)
        queue.task_done()
    
    time.sleep(1)

def algorithm_g(
    global_graph: Graph,
    graphs: List[IntangibleSubgraph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement,
    quiet: bool,
    nodes: bool,
    ans,
    node2cids,
    num_cores: int = 4,
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:
    """ (VR) Main algorithm in hm01 
    
    Params:
        global_graph (Graph)                                : full graph from input
        graph (List[IntangibleSubgraph])                    : list of clusters
        clusterer (Union[IkcClusterer, LeidenClusterer])    : clustering algorithm
        requirement (MincutRequirement)                     : mincut connectivity requirement
    """
    if nodes:
        tree = ts.Tree()                                # (VR) tree: Recursion tree that keeps track of clusters created by serial mincut/reclusters
        tree.root = ClusterTreeNode()
        annotate_tree_node(tree.root, global_graph)
        node_mapping: Dict[str, ClusterTreeNode] = {}   # (VR) node_mapping: maps cluster id to cluster tree node       
        for g in graphs:
            n = ClusterTreeNode()
            annotate_tree_node(n, g)
            tree.root.add_child(n)
            node_mapping[g.index] = n

    stack: List[IntangibleSubgraph] = mp.JoinableQueue()  # (VR) stack: the stack for cluster processing

    # ans: List[IntangibleSubgraph] = []              # (VR) ans: Reclustered output
   
    # node2cids: Dict[int, str] = {}                  # (VR) node2cids: Mapping between nodes and cluster ID
    
    if not quiet:
        log = get_logger()
        log.info("starting algorithm-g", queue_size=len(graphs))

    print_lock = mp.Lock()
    workers = []
    for _ in range(num_cores):
        worker = mp.Process(target=par_task, args=(stack,node2cids,requirement,clusterer,global_graph,ans,print_lock))
        workers.append(worker)
    
    for worker in workers:
        worker.start()
    
    for g in graphs:
        stack.put(g)

    stack.join()

    for _ in range(len(workers)):
        stack.put(None)
    
    stack.join()

    for worker in workers:
        worker.join()

    if nodes:
        return ans, node2cids, tree

def main(
    input: str = typer.Option(..., "--input", "-i"),
    existing_clustering: str = typer.Option(..., "--existing-clustering", "-e"),
    quiet: Optional[bool] = typer.Option(False, "--quiet", "-q"),
    nodes: Optional[bool] = typer.Option(False, "--nodes", "-n"),
    working_dir: Optional[str] = typer.Option("", "--working-dir", "-d"),
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),
    threshold: str = typer.Option("", "--threshold", "-t"),
    output: str = typer.Option("", "--output", "-o")
):
    """ (VR) Connectivity-Modifier (CM). Take a network and cluster it ensuring cut validity

    Parameters:
        input (str)                     : filename of input graph
        existing_clustering (str)       : filename of existing clustering
        quiet (bool)                    : silence output messages
        working_dir (str)               : name of temporary directory to store mid-stage data (optional)
        clusterer_spec (ClusterSpec)    : clusterering algorithm
        k (int)                         : k param (for IKC only)
        resolution (float)              : resolution param (for Leiden only)
        threshold (str)                 : connectivity requiremen, can be in terms of log(N)
        output (str)                    : filename to store output
    """
    # (VR) Setting a really high recursion limit to prevent stack overflow errors
    sys.setrecursionlimit(1231231234)

    # (VR) Check -g and -k parameters for Leiden and IKC respectively
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1, "Leiden requires resolution"
        clusterer: Union[LeidenClusterer, IkcClusterer] = LeidenClusterer(resolution)
    elif clusterer_spec == ClustererSpec.leiden_mod:
        assert resolution == -1, "Leiden with modularity does not support resolution"
        clusterer = LeidenClusterer(resolution, quality=Quality.modularity)
    else:
        assert k != -1, "IKC requires k"
        clusterer = IkcClusterer(k)

    # (VR) Start hm01
    if not quiet:
        log = get_logger()
        context.with_working_dir(input + "_working_dir" if not working_dir else working_dir)
        log.info(
            f"starting hm01",
            input=input,
            working_dir=context.working_dir,
            clusterer=clusterer,
        )

    # (VR) Parse mincut threshold specification
    requirement = MincutRequirement.try_from_str(threshold)
    if not quiet:
        log.info(f"parsed connectivity requirement", requirement=requirement)

    time1 = time.time()

    # (VR) Load full graph into Graph object
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(input)
    if not quiet:
        log.info(
            f"loaded graph",
            n=nk_graph.numberOfNodes(),
            m=nk_graph.numberOfEdges(),
            elapsed=time.time() - time1,
        )
    root_graph = Graph(nk_graph, "")

    # (VR) Load clustering
    if not quiet:
        log.info(f"loading existing clustering before algorithm-g", clusterer=clusterer)
    clusters = clusterer.from_existing_clustering(existing_clustering)
    if not quiet:
        log.info(
            f"first round of clustering obtained",
            num_clusters=len(clusters),
            summary=summarize_graphs(clusters),
        )

    # Initialize return values
    with mp.Manager() as manager:
        new_clusters = manager.list()
        labels = manager.dict()

        if nodes:
            # (VR) Call the main CM algorithm
            new_clusters, labels, tree = algorithm_g(
                root_graph, clusters, clusterer, requirement, quiet, nodes
            )
        else:
            algorithm_g(
                root_graph, clusters, clusterer, requirement, quiet, nodes, new_clusters, labels, 8
            )
            tree = None

        time.sleep(2)

        # (VR) Retrieve output
        with open(output, "w+") as f:
            for n, cid in labels.items():
                f.write(f"{n} {cid}\n")

        if nodes:
            with open(output + ".tree.json", "w+") as f:
                f.write(cast(str, jsonpickle.encode(tree)))

            cm2universal(quiet, root_graph, tree, labels, output)

def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
