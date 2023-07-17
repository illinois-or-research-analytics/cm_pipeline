# pylint: disable=missing-docstring, unused-variable, global-statement
# pylint: disable=global-variable-undefined, unused-argument, fixme
# pylint: disable=c-extension-no-member, invalid-name, import-error
"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations

import multiprocessing as mp
import os
import sys
import time
from enum import Enum
from itertools import chain
from multiprocessing import shared_memory
from typing import Dict, List, Optional, Tuple, Union, cast

import jsonpickle
import networkit as nk
import numpy as np
import treeswift as ts
import typer
from cluster_tree import ClusterTreeNode
from clusterers.ikc_wrapper import IkcClusterer
from clusterers.leiden_wrapper import LeidenClusterer, Quality
# (VR) Change: I removed the context import since we do everything in memory
# (VR) Change 2: I brought back context just for IKC
from context import context
from graph import Graph, IntangibleSubgraph, RealizedSubgraph
from mincut_requirement import MincutRequirement
from pruner import prune_graph
from structlog import get_logger

from json2membership import json2membership
from to_universal import cm2universal


class ClustererSpec(str, Enum):
    """ (VR) Container for Clusterer Specification """
    leiden = "leiden"
    ikc = "ikc"
    leiden_mod = "leiden_mod"


def annotate_tree_node(
    node: ClusterTreeNode,
    graph: Union[Graph, IntangibleSubgraph, RealizedSubgraph],
):
    """ (VR) Labels a ClusterTreeNode with its respective cluster """

    # (VR) Def Extant: An input cluster that has remained untouched by CM
    #   (unpruned and uncut).
    # (VR) Def CM_Valid: A cluster that is in the final result,
    #   must have connectivity that fits the threshold.
    node.label = graph.index
    node.graph_index = graph.index
    node.num_nodes = graph.n()
    node.extant = False
    node.cm_valid = True


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
    # (VR) Main algorithm loop: Recursively cut clusters in stack
    # until they have mincut above threshold.
    while stack:
        if not quiet_g:
            log = get_logger()
            log.debug("entered next iteration of loop", queue_size=len(stack))

        # (VR) Get the next cluster to operate on
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
        tree_node = node_mapping[subgraph.index]

        # (VR) Log current cluster data after realization
        if not quiet_g:
            log = log.bind(
                g_id=subgraph.index,
                g_n=subgraph.n(),
                g_m=subgraph.m(),
                g_mcd=subgraph.mcd(),
            )

        # (VR) Get minimum node degree in current cluster
        original_mcd = subgraph.mcd()

        # (VR) Pruning: Remove singletons with node degree under threshold
        # until there exists none
        num_pruned = prune_graph(subgraph, requirement, clusterer)
        if num_pruned > 0:
            # (VR) Set the cluster cut size to the degree of the removed node
            tree_node.cut_size = original_mcd

            # (VR) Change: The current cluster has been changed,
            # so its not extant or CM valid anymore
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

            # (VR) Create a TreeNodeCluster for the pruned cluster
            # and set it as the current node's child.
            new_child = ClusterTreeNode()
            subgraph.index = f"{subgraph.index}δ"
            annotate_tree_node(new_child, subgraph)
            tree_node.add_child(new_child)
            node_mapping[subgraph.index] = new_child

            # (VR) Iterate to the new node
            tree_node = new_child
            update_cid_membership(subgraph, node2cids)

        # (VR) Compute the mincut and validity threshold of the cluster
        mincut_res = subgraph.find_mincut()
        valid_threshold = requirement.validity_threshold(clusterer, subgraph)
        if not quiet_g:
            log.debug(
                "calculated validity threshold",
                validity_threshold=valid_threshold,
            )
            log.debug(
                "mincut computed",
                a_side_size=len(mincut_res.get_light_partition()),
                b_side_size=len(mincut_res.get_heavy_partition()),
                cut_size=mincut_res.get_cut_size(),
            )

        # (VR) Set the current cluster's cut size
        tree_node.cut_size = mincut_res.get_cut_size()
        tree_node.validity_threshold = valid_threshold

        # (VR) If the cut size is below validity, split!
        if mincut_res.get_cut_size() <= valid_threshold:
            # and mincut_res.get_cut_size >= 0: ->
            # (VR) Change: Commented this out to handle disconnected clusters

            # (VR) Change: The current cluster has been changed,
            # so its not extant or CM valid anymore
            tree_node.cm_valid = False
            tree_node.extant = False

            # (VR) Split partitions and set them as children nodes
            p1, p2 = subgraph.cut_by_mincut(mincut_res)

            node_a = ClusterTreeNode()
            node_b = ClusterTreeNode()

            annotate_tree_node(node_a, p1)
            annotate_tree_node(node_b, p2)

            # Change: These partitions are to be clustered,
            # so they cannot be marked extant or CM valid.
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
            for p, np_ in [(subp1, node_a), (subp2, node_b)]:
                for sg in p:
                    n = ClusterTreeNode()
                    # Change: Each cluster from the partition can be marked
                    # cm-valid but not extant.
                    annotate_tree_node(n, sg)
                    node_mapping[sg.index] = n
                    np_.add_child(n)

            # (VR) Add the new clusters to the stack
            stack.extend(subp1)
            stack.extend(subp2)

            # (VR) Log the partitions
            if not quiet_g:
                log.info(
                    "cluster split",
                    num_a_side=len(subp1),
                    num_b_side=len(subp2),
                    summary_a_side=summarize_graphs(subp1),
                    summary_b_side=summarize_graphs(subp2),
                )
        else:
            if not quiet_g:
                log.info("cut valid, not splitting anymore")

    return (node_mapping, node2cids)


