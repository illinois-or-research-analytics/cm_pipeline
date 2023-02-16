from dataclasses import dataclass
from typing import Dict, Iterator, List, Union
from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph
from hm01.clusterers.abstract_clusterer import AbstractClusterer
from enum import Enum
import leidenalg as la


class Quality(str, Enum):
    cpm = "cpm"
    modularity = "mod"


@dataclass
class LeidenClusterer(AbstractClusterer):
    resolution: float
    quality: Quality = Quality.cpm

    def cluster(self, graph: Union[Graph, RealizedSubgraph]) -> Iterator[IntangibleSubgraph]:
        g = graph.to_igraph()
        if self.quality == Quality.cpm:
            partition = la.find_partition(
                g, la.CPMVertexPartition, resolution_parameter=self.resolution
            )
        else:
            partition = la.find_partition(g, la.ModularityVertexPartition)
        for i in range(len(partition)):
            nodes = partition[i]
            yield graph.intangible_subgraph_from_compact(nodes, f"{i+1}")

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
