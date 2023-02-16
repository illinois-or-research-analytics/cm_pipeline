from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterator, List, Protocol, Tuple, Union


class AbstractClusterer(Protocol):
    @abstractmethod
    def cluster(
        self, graph: hm01.graph.Graph
    ) -> Iterator[hm01.graph.IntangibleSubgraph]:
        raise NotImplementedError

    def cluster_without_singletons(
        self, graph: hm01.graph.IntangibleSubgraph
    ) -> Iterator[hm01.graph.IntangibleSubgraph]:
        for cluster in self.cluster(graph):
            if cluster.n() > 1:
                yield cluster

    @abstractmethod
    def from_existing_clustering(self, filepath) -> List[hm01.graph.IntangibleSubgraph]:
        raise NotImplementedError

    # @abstractmethod
    # def postprocess_check(self, g : IntangibleSubgraph) -> Union[bool, Tuple[bool, str]]:
    #     raise NotImplementedError
