"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations

from typing import List, Optional, Tuple, Union, Dict, Deque, cast
from dataclasses import dataclass
from collections import deque
from enum import Enum
from itertools import chain
from structlog import get_logger

from queue import Queue

import logging
import logging.handlers

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

from copy import deepcopy

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

def bookkeeping_task(info_queue, quiet, root_graph, output):
    node_mapping = dict()
    labels = dict()

    tree = ts.Tree()

    my_pid = os.getpid()

    tasks_dict = {
        'add_tree_node': 0,
        'label': 0,
        'update_node_info': 0
    }

    while True:
        if not quiet:
            log = get_logger()
            log.debug("bookkeeping: next iteration", queue_size=info_queue.qsize(), pid=my_pid)

        item = info_queue.get()
        if item is None:
            if not quiet:
                log = get_logger()
                log.debug("bookkeeping process set free", pid=my_pid)
            info_queue.task_done()
            break
        
        info_type = item[0]
        tasks_dict[info_type] += 1
        if info_type == 'add_tree_node':
            _, parent_index, child_index, num_nodes = item

            new_node = ClusterTreeNode()
            new_node.label = child_index
            new_node.graph_index = child_index
            new_node.num_nodes = num_nodes
            new_node.extant = False

            node_mapping[child_index] = new_node

            if parent_index is None:
                tree.root = new_node
            else:
                parent_node = node_mapping[parent_index]
                parent_node.add_child(new_node)
        elif info_type == 'label':
            _, graph_index, nodes = item

            for node in nodes:
                labels[node] = graph_index
        elif info_type == 'update_node_info':
            _, graph_index, new_info = item
            node = node_mapping[graph_index]
            for field_name, field_value in new_info.items():
                setattr(node, field_name, field_value)

        info_queue.task_done()
        
    if not quiet:
        log = get_logger()
        log.debug("Finished bookkeeping, will save things now.")

    # (VR) Retrieve output
    with open(output, "w+") as f:
        for n, cid in labels.items():
            f.write(f"{n} {cid}\n")

    with open(output + ".tree.json", "w+") as f:
        f.write(cast(str, jsonpickle.encode(tree)))

    cm2universal(quiet, root_graph, tree, labels, output)


def par_task(
    queue, 
    requirement, 
    clusterer,
    global_graph,
    # ans,
    tree_tasks,
    quiet,
    print_lock=None):
    print_msg = functools.partial(print_msg_with_lock, print_lock)
    my_pid = os.getpid()

    while True:
        if not quiet:
            log = get_logger()
            log.debug("entered next iteration of loop", queue_size=queue.qsize(), pid=my_pid)

        intangible_subgraph = queue.get()
        if intangible_subgraph is None:
            if not quiet:
                log = get_logger()
                log.debug("process set free", pid=my_pid)
            queue.task_done()
            break

        if not quiet:
            log.debug(
                "popped graph",
                graph_n=intangible_subgraph.n(),
                graph_index=intangible_subgraph.index,
                pid=my_pid
            )

        # (VR) Mark nodes in popped cluster with their respective cluster ID
        tree_tasks.put(('label', intangible_subgraph.index, list(intangible_subgraph.nodes())))

        # (VR) If the current cluster is a singleton or empty, move on
        if intangible_subgraph.n() <= 1:
            queue.task_done()
            continue
        
        # (VR) Realize the set of nodes contained by the graph (i.e. construct its adjacency list)
        subgraph = intangible_subgraph.realize(global_graph)
        if not quiet:
            log = log.bind(
                g_id=subgraph.index,
                g_n=subgraph.n(),
                g_m=subgraph.m(),
                g_mcd=subgraph.mcd(),
                pid=my_pid
            )

        # (VR) Get minimum node degree in current cluster
        original_mcd = subgraph.mcd()

        # (VR) Pruning: Remove singletons with node degree under threshold until there exists none
        num_pruned = prune_graph(subgraph, requirement, clusterer)
        if num_pruned > 0:
            # (VR) Set the cluster cut size to the degree of the removed node
            tree_tasks.put((
                'update_node_info',
                subgraph.index,
                {
                    'cut_size': original_mcd,
                },
            ))
            if not quiet:
                log = log.bind(
                    g_id=subgraph.index,
                    g_n=subgraph.n(),
                    g_m=subgraph.m(),
                    g_mcd=subgraph.mcd()
                )
                log.info("pruned graph", num_pruned=num_pruned, pid=my_pid)

            # (VR) Create a TreeNodeCluster for the pruned cluster and set it as the current node's child
            tree_tasks.put(('add_tree_node', subgraph.index, f"{subgraph.index}δ", subgraph.n()))

            # (VR) "Iterate" to the new node
            subgraph.index = f"{subgraph.index}δ"

            tree_tasks.put(('label', subgraph.index, list(subgraph.nodes())))
        
        # (VR) If the current cluster post pruning is a singleton or empty, move on
        if subgraph.n() <= 1:
            queue.task_done()
            continue

        # (VR) Compute the mincut of the cluster
        mincut_res = subgraph.find_mincut()

        # is a cluster "cut-valid" -- having good connectivity?
        valid_threshold = requirement.validity_threshold(clusterer, subgraph)
        if not quiet:
            log.debug("calculated validity threshold", validity_threshold=valid_threshold, pid=my_pid)
            log.debug(
                "mincut computed",
                a_side_size=len(mincut_res.get_light_partition()),
                b_side_size=len(mincut_res.get_heavy_partition()),
                cut_size=mincut_res.get_cut_size(),
                pid=my_pid
            )

        # (VR) Set the current cluster's cut size
        tree_tasks.put((
            'update_node_info', 
            subgraph.index, 
            {
                'cut_size': mincut_res.get_cut_size(), 
                'validity_threshold': valid_threshold,
            },
        ))

        # (VR) If the cut size is below validity, split!
        if mincut_res.get_cut_size() <= valid_threshold and mincut_res.get_cut_size() > 0:
            # print_msg(f'{my_pid}: splitting graph')
            # (VR) Split partitions and set them as children nodes
            p1, p2 = subgraph.cut_by_mincut(mincut_res)

            tree_tasks.put(('add_tree_node', subgraph.index, p1.index, p1.n()))
            tree_tasks.put(('add_tree_node', subgraph.index, p2.index, p2.n()))

            # print_msg(f'{my_pid}: splitting done')
            # (VR) Cluster both partitions
            subp1 = list(clusterer.cluster_without_singletons(p1))
            subp2 = list(clusterer.cluster_without_singletons(p2))

            # (VR) Set clusters as children of the partitions
            for sg in subp1:
                tree_tasks.put(('add_tree_node', p1.index, sg.index, sg.n()))

            for sg in subp2:
                tree_tasks.put(('add_tree_node', p2.index, sg.index, sg.n()))

            # (VR) Add the new clusters to the stack
            # print_msg(f'{my_pid}: subp1 len: {len(subp1)}, subp2 len: {len(subp2)}')
            for g in subp1 + subp2:
                queue.put(g)

            if not quiet:
                log.info(
                    "cluster split",
                    num_a_side=len(subp1),
                    num_b_side=len(subp2),
                    summary_a_side=summarize_graphs(subp1),
                    summary_b_side=summarize_graphs(subp2),
                    pid=my_pid
                )
        else:
            # print_msg(f"{my_pid}: mincut_res: {mincut_res.get_cut_size()}, thresh: {valid_threshold}")
            # (VR) Compute the modularity of the cluster
            candidate = subgraph.to_intangible(global_graph)
            mod = global_graph.modularity_of(candidate)

            # (VR) Check if the modularity value is valid so that the answer can include the modified cluster
            if not isinstance(clusterer, IkcClusterer) or mod > 0:
                extant = True
                # ans.append(candidate)
                if not quiet:
                    log.info("cut valid, not splitting anymore", pid=my_pid)
            else:
                extant = False
                if not quiet:
                    log.info(
                        "cut valid, but modularity non-positive, thrown away",
                        modularity=mod,
                        pid=my_pid
                    )
            tree_tasks.put((
                'update_node_info', 
                subgraph.index, 
                {
                    'extant': extant, 
                },
            ))
        queue.task_done()
    
    if not quiet:
        log = get_logger()
        log.debug("process finished", pid=my_pid)

