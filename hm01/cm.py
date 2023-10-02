# pylint: disable=missing-docstring, unused-variable, global-statement
# pylint: disable=global-variable-undefined, unused-argument, fixme
# pylint: disable=c-extension-no-member, invalid-name, import-error
"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations

import importlib
import json
import multiprocessing as mp
import os
import sys
import time
from enum import Enum
from itertools import chain
from multiprocessing import shared_memory
from typing import Dict, List, Optional, Tuple, cast

import jsonpickle
import networkit as nk
import numpy as np
import treeswift as ts
import typer
from hm01.cluster_tree import ClusterTreeNode
from hm01.clusterers.ikc_wrapper import IkcClusterer
from hm01.clusterers.leiden_wrapper import LeidenClusterer, Quality
# (VR) Change: I removed the context import since we do everything in memory
# (VR) Change 2: I brought back context just for IKC
from hm01.context import context
from hm01.graph import IntangibleSubgraph, RealizedSubgraph
from hm01.mincut_requirement import MincutRequirement
from hm01.pruner import prune_graph
from structlog import get_logger
from enum import Enum

# from json2membership import json2membership
# from to_universal import cm2universal


class ClustererSpec(str, Enum):
    """ (VR) Container for Clusterer Specification """
    leiden = "leiden"
    ikc = "ikc"
    leiden_mod = "leiden_mod"
    external = "external"


def summarize_graphs(graphs: List[IntangibleSubgraph]) -> str:
    """ (VR) Summarize graphs for logging purposes """
    if not graphs:
        return "[](empty)"
    if len(graphs) > 3:
        return f"[{graphs[0].index}, ..., {graphs[-1].index}]({len(graphs)})"
    else:
        return f"[{', '.join([g.index for g in graphs])}]({len(graphs)})"
    

def encode_to_26_ary(n):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    result = ''

    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = alphabet[remainder] + result

    return result


class ClusterInfo:

    class Task(Enum):
        PRUNE = 0
        MINCUT = 1
        CLUSTER = 2

    def __init__(
        self,
        parent_id: str,
        cluster_id: str,
        begin: int,
        end: int,
        task: Task,
    ):
        self.parent_id = parent_id
        self.cluster_id = cluster_id
        self.begin = begin
        self.end = end
        self.task = task
        self.cut_size: int | None = None
        self.validity_threshold: float | None = None
        self.disintegrated = False

def initialize_subgraph(
    nodes_global,
    adj_global,
    endpoints_global,
    begin,
    end,
    cluster_id,
):
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

    subgraph = RealizedSubgraph.from_adjlist(node_set, edges, cluster_id)
    return subgraph, node_set

