from dataclasses import dataclass
from typing import List, Iterator, Dict, Union

from infomap import Infomap

from hm01.clusterers.abstract_clusterer import AbstractClusterer

from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph


@dataclass
class InfomapClusterer(AbstractClusterer):

    def cluster(self, graph: Union[Graph, RealizedSubgraph]) -> Iterator[IntangibleSubgraph]:
        """Returns a list of (labeled) subgraphs on the graph"""
        im = Infomap('--silent') # add options such as the level or the directed ness

        if graph.m() == 0:
            return []

        for u in graph.nodes():
            for v in graph.neighbors(u):
                im.add_link(u, v)
        im.run()
        cluster_dict = {}
        for node in im.tree:
            if node.is_leaf:
                if(node.module_id not in cluster_dict):
                    cluster_dict[node.module_id] = []
                cluster_dict[node.module_id].append(node.node_id)

        for local_cluster_id,cluster_member_arr in cluster_dict.items():
            yield graph.intangible_subgraph(
                cluster_member_arr, str(local_cluster_id)
            )
    
def get_clusterer():
    return InfomapClusterer()
