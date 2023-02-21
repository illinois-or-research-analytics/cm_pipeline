from __future__ import annotations
from graph import RealizedSubgraph

from mincut_requirement import MincutRequirement
from clusterers.abstract_clusterer import AbstractClusterer
from heapdict import heapdict


def prune_graph(
    graph: RealizedSubgraph,
    connectivity_requirement: MincutRequirement,
    clusterer: AbstractClusterer,
) -> int:
    """ This stage comes before the mincut stage for each cluster. 
    Remove the single vertices that have degrees lower than the mincut requirement until there exists no such vertices.

    Params:
        graph (RealizedSubgraph)                        : Graph to prune
        connectivity_requirement (MincutRequirement)    : the mincut requirement
        clusterer (AbstractClusterer)                   : Clusterer used to create the subgraph (for determining validity of the threshold)
    """
    mcd = graph.mcd()
    if mcd > connectivity_requirement.validity_threshold(clusterer, graph):
        return 0
    deleted_nodes = 0
    degrees = heapdict()
    for node in graph.nodes():
        degrees[node] = graph.degree(node)
    while degrees:
        node, degree = degrees.popitem()
        if degree > connectivity_requirement.validity_threshold(
            clusterer, graph, mcd_override=degree
        ):
            break
        for neighbor in graph.neighbors(node):
            if neighbor in degrees:
                degrees[neighbor] -= 1
            else:
                # TODO: this else case should be not needed, but still kept here for defensive programming
                degrees[neighbor] = graph.degree(neighbor) - 1
        graph.remove_node(node)
        deleted_nodes += 1
    graph.mcd.cache_clear()
    return deleted_nodes