def new_par_task(
    queue,
    data_queue,
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
        parent_id, cluster_id, begin, end, task = item
        cluster_info = ClusterInfo(parent_id, cluster_id, begin, end, task)

        # If the cluster is a singleton, nothing to be done here,
        # get another work item. Since singletons are being discarded,
        # this item is not even registered into the bookkeeping table.
        num_nodes = end - begin
        if num_nodes <= 1:
            queue.task_done()
            continue

        # Initialize the realized subgraph from shared mem structure
        subgraph, node_set = initialize_subgraph(
            nodes_global,
            adj_global,
            endpoints_global,
            begin,
            end,
            cluster_id,
        )

        if cluster_info.task == ClusterInfo.Task.PRUNE:

            # (VR) Get minimum node degree in current cluster
            original_mcd = subgraph.mcd()

            # (VR) Pruning: Remove singletons with node degree under threshold
            # until there exists none
            num_pruned = prune_graph(subgraph, requirement, clusterer)
            if num_pruned > 0:
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

            else:
                parent_id = cluster_info.parent_id
                cluster_id = cluster_info.cluster_id
                begin = cluster_info.begin
                end = cluster_info.end

            task = ClusterInfo.Task.MINCUT

            queue.put((parent_id, cluster_id, begin, end, task))

        elif cluster_info.task == ClusterInfo.Task.MINCUT:

            # (VR) Compute the mincut and validity threshold of the cluster
            mincut_res = subgraph.find_mincut()
            valid_threshold = requirement.validity_threshold(
                clusterer,
                subgraph,
            )

            # (VR) Set the current cluster's cut size
            cluster_info.cut_size = mincut_res[-1]
            cluster_info.validity_threshold = valid_threshold
            local_jobs.append(cluster_info)

            # (VR) If the cut size is above validity, we are done.
            # Else, split!
            if mincut_res[-1] <= valid_threshold:
                # (VR) Change: The current cluster has been changed,
                # so its not extant or CM valid anymore

                # (VR) Split partitions and set them as children nodes
                partitions = mincut_res[:-1]

                # For each subgraph resulting from a mincut/components operation,
                # create a new cluster info and
                # initialize sorted node lists
                cluster_info_children = []
                parent_node_set = subgraph.nodeset.copy()
                sorted_node_list = []

                parent_id = cluster_info.cluster_id

                task = ClusterInfo.Task.CLUSTER

                begin = cluster_info.begin
                for k, child_graph in enumerate(partitions):
                    child_node_set = set(child_graph)

                    parent_node_set -= child_node_set
                    sorted_node_list.extend(child_node_set)

                    cluster_id = parent_id + encode_to_26_ary(k+1)
                    end = begin + len(child_node_set)
                    child_cluster_info = ClusterInfo(
                        parent_id,
                        cluster_id,
                        begin,
                        end,
                        task
                    )
                    cluster_info_children.append(child_cluster_info)
                    begin = end

                # There shouldn't be extra singletons, but just in case
                # sorted_node_list.extend(list(parent_node_set))
                begin = cluster_info.begin
                end = cluster_info.end
                nodes_global[begin:end] = sorted_node_list

                # Put clustering jobs in the queue
                for item in cluster_info_children:
                    queue.put((
                        item.parent_id,
                        item.cluster_id,
                        item.begin,
                        item.end,
                        item.task
                    ))

        else:
            # (VR) Cluster both partitions
            subp1 = clusterer.cluster_without_singletons(subgraph)

            cl_count = 0

            # Stash the parent into the jobs array
            local_jobs.append(cluster_info)

            # For each subgraph resulting from a clustering operation,
            # create a new cluster info and
            # initialize sorted node lists
            cluster_info_children = []
            parent_node_set = subgraph.nodeset.copy()
            sorted_node_list = []

            parent_id = cluster_info.cluster_id
            begin = cluster_info.begin
            for k, child_graph in enumerate(subp1):
                child_node_set = child_graph.nodeset

                parent_node_set -= child_node_set
                sorted_node_list.extend(child_node_set)

                task = ClusterInfo.Task.PRUNE

                cluster_id = parent_id + str(k)
                end = begin + len(child_node_set)
                child_cluster_info = ClusterInfo(
                    parent_id,
                    cluster_id,
                    begin,
                    end,
                    task,
                )
                cluster_info_children.append(child_cluster_info)
                begin = end

                cl_count += 1

                del child_graph

            if cl_count == 0:
                cluster_info.disintegrated = True

            # Add the removed singletons to the original node list.
            sorted_node_list.extend(parent_node_set)
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
                    item.task,
                ))

        del subgraph, node_set
        queue.task_done()

    data_queue.put(local_jobs)


