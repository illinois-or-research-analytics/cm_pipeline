"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations

from typing import List, Optional, Tuple, Union, Dict, Deque, cast
from dataclasses import dataclass
from collections import deque
from enum import Enum
from itertools import chain
from structlog import get_logger

import typer
import math
import time
import treeswift as ts
import networkit as nk
import jsonpickle

# UNCOMMENT IF INTERESTED IN SEEING PER-PROCESS MEM USAGE
# import psutil
# import os
# import tracemalloc

from clusterers.abstract_clusterer import AbstractClusterer
from clusterers.ikc_wrapper import IkcClusterer
from clusterers.leiden_wrapper import LeidenClusterer, Quality
from context import context
from mincut_requirement import MincutRequirement
from graph import Graph, IntangibleSubgraph, RealizedSubgraph
from pruner import prune_graph
from to_universal import cm2universal
from cluster_tree import ClusterTreeNode

import multiprocessing as mp
from multiprocessing.managers import BaseProxy

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
    node.extant = False     # Def Extant: An input cluster that has remained untouched by CM (unpruned and uncut)
    node.cm_valid = True    # Def CM_Valid: A cluster that is in the final result, must have connectivity that fits the threshold

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

def par_task(stack, node_mapping, node2cids):
    # (VR) Main algorithm loop: Recursively cut clusters in stack until they have mincut above threshold
    '''
    if label_only:
        stack, node2cids = entry
    else:
        stack, node_mapping, node2cids = entry
    '''
    # UNCOMMENT TO PRINT MEMORY USAGE
    # tracemalloc.clear_traces()
    # tracemalloc.reset_peak()
    # tracemalloc.start()
    while stack:
        if not quiet_g:
            log = get_logger()
            log.debug("entered next iteration of loop", queue_size=len(stack))
        
        intangible_subgraph = stack.pop()

        if not quiet_g:
            log.debug(
                "popped graph",
                graph_n=intangible_subgraph.n(),
                graph_index=intangible_subgraph.index,
            )

        # (VR) Mark nodes in popped cluster with their respective cluster ID
        update_cid_membership(intangible_subgraph, node2cids)

        # (VR) If the current cluster is a singleton or empty, move on
        if intangible_subgraph.n() <= 1:
            continue
        
        # (VR) Realize the set of nodes contained by the graph (i.e. construct its adjacency list)
        if isinstance(intangible_subgraph, IntangibleSubgraph):
            subgraph = intangible_subgraph.realize(global_graph)
        else:
            subgraph = intangible_subgraph

        # (VR) Get the current cluster tree node
        if not label_only:
            tree_node = node_mapping[subgraph.index]

        if not quiet_g:
            log = log.bind(
                g_id=subgraph.index,
                g_n=subgraph.n(),
                g_m=subgraph.m(),
                g_mcd=subgraph.mcd(),
            )
        
        # (VR) Get minimum node degree in current cluster
        original_mcd = subgraph.mcd()

        # (VR) Pruning: Remove singletons with node degree under threshold until there exists none
        num_pruned = prune_graph(subgraph, requirement, clusterer)
        if num_pruned > 0:
            # (VR) Set the cluster cut size to the degree of the removed node
            if not label_only:
                tree_node.cut_size = original_mcd
                tree_node.extant = False
                tree_node.cm_valid = False

            if not quiet_g:
                log = log.bind(
                    g_id=subgraph.index,
                    g_n=subgraph.n(),
                    g_m=subgraph.m(),
                    g_mcd=subgraph.mcd(),
                )
                log.info("pruned graph", num_pruned=num_pruned)

            # (VR) Create a TreeNodeCluster for the pruned cluster and set it as the current node's child
            if not label_only:
                new_child = ClusterTreeNode()
                subgraph.index = f"{subgraph.index}δ"

                annotate_tree_node(new_child, subgraph)

            if not label_only:
                tree_node.add_child(new_child)
                node_mapping[subgraph.index] = new_child

                # (VR) Iterate to the new node
                tree_node = new_child

            update_cid_membership(subgraph, node2cids)
        
        # (VR) Compute the mincut of the cluster
        mincut_res = subgraph.find_mincut()

        # is a cluster "cut-valid" -- having good connectivity?
        valid_threshold = requirement.validity_threshold(clusterer, subgraph)
        if not quiet_g:
            log.debug("calculated validity threshold", validity_threshold=valid_threshold)
            log.debug(
                "mincut computed",
                a_side_size=len(mincut_res.get_light_partition()),
                b_side_size=len(mincut_res.get_heavy_partition()),
                cut_size=mincut_res.get_cut_size(),
            )
        
        if not label_only:
            # (VR) Set the current cluster's cut size
            tree_node.cut_size = mincut_res.get_cut_size()
            tree_node.validity_threshold = valid_threshold

        # (VR) If the cut size is below validity, split!
        if mincut_res.get_cut_size() <= valid_threshold: # and mincut_res.get_cut_size >= 0: -> Commented this out to handle disconnected clusters
            if not label_only:
                tree_node.cm_valid = False
                tree_node.extant = False
            
            # (VR) Split partitions and set them as children nodes
            # print(mincut_res.get_cut_size())
            # print(mincut_res.get_light_partition())
            # print(mincut_res.get_heavy_partition())
            p1, p2 = subgraph.cut_by_mincut(mincut_res)
            # print(list(p1.nodes()), list(p2.nodes()))

            if not label_only:
                node_a = ClusterTreeNode()
                node_b = ClusterTreeNode()

                annotate_tree_node(node_a, p1)
                annotate_tree_node(node_b, p2)

                node_a.cm_valid = False
                node_b.cm_valid = False

                tree_node.add_child(node_a)
                tree_node.add_child(node_b)
                
                node_mapping[p1.index] = node_a
                node_mapping[p2.index] = node_b

            # (VR) Cluster both partitions
            subp1 = list(clusterer.cluster_without_singletons(p1))
            subp2 = list(clusterer.cluster_without_singletons(p2))
            subp1 = [s.realize(p1) for s in subp1]
            subp2 = [s.realize(p2) for s in subp2]

            # (VR) Set clusters as children of the partitions
            if not label_only:
                for p, np in [(subp1, node_a), (subp2, node_b)]:
                    for sg in p:
                        n = ClusterTreeNode()
                        annotate_tree_node(n, sg)
                        node_mapping[sg.index] = n
                        np.add_child(n)

            # (VR) Add the new clusters to the stack
            stack.extend(subp1)
            stack.extend(subp2)

            if not quiet_g:
                log.info(
                    "cluster split",
                    num_a_side=len(subp1),
                    num_b_side=len(subp2),
                    summary_a_side=summarize_graphs(subp1),
                    summary_b_side=summarize_graphs(subp2),
                )
        # else:
            # (VR) Compute the modularity of the cluster
            # candidate = subgraph.to_intangible(global_graph)
            # mod = global_graph.modularity_of(candidate)

            # (VR) Check if the modularity value is valid so that the answer can include the modified cluster
            # if (not isinstance(clusterer, IkcClusterer)) or mod > 0:
                # ans.append(candidate)
            #     if not label_only:
            #         node_mapping[subgraph.index].extant = True
            #     if not quiet_g:
            #         log.info("cut valid, not splitting anymore")
            # else:
            #     if not label_only:
            #         node_mapping[subgraph.index].extant = False
            #     if not quiet_g:
            #         log.info(
            #             "cut valid, but modularity non-positive, thrown away",
            #             modularity=mod,
            #         )
    # current, peak = tracemalloc.get_traced_memory()
    # print(f"{os.getpid()}: Current memory usage is {current / 10**3}KB; Peak was {peak / 10**6}MB; Diff = {(peak - current) / 10**6}MB; USS={psutil.Process(os.getpid()).memory_full_info().uss / 1024 ** 2}MB")
    # tracemalloc.stop()
    if label_only:
        return (None, node2cids)
    else:     
        return (node_mapping, node2cids)

