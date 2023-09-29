from __future__ import annotations
from hm01.graph import RealizedSubgraph
from hm01.mincut_requirement import MincutRequirement
from hm01.clusterers.abstract_clusterer import AbstractClusterer
from heapdict import heapdict


def prune_graph(
    graph: RealizedSubgraph,
    connectivity_requirement: MincutRequirement,
    clusterer: AbstractClusterer,
) -> int:
    """ (VR) This stage comes before the mincut stage for each cluster. 
    Remove the single vertices that have degrees lower than the mincut requirement until there exists no such vertices.

    Params:
        graph (RealizedSubgraph)                        : Graph to prune
        connectivity_requirement (MincutRequirement)    : the mincut requirement
        clusterer (AbstractClusterer)                   : Clusterer used to create the subgraph (for determining validity of the threshold)
    """
    mcd = graph.mcd()
    if mcd > connectivity_requirement.validity_threshold(clusterer, graph): # (VR) If the mcd fits the threshold, no need to prune
        return 0
    
    deleted_nodes = 0                                                       # (VR) Keep count of the number of pruned nodes

    degrees = heapdict()                                                    # (VR) Heapdict automatically goes smallest to largest
    for node in graph.nodes():
        degrees[node] = graph.degree(node)

    while degrees:
        node, degree = degrees.popitem()
        if degree > connectivity_requirement.validity_threshold(            # (VR) If we hit a degree that fits the threshold, no need to prune
            clusterer, graph, mcd_override=degree
        ):
            break

        for neighbor in graph.neighbors(node):                              # (VR) Otherwise, adjust degrees and pop the node from the graph
            if neighbor in degrees:
                degrees[neighbor] -= 1
            else:
                # This else case should be not needed, but still kept here for defensive programming
                degrees[neighbor] = graph.degree(neighbor) - 1
        graph.remove_node(node)
        deleted_nodes += 1                                                  # (VR) Increment the number of pruned nodes

    graph.mcd.cache_clear()
    return deleted_nodes
