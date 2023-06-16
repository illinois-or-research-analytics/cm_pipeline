"""The main CLI logic, containing also the main algorithm"""
from __future__ import annotations

from typing import List, Optional, Tuple, Union, Dict, cast
from enum import Enum
from structlog import get_logger

import typer
import time
import treeswift as ts
import networkit as nk
import jsonpickle
import sys

# (VR) Change: I removed the context import since we do everything in memory
# (VR) Change 2: I brought back context just for IKC
from context import context
from clusterers.ikc_wrapper import IkcClusterer
from clusterers.leiden_wrapper import LeidenClusterer, Quality
from mincut_requirement import MincutRequirement
from graph import Graph, IntangibleSubgraph, RealizedSubgraph
from pruner import prune_graph
from to_universal import cm2universal
from cluster_tree import ClusterTreeNode
from json2membership import json2membership

import multiprocessing as mp

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
    node.extant = False     # (VR) Def Extant: An input cluster that has remained untouched by CM (unpruned and uncut)
    node.cm_valid = True    # (VR) Def CM_Valid: A cluster that is in the final result, must have connectivity that fits the threshold

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

        # (VR) Pruning: Remove singletons with node degree under threshold until there exists none
        num_pruned = prune_graph(subgraph, requirement, clusterer)
        if num_pruned > 0:
            # (VR) Set the cluster cut size to the degree of the removed node
            tree_node.cut_size = original_mcd
            tree_node.extant = False                        # (VR) Change: The current cluster has been changed, so its not extant or CM valid anymore
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
            log.debug("calculated validity threshold", validity_threshold=valid_threshold)
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
        if mincut_res.get_cut_size() <= valid_threshold:    # and mincut_res.get_cut_size >= 0: -> (VR) Change: Commented this out to handle disconnected clusters
            tree_node.cm_valid = False                      # (VR) Change: The current cluster has been changed, so its not extant or CM valid anymore
            tree_node.extant = False
            
            # (VR) Split partitions and set them as children nodes
            p1, p2 = subgraph.cut_by_mincut(mincut_res)

            node_a = ClusterTreeNode()
            node_b = ClusterTreeNode()

            annotate_tree_node(node_a, p1)
            annotate_tree_node(node_b, p2)

            node_a.cm_valid = False                         # Change: These partitions are to be clustered, so they cannot be marked extant or CM valid
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
            for p, np in [(subp1, node_a), (subp2, node_b)]:
                for sg in p:
                    n = ClusterTreeNode()   
                    annotate_tree_node(n, sg)               # Change: Each cluster from the partiiton can be marked cm-valid but not extant
                    node_mapping[sg.index] = n
                    np.add_child(n)

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

    tree = ts.Tree()                                    # (VR) tree: Recursion tree that keeps track of clusters created by serial mincut/reclusters
    tree.root = ClusterTreeNode()                       # (VR) Give this tree an empty root
    annotate_tree_node(tree.root, global_graph)
    node_mapping: Dict[str, ClusterTreeNode] = {}       # (VR) node_mapping: maps cluster id to cluster tree node  
    node2cids: Dict[int, str] = {}                      # (VR) node2cids: Mapping between nodes and cluster ID  

    # (VR) Split data into parititions such that each core handles one partition
    mapping_split = [{} for _ in range(cores)]
    stacks = [[] for _ in range(cores)]
    labeling_split = [{} for _ in range(cores)]

    # (VR) Fill each partition
    for i, g in enumerate(graphs):
        n = ClusterTreeNode()
        annotate_tree_node(n, g)
        n.extant = True                                 # (VR) Input clusters are marked extant by default until they are changed
        node_mapping[g.index] = n
        mapping_split[i % cores][g.index] = n
        stacks[i % cores].append(g)

    # (VR) Map the algorithm to each partition
    with mp.Pool(cores) as p:
        out = p.starmap(par_task, list(zip(stacks, mapping_split, labeling_split)))

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

def main(
    input: str = typer.Option(..., "--input", "-i", help="The input network."),
    existing_clustering: str = typer.Option(..., "--existing-clustering", "-e", help="The existing clustering of the input network to be reclustered."),
    quiet: Optional[bool] = typer.Option(False, "--quiet", "-q", help="Silence output messages."), # (VR) Change: Removed working directory parameter since no FileIO occurs during runtime anymore
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c", help="Clustering algorithm used to obtain the existing clustering."),
    k: int = typer.Option(-1, "--k", "-k", help="(IKC Only) k parameter."),
    resolution: float = typer.Option(-1, "--resolution", "-g", help="(Leiden Only) Resolution parameter."),
    threshold: str = typer.Option("", "--threshold", "-t", help="Connectivity threshold which all clusters should be above."),
    output: str = typer.Option("", "--output", "-o", help="Output filename."),
    cores: int = typer.Option(4, "--nprocs", "-n", help="Number of cores to run in parallel."),
    first_tsv: bool = typer.Option(False, "--firsttsv", "-f", help="Output the tsv file that comes before CM2Universal and json2membership.")
):
    """ (VR) Connectivity-Modifier (CM). Take a network and cluster it ensuring cut validity """
    # (VR) Initialize shared global variables (TODO: Windows does not share globalised variables between processes, adjust this to allow SM on Windows)
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
        context.with_working_dir(input + "_working_dir")

    # (VR) Start hm01
    if not quiet:
        log = get_logger()      # (VR) Change: removed working dir initialization
        log.info(
            f"starting hm01",
            input=input,
            clusterer=clusterer,
        )

    # (VR) Parse mincut threshold specification
    requirement = MincutRequirement.try_from_str(threshold)
    if not quiet:
        log.info(f"parsed connectivity requirement", requirement=requirement)

    # (VR) Get the initial time for reporting the time it took to load the graph
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

    # (VR) Call the main CM algorithm

    # (VR) Start the timer for the algorithmic stage of CM
    if not quiet:
        time1 = time.perf_counter()

    labels, tree = algorithm_g(
        clusters, quiet, cores
    )

    # (VR) Log the output time for the algorithmic stage of CM
    if not quiet:
        log.info("CM algorithm completed", time_elapsed=time.perf_counter() - time1)

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