def algorithm_g(
    graphs: List[IntangibleSubgraph],
    quiet: bool,
    cores: int
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:
    """ (VR) Main algorithm in hm01 
    
    Params:
        global_graph (Graph)                                : full graph from input
        graph (List[IntangibleSubgraph])                    : list of clusters
        clusterer (Union[IkcClusterer, LeidenClusterer])    : clustering algorithm
        requirement (MincutRequirement)                     : mincut connectivity requirement
    """
    # Share quiet variable with processes
    global quiet_g
    quiet_g = quiet

    if not quiet:
        log = get_logger()
        log.info("starting algorithm-g", queue_size=len(graphs))

    if not label_only:
        tree = ts.Tree()                                # (VR) tree: Recursion tree that keeps track of clusters created by serial mincut/reclusters
        tree.root = ClusterTreeNode()
        annotate_tree_node(tree.root, global_graph)
        node_mapping: Dict[str, ClusterTreeNode] = {}   # (VR) node_mapping: maps cluster id to cluster tree node  

    node2cids: Dict[int, str] = {}                      # (VR) node2cids: Mapping between nodes and cluster ID  

    # Split data into parititions such that each core handles one partition
    mapping_split = [{} for _ in range(cores)] if not label_only else [None]*cores
    stacks = [[] for _ in range(cores)]
    labeling_split = [{} for _ in range(cores)]

    # Fill each partition
    for i, g in enumerate(graphs):
        if not label_only:
            n = ClusterTreeNode()
            annotate_tree_node(n, g)
            n.extant = True
            node_mapping[g.index] = n
            mapping_split[i % cores][g.index] = n
        stacks[i % cores].append(g)

    # Map the algorithm to each partition
    with mp.Pool(cores) as p:
        if not label_only:
            out = p.starmap(par_task, list(zip(stacks, mapping_split, labeling_split)))
        else:
            out = p.starmap(par_task, list(zip(stacks, mapping_split, labeling_split)))

    # Merge partitions into single return data
    for mapping, label_part in out:
        if mapping is not None:
            node_mapping.update(mapping)
        node2cids.update(label_part)

    if not label_only:
        # Add each initial clustering node as children of the tree root
        for g in graphs:
            n = node_mapping[g.index]
            tree.root.add_child(n)

        return node2cids, tree
    else:
        return node2cids

def main(
    input: str = typer.Option(..., "--input", "-i"),
    existing_clustering: str = typer.Option(..., "--existing-clustering", "-e"),
    quiet: Optional[bool] = typer.Option(False, "--quiet", "-q"),
    working_dir: Optional[str] = typer.Option("", "--working-dir", "-d"),
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),
    threshold: str = typer.Option("", "--threshold", "-t"),
    output: str = typer.Option("", "--output", "-o"),
    cores: int = typer.Option(4, "--nprocs", "-n"),
    labelonly: bool = typer.Option(False, "--labelonly", "-l")
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
    # Initialize shared global variables (TODO: Find alternative for people running on Windows)
    global clusterer
    global requirement
    global global_graph
    global label_only

    # (VR) Setting a really high recursion limit to prevent stack overflow errors
    sys.setrecursionlimit(1231231234)

    # (VR) Check -g and -k parameters for Leiden and IKC respectively
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1, "Leiden requires resolution"
        clusterer = LeidenClusterer(resolution)
    elif clusterer_spec == ClustererSpec.leiden_mod:
        assert resolution == -1, "Leiden with modularity does not support resolution"
        clusterer = LeidenClusterer(resolution, quality=Quality.modularity)
    else:
        assert k != -1, "IKC requires k"
        clusterer = IkcClusterer(k)

    # (VR) Start hm01
    if not quiet:
        log = get_logger()
        # context.with_working_dir(input + "_working_dir" if not working_dir else working_dir)
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

    global_graph = Graph(nk_graph, "")

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

    label_only = labelonly

    # (VR) Call the main CM algorithm

    # UNCOMMENT TO TIME JUST THE CM ALGO
    # time1 = time.perf_counter()

    if not labelonly:
        labels, tree = algorithm_g(
            clusters, quiet, cores
        )
    else:
        labels = algorithm_g(
            clusters, quiet, cores
        )

    # print(time.perf_counter() - time1)

    # (VR) Retrieve output
    with open(output, "w+") as f:
        for n, cid in labels.items():
            f.write(f"{n} {cid}\n")
    
    if not labelonly:
        with open(output + ".tree.json", "w+") as f:
            f.write(cast(str, jsonpickle.encode(tree)))

        cm2universal(quiet, global_graph, tree, labels, output)

def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
