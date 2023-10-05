from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterator, List, Protocol, Tuple, Union, Dict

from hm01.graph import IntangibleSubgraph, Graph


class AbstractClusterer(Protocol):
    @abstractmethod
    def cluster(
        self, graph: Graph
    ) -> Iterator[IntangibleSubgraph]:
        raise NotImplementedError

    def cluster_without_singletons(
        self, graph: IntangibleSubgraph
    ) -> Iterator[IntangibleSubgraph]:
        for cluster in self.cluster(graph):
            if cluster.n() > 1:
                yield cluster

    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        clusters: Dict[str, IntangibleSubgraph] = {}
        with open(filepath) as f:
            for line in f:
                node_id, cluster_id = line.split()
                clusters.setdefault(
                    cluster_id, IntangibleSubgraph([], cluster_id)
                ).subset.append(int(node_id))
        return list(v for v in clusters.values() if v.n() > 1)

    # @abstractmethod
    # def postprocess_check(self, g : IntangibleSubgraph) -> Union[bool, Tuple[bool, str]]:
    #     raise NotImplementedError