def algorithm_h(
    graphs: List[IntangibleSubgraph],
    nk_graph: nk.graph.Graph,
    quiet: bool,
    cores: int,
) -> Tuple[List[IntangibleSubgraph], Dict[int, str], ts.Tree]:

    if not quiet:
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
    data_queue = mp.Queue()

    begin = 0
    parent_id = ''  # Root node is the parent of the original clusters.
    task = ClusterInfo.Task.PRUNE
    for cluster_index, graph in enumerate(graphs):
        end = begin + len(graph.subset)
        nodes_array[begin:end] = graph.subset
        cluster_id = str(cluster_index)
        work_queue.put((parent_id, cluster_id, begin, end, task))

        begin = end

    # Create the workers.
    workers = []
    for _ in range(cores):
        worker = mp.Process(
            target=new_par_task,
            args=(
                work_queue,
                data_queue,
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

    work_queue.join()

    work_tables = []
    for _ in range(cores):
        work_tables.extend(data_queue.get())

    for worker in workers:
        worker.join()

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

        if entry.disintegrated:
            child_node.extant = False
            child_node.cm_valid = False

    # Mark extant clusters
    for child in root_node.children:
        child.extant = child.cm_valid               

    # Make the node2cids dict.
    node2cids = {}
    for tree_node in tree.traverse_leaves():
        if tree_node.cm_valid:
            for node_id in range(tree_node.begin, tree_node.end):
                node2cids[nodes_array[node_id]] = tree_node.graph_index

    shm.close()
    shm.unlink()

    shm_adj.close()
    shm_adj.unlink()

    shm_endpoints.close()
    shm_endpoints.unlink()

    return node2cids, tree


def load_clusterer(module_file, clusterer_args_str):
    spec=importlib.util.spec_from_file_location("clusterer", module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    kwargs = json.loads(clusterer_args_str)
    clusterer = module.get_clusterer(**kwargs)
    return clusterer


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
    # since no FileIO occurs during runtime anymore.
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
    clusterer_file: str = typer.Option(
        "",
        "--clusterer_file",
        "-cfile",
        help="If using an external clusterer, specify the file path to the clusterer object."
    ),
    clusterer_args: str = typer.Option(
        "",
        "--clusterer_args",
        "-cargs",
        help="If using an external clusterer, specify the arguments here.",
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
    # first_tsv: bool = typer.Option(
    #     False,
    #     "--firsttsv",
    #     "-f",
    #     help=
    #     "Output the tsv file that comes before CM2Universal and json2membership.",
    # ),
):
    """ (VR) Connectivity-Modifier (CM). 
    Take a network and cluster it ensuring cut validity."""

    # Edge case for empty output name
    if len(output) == 0:
        output = '.tsv'

    # (VR) Initialize shared global variables (TODO: Windows does not share
    # globalised variables between processes, adjust this to allow SM on Windows)
    global clusterer
    global requirement

    # (VR) Setting a really high recursion limit to prevent stack overflow errors
    sys.setrecursionlimit(1231231234)

    # (VR) Check -g and -k parameters for Leiden and IKC respectively
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1, "Leiden requires resolution"
        clusterer = LeidenClusterer(resolution)
    elif clusterer_spec == ClustererSpec.leiden_mod:
        assert resolution == -1, "Leiden with modularity does not support resolution"
        clusterer = LeidenClusterer(resolution, quality=Quality.modularity)
    elif clusterer_spec == ClustererSpec.ikc:
        assert k != -1, "IKC requires k"
        clusterer = IkcClusterer(k)
    else:
        assert clusterer_file != "", "File is required for external clusterers"
        # It is an external clusterer, load it.
        clusterer = load_clusterer(clusterer_file, clusterer_args)

    # (VR) Change get working dir iff IKC
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
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0, continuous=False)
    nk_graph = edgelist_reader.read(input_)
    if not quiet:
        log.info(
            "loaded graph",
            n=nk_graph.numberOfNodes(),
            m=nk_graph.numberOfEdges(),
            elapsed=time.time() - time1,
        )
    dehydrator = {int(k): v for k, v in edgelist_reader.getNodeMap().items()}
    hydrator = {v: k for k, v in dehydrator.items()}

    # (VR) Load clustering
    if not quiet:
        log.info(
            "loading existing clustering before algorithm-g",
            clusterer=clusterer,
        )
    clusters = clusterer.from_existing_clustering(existing_clustering)
    for cluster in clusters:
        cluster.subset = list(dehydrator[item] for item in cluster.subset)

    if not quiet:
        log.info(
            "first round of clustering obtained",
            num_clusters=len(clusters),
            summary=summarize_graphs(clusters),
        )

    # (VR) Call the main CM algorithm

    # (VR) Start the timer for the algorithmic stage of CM
    time1 = time.perf_counter()

    labels, tree = algorithm_h(clusters, nk_graph, quiet, cores)
    labels = {hydrator[k]: v for k, v in labels.items()}

    # (VR) Log the output time for the algorithmic stage of CM
    if not quiet:
        log.info(
            "CM algorithm completed",
            time_elapsed=time.perf_counter() - time1,
        )

    # (VR) Retrieve output if we want the original tsv
    # if first_tsv:
    with open(output, "w+", encoding='utf8') as f:
        for n, cid in labels.items():
            f.write(f"{n}\t{cid}\n")

    # (VR) Output the json data
    with open(output + ".tree.json", "w+", encoding='utf8') as f:
        f.write(cast(str, jsonpickle.encode(tree)))
    # cm2universal(quiet, tree, labels, output)

    # (VR) Convert the 'after' json into a tsv file with columns (node_id, cluster_id)
    # json2membership(output + ".after.json", output + ".after.tsv")


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
