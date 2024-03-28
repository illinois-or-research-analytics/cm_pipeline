from dataclasses import dataclass
from typing import List, Iterator, Dict, Union

from hm01.clusterers.abstract_clusterer import AbstractClusterer

from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph


@dataclass
class NopClusterer(AbstractClusterer):

    def cluster(self, graph: Union[Graph, RealizedSubgraph]) -> Iterator[IntangibleSubgraph]:
        """Returns a list of (labeled) subgraphs on the graph"""
        yield IntangibleSubgraph([], "")

    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        clusters: Dict[str, IntangibleSubgraph] = {}
        with open(filepath) as f:
            for line in f:
                node_id, cluster_id = line.split()
                clusters.setdefault(
                    cluster_id, IntangibleSubgraph([], cluster_id)
                ).subset.append(int(node_id))
        return list(v for v in clusters.values() if v.n() > 1)


def get_clusterer(**kwargs):
    return NopClusterer(**kwargs)