def algorithm_g(
        graphs: List[IntangibleSubgraph], quiet: bool, cores: int
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

    tree = ts.Tree(
    )  # (VR) tree: Recursion tree that keeps track of clusters created by serial mincut/reclusters
    tree.root = ClusterTreeNode()  # (VR) Give this tree an empty root
    annotate_tree_node(tree.root, global_graph)
    node_mapping: Dict[str, ClusterTreeNode] = {
    }  # (VR) node_mapping: maps cluster id to cluster tree node
    node2cids: Dict[int, str] = {
    }  # (VR) node2cids: Mapping between nodes and cluster ID

    # (VR) Split data into parititions such that each core handles one partition
    mapping_split = [{} for _ in range(cores)]
    stacks = [[] for _ in range(cores)]
    labeling_split = [{} for _ in range(cores)]

    # (VR) Fill each partition
    for i, g in enumerate(graphs):
        n = ClusterTreeNode()
        annotate_tree_node(n, g)
        n.extant = True  # (VR) Input clusters are marked extant by default until they are changed
        node_mapping[g.index] = n
        mapping_split[i % cores][g.index] = n
        stacks[i % cores].append(g)

    # (VR) Map the algorithm to each partition
    with mp.Pool(cores) as p:
        out = p.starmap(par_task,
                        list(zip(stacks, mapping_split, labeling_split)))

    # (VR) Merge partitions into single return data
    for mapping, label_part in out:
        if mapping is not None:
            node_mapping.update(mapping)
        node2cids.update(label_part)

    # (VR) Add each initial clustering node as children of the tree root
    for g in graphs:
        n = node_mapping[g.index]
        tree.root.add_child(n)

    return node2cids, tree


class ClusterInfo:

    def __init__(self, parent_id, cluster_id, begin, end):
        self.parent_id: str = parent_id
        self.cluster_id: str = cluster_id
        self.begin: int = begin
        self.end: int = end
        self.cut_size: int | None = None
        self.validity_threshold: float | None = None


def new_par_task(
    queue,
    shm,
    shm_adj,
    shm_endpoints,
    num_nodes,
    num_edges,
    dtype,
):
    nodes_global = np.ndarray(
        shape=(num_nodes, ),
        dtype=dtype,
        buffer=shm.buf,
    )
    adj_global = np.ndarray(
        shape=(num_nodes + 1, ),
        dtype=dtype,
        buffer=shm_adj.buf,
    )
    endpoints_global = np.ndarray(
        shape=(2 * num_edges, ),
        dtype=dtype,
        buffer=shm_endpoints.buf,
    )

    # Bookkeeping table.
    local_jobs = []

    while True:
        item = queue.get()
        if item is None:
            queue.task_done()
            break

        # A job (a cluster) has been accepted.
        # Must place it into local_jobs (the bookkeeping table) once done
        # with the cluster.
        parent_id, cluster_id, begin, end = item
        cluster_info = ClusterInfo(parent_id, cluster_id, begin, end)

        # If the cluster is a singleton, nothing to be done here,
        # get another work item. Since singletons are being discarded,
        # this item is not even registered into the bookkeeping table.
        num_nodes = end - begin
        if num_nodes <= 1:
            queue.task_done()
            continue

        #
        # Make the nodes list and cluster edges dictionary.
        #
        node_set = set(nodes_global[begin:end].tolist())

        edges = {}
        for node_a in node_set:
            endpoints = []

            # Locate neighbors of node_a that are in the node_set.
            begin = adj_global[node_a]
            end = adj_global[node_a + 1]
            for node_b in endpoints_global[begin:end]:
                if node_b in node_set:
                    endpoints.append(node_b)

            edges[node_a] = endpoints

        # make pruner, etc.
        subgraph = RealizedSubgraph.from_adjlist(node_set, edges, cluster_id)

        # (VR) Get minimum node degree in current cluster
        original_mcd = subgraph.mcd()

        # (VR) Pruning: Remove singletons with node degree under threshold
        # until there exists none
        num_pruned = prune_graph(subgraph, requirement, clusterer)
        if num_pruned > 0:
            # TODO: Cut size might not actually be mcd, but just the degree
            cluster_info.cut_size = original_mcd

            # Now, rearrange the nodes to separate the pruned nodes from the
            # surviving nodes.
            surviving_node_set = subgraph.nodeset
            pruned_node_set = node_set - surviving_node_set

            begin = cluster_info.begin
            end = cluster_info.end

            nodes_global[begin:end] = \
                list(surviving_node_set) + list(pruned_node_set)

            # A cluster has been processed, move on to the cluster of
            # surviving nodes.
            local_jobs.append(cluster_info)

            parent_id = cluster_info.cluster_id
            cluster_id = parent_id + 'δ'
            end = begin + len(surviving_node_set)

            subgraph.index = cluster_id

            cluster_info = ClusterInfo(parent_id, cluster_id, begin, end)

        # (VR) Compute the mincut and validity threshold of the cluster
        mincut_res = subgraph.find_mincut()
        valid_threshold = requirement.validity_threshold(clusterer, subgraph)

        # (VR) Set the current cluster's cut size
        cluster_info.cut_size = mincut_res.get_cut_size()
        cluster_info.validity_threshold = valid_threshold
        local_jobs.append(cluster_info)

        # (VR) If the cut size is above validity, we are done.
        # Else, split!
        if mincut_res.get_cut_size() <= valid_threshold:
            # (VR) Change: The current cluster has been changed,
            # so its not extant or CM valid anymore

            # (VR) Split partitions and set them as children nodes
            p1, p2 = subgraph.cut_by_mincut(mincut_res)

            begin = cluster_info.begin
            end = cluster_info.end
            nodes_global[begin:end] = list(p1.nodeset) + list(p2.nodeset)

            parent_id = cluster_info.cluster_id

            cluster_id_a = parent_id + 'a'
            begin_a = cluster_info.begin
            end_a = begin_a + len(p1.nodeset)
            cluster_info_a = ClusterInfo(
                parent_id,
                cluster_id_a,
                begin_a,
                end_a,
            )
            local_jobs.append(cluster_info_a)

            cluster_id_b = parent_id + 'b'
            begin_b = end_a
            end_b = cluster_info.end
            cluster_info_b = ClusterInfo(
                parent_id,
                cluster_id_b,
                begin_b,
                end_b,
            )
            local_jobs.append(cluster_info_b)

            # (VR) Cluster both partitions
            subp1 = list(clusterer.cluster_without_singletons(p1))
            subp2 = list(clusterer.cluster_without_singletons(p2))

            sorted_node_list = []
            cluster_info_children = []
            parent_node_set = subgraph.nodeset.copy()

            for child_graph_list, parent_cluster_info in [
                (subp1, cluster_info_a), (subp2, cluster_info_b)
            ]:
                parent_id = parent_cluster_info.cluster_id
                begin = parent_cluster_info.begin
                for k, child_graph in enumerate(child_graph_list):
                    child_node_set = child_graph.nodeset

                    parent_node_set -= child_node_set
                    sorted_node_list.extend(list(child_node_set))

                    cluster_id = parent_id + str(k)
                    end = begin + len(child_node_set)
                    child_cluster_info = ClusterInfo(
                        parent_id,
                        cluster_id,
                        begin,
                        end,
                    )
                    cluster_info_children.append(child_cluster_info)
                    begin = end

            # Add the removed singletons to the original node list.
            sorted_node_list.extend(list(parent_node_set))
            begin = cluster_info.begin
            end = cluster_info.end
            nodes_global[begin:end] = sorted_node_list

            # Place the jobs on the queue.
            for item in cluster_info_children:
                queue.put((
                    item.parent_id,
                    item.cluster_id,
                    item.begin,
                    item.end,
                ))

        queue.task_done()

    queue.put(local_jobs)


def algorithm_h(
    graphs: List[IntangibleSubgraph],
    nk_graph: nk.graph.Graph,
    quiet: bool,
    cores: int,
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:

    print(f'process {os.getpid()} is the master')

    num_nodes = nk_graph.numberOfNodes()
    num_edges = nk_graph.numberOfEdges()

    dtype = np.uint64

    # Make the shared memory for the node list.
    # TODO: document the node list structure.
    memory_size = num_nodes * dtype(0).itemsize
    shm = shared_memory.SharedMemory(create=True, size=memory_size)

    # Make the shared memory for the adjacency list structure.
    # TODO: document the adjacency list structure.
    len_adj = num_nodes + 1
    memory_size = len_adj * dtype(0).itemsize
    shm_adj = shared_memory.SharedMemory(create=True, size=memory_size)

    len_endpoints = 2 * num_edges
    memory_size = len_endpoints * dtype(0).itemsize
    shm_endpoints = shared_memory.SharedMemory(create=True, size=memory_size)

    # Populate the adjacency list.
    node_degrees = [nk_graph.degree(k) for k in range(num_nodes)]
    adj_list_content = [0] + np.cumsum(node_degrees).tolist()

    adj = np.ndarray(shape=(len_adj, ), dtype=dtype, buffer=shm_adj.buf)
    adj[:] = adj_list_content

    # Populate the endpoints list.
    node_neighbors = [ \
        list(nk_graph.iterNeighbors(node)) for node in range(num_nodes) \
    ]
    endpoints_list_content = list(chain.from_iterable(node_neighbors))

    endpoints = np.ndarray(
        shape=(len_endpoints, ),
        dtype=dtype,
        buffer=shm_endpoints.buf,
    )
    endpoints[:] = endpoints_list_content

    # Place all work on the stack and the nodes on the shared memory.
    nodes_array = np.ndarray(shape=(num_nodes, ), dtype=dtype, buffer=shm.buf)

    work_queue = mp.JoinableQueue()

    begin = 0
    for cluster_index, graph in enumerate(graphs):
        end = begin + len(graph.subset)
        nodes_array[begin:end] = graph.subset

        # (parent_id, cluster_id, begin, end)
        work_queue.put(('', str(cluster_index), begin, end))

        begin = end

    # Create the workers.
    workers = []
    for _ in range(cores):
        worker = mp.Process(
            target=new_par_task,
            args=(
                work_queue,
                shm,
                shm_adj,
                shm_endpoints,
                num_nodes,
                num_edges,
                dtype,
            ),
        )
        workers.append(worker)

    for worker in workers:
        worker.start()

    work_queue.join()

    # Place the sentinels to signal to the workers that no more tasks
    # will come.
    for _ in range(cores):
        work_queue.put(None)

    for worker in workers:
        worker.join()

    work_tables = []
    for _ in range(cores):
        work_tables.extend(work_queue.get())

    # Construct the tree nodes
    node_mapping = {
        item.cluster_id:
        ClusterTreeNode(
            item.cluster_id,
            item.end - item.begin,
            item.begin,
            item.end,
            item.cut_size,
            item.validity_threshold,
        )
        for item in work_tables
    }
    root_node = ClusterTreeNode('', num_nodes, 0, num_nodes, None, None)
    node_mapping[''] = root_node

    tree = ts.Tree()
    tree.root = root_node

    # Link the tree nodes to each other
    for entry in work_tables:
        parent_id = entry.parent_id
        child_id = entry.cluster_id
        parent_node = node_mapping[parent_id]
        child_node = node_mapping[child_id]
        parent_node.add_child(child_node)
        parent_node.cm_valid = False

    # Mark extant clusters
    for child in root_node.children:
        child.extant = child.cm_valid

    # Make the node2cids dict.
    node2cids = {}
    for tree_node in tree.traverse_leaves():
        if tree_node.cm_valid:
            for node_id in range(tree_node.begin, tree_node.end):
                node2cids[node_id] = tree_node.graph_index

    shm.close()
    shm.unlink()

    shm_adj.close()
    shm_adj.unlink()

    shm_endpoints.close()
    shm_endpoints.unlink()

    return node2cids, tree

def main(
    input_: str = typer.Option(
        ...,
        "--input",
        "-i",
        help="The input network.",
    ),
    existing_clustering: str = typer.Option(
        ...,
        "--existing-clustering",
        "-e",
        help="The existing clustering of the input network to be reclustered.",
    ),
    # (VR) Change: Removed working directory parameter
    # since no FileIO occurs during runtime aputnymore.
    quiet: Optional[bool] = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Silence output messages.",
    ),
    clusterer_spec: ClustererSpec = typer.Option(
        ...,
        "--clusterer",
        "-c",
        help="Clustering algorithm used to obtain the existing clustering.",
    ),
    k: int = typer.Option(
        -1,
        "--k",
        "-k",
        help="(IKC Only) k parameter.",
    ),
    resolution: float = typer.Option(
        -1,
        "--resolution",
        "-g",
        help="(Leiden Only) Resolution parameter.",
    ),
    threshold: str = typer.Option(
        "",
        "--threshold",
        "-t",
        help="Connectivity threshold which all clusters should be above.",
    ),
    output: str = typer.Option(
        "",
        "--output",
        "-o",
        help="Output filename.",
    ),
    cores: int = typer.Option(
        4,
        "--nprocs",
        "-n",
        help="Number of cores to run in parallel.",
    ),
    first_tsv: bool = typer.Option(
        False,
        "--firsttsv",
        "-f",
        help=
        "Output the tsv file that comes before CM2Universal and json2membership.",
    ),
):
    """ (VR) Connectivity-Modifier (CM). 
    Take a network and cluster it ensuring cut validity."""

    # (VR) Initialize shared global variables (TODO: Windows does not share
    # globalised variables between processes, adjust this to allow SM on Windows)
    global clusterer
    global requirement
    global global_graph

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

    # (VR) Change get working dir iff IKC
    if isinstance(clusterer, IkcClusterer):
        context.with_working_dir(input_.split('/')[-1] + "_working_dir")

    # (VR) Start hm01
    if not quiet:
        log = get_logger()  # (VR) Change: removed working dir initialization
        log.info(
            "starting hm01",
            input=input_,
            clusterer=clusterer,
        )

    # (VR) Parse mincut threshold specification
    requirement = MincutRequirement.try_from_str(threshold)
    if not quiet:
        log.info("parsed connectivity requirement", requirement=requirement)

    # (VR) Get the initial time for reporting the time it took to load the graph
    time1 = time.time()

    # (VR) Load full graph into Graph object
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(input_)
    if not quiet:
        log.info(
            "loaded graph",
            n=nk_graph.numberOfNodes(),
            m=nk_graph.numberOfEdges(),
            elapsed=time.time() - time1,
        )
    global_graph = Graph(nk_graph, "")

    # (VR) Load clustering
    if not quiet:
        log.info("loading existing clustering before algorithm-g",
                 clusterer=clusterer)
    clusters = clusterer.from_existing_clustering(existing_clustering)
    if not quiet:
        log.info(
            "first round of clustering obtained",
            num_clusters=len(clusters),
            summary=summarize_graphs(clusters),
        )

    # (VR) Call the main CM algorithm

    # (VR) Start the timer for the algorithmic stage of CM
    if not quiet:
        time1 = time.perf_counter()

    labels, tree = algorithm_h(clusters, nk_graph, quiet, cores)

    # (VR) Log the output time for the algorithmic stage of CM
    if not quiet:
        log.info("CM algorithm completed",
                 time_elapsed=time.perf_counter() - time1)

    # (VR) Retrieve output if we want the original tsv
    if first_tsv:
        with open(output, "w+") as f:
            for n, cid in labels.items():
                f.write(f"{n} {cid}\n")

    # (VR) Output the json data
    with open(output + ".tree.json", "w+") as f:
        f.write(cast(str, jsonpickle.encode(tree)))
    cm2universal(quiet, tree, labels, output)

    # (VR) Convert the 'after' json into a tsv file with columns (node_id, cluster_id)
    json2membership(output + ".after.json", output + ".after.tsv")


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