def algorithm_g(
    global_graph: Graph,
    graphs: List[IntangibleSubgraph],
    clusterer: Union[IkcClusterer, LeidenClusterer],
    requirement: MincutRequirement,
    quiet: bool,
    nodes: bool,
    # ans,
    output,
    num_cores: int = 4,
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:
    """ (VR) Main algorithm in hm01 
    
    Params:
        global_graph (Graph)                                : full graph from input
        graph (List[IntangibleSubgraph])                    : list of clusters
        clusterer (Union[IkcClusterer, LeidenClusterer])    : clustering algorithm
        requirement (MincutRequirement)                     : mincut connectivity requirement
    """
    if not quiet:
        log = get_logger()
        log.info("starting algorithm-g", queue_size=len(graphs))

    # Initialize queues of tasks
    tree_tasks = mp.JoinableQueue() # (VR) tree_tasks: list of logging tasks for CM + CM2Universal
    stack = mp.JoinableQueue()  # (VR) stack: the stack for cluster processing

    # Fill said queues
    tree_tasks.put(('add_tree_node', None, global_graph.index, global_graph.n()))
    for g in graphs:
        tree_tasks.put(('add_tree_node', global_graph.index, g.index, g.n()))
        stack.put(g)

    if not quiet:
        log.info("Queues Initialized", tree_tasks_size=tree_tasks.qsize(), stack_size=stack.qsize())

    tree_logging_worker = mp.Process(
        target=bookkeeping_task, 
        args=(
            tree_tasks, 
            quiet, 
            global_graph, 
            output,
        ),
    )

    print_lock = mp.Lock()
    workers = [
        mp.Process(target=par_task, args=(stack,requirement,clusterer,global_graph,tree_tasks,quiet,print_lock))
        for _ in range(num_cores)
    ]

    tree_logging_worker.start()
    tree_tasks.join()

    for worker in workers:
        worker.start()

    stack.join()
    tree_tasks.join()

    for _ in range(len(workers)):
        stack.put(None)
    tree_tasks.put(None)

    if not quiet:
        log = get_logger()
        log.debug("All workers sent None tasks")

    stack.join()
    tree_tasks.join()

    if not quiet:
        log = get_logger()
        log.debug("Task queues joined")

    tree_logging_worker.join()

    if not quiet:
        log = get_logger()
        log.debug("tree logger joined")

    for worker in workers:
        worker.join()

    if not quiet:
        log = get_logger()
        log.debug("all workers joined")


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

    algorithm_g(
        root_graph, clusters, clusterer, requirement, quiet, True, output, 8
    )


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
