from dataclasses import dataclass
from typing import List, Iterator, Dict, Union

import graph_tool.all as gt

from hm01.clusterers.abstract_clusterer import AbstractClusterer

from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph


@dataclass
class SBMClusterer(AbstractClusterer):

    def __init__(self, **kwargs):
        self.block_state = kwargs["block_state"]
        self.degree_corrected = kwargs["degree_corrected"]

    def cluster(self, graph: Union[Graph, RealizedSubgraph]) -> Iterator[IntangibleSubgraph]:
        """Returns a list of (labeled) subgraphs on the graph"""
        sbm_graph = gt.Graph(directed=False)

        if graph.m() == 0:
            return []

        def edge_list_iterable():
            for u in graph.nodes():
                for v in graph.neighbors(u):
                    yield u,v
        vpm_name = sbm_graph.add_edge_list(edge_list_iterable(), hashed=True, hash_type="int")

        sbm_clustering = None
        if self.block_state == "non_nested_sbm":
            if self.degree_corrected:
                sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state=gt.BlockState, state_args={"deg_corr": True})
            else:
                sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state=gt.BlockState, state_args={"deg_corr": False})
        elif self.block_state == "planted_partition_model":
            sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state=gt.PPBlockState)

        if not sbm_clustering:
            return []

        block_membership = sbm_clustering.get_blocks()

        cluster_dict = {}
        for new_node_id in sbm_graph.vertices():
            current_cluster_id = block_membership[new_node_id]
            if(current_cluster_id not in cluster_dict):
                cluster_dict[current_cluster_id] = []
            cluster_dict[current_cluster_id].append(vpm_name[new_node_id])

        for local_cluster_id,cluster_member_arr in cluster_dict.items():
            yield graph.intangible_subgraph(
                cluster_member_arr, str(local_cluster_id)
            )

    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        # node_id cluster_id format
        clusters: Dict[str, IntangibleSubgraph] = {}
        with open(filepath) as f:
            for line in f:
                node_id, cluster_id = line.split()
                clusters.setdefault(
                    cluster_id, IntangibleSubgraph([], cluster_id)
                ).subset.append(int(node_id))
        return list(v for v in clusters.values() if v.n() > 1)

def get_clusterer(**kwargs):
    return SBMClusterer(**kwargs)

