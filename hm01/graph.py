from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
import networkit as nk
from typing import Dict, Iterator, List, Tuple, Union

from clusterers.abstract_clusterer import AbstractClusterer
import mincut
from context import context
from structlog import get_logger
from functools import cache, cached_property

from sys import path
path.append('tools/python-mincut/build')
path.append('tools/python-mincut/src')
from mincut_wrapper import MincutResult
from pygraph import PyGraph

log = get_logger()

# TODO: AbstractGraph type should incorporate all duplicate code of all the Graph classes
# Also, AbstractGraph should replace most of the Union[RealizedSubgraph, Graph] types
class AbstractGraph:
    index : str

    def intangible_subgraph(self, nodes: List[int], suffix: str) -> IntangibleSubgraph:
        return IntangibleSubgraph(nodes, self.index + suffix)

    @abstractmethod
    def n(self) -> int:
        pass

    @abstractmethod
    def m(self) -> int:
        pass

    @abstractmethod
    def nodes(self) -> Iterator[int]:
        pass

    @abstractmethod
    def degree(self, u) -> int:
        pass

    @abstractmethod
    def neighbors(self, u) -> Iterator[int]:
        pass

    def degree_sequence(self) -> List[int]:
        return sorted([self.degree(u) for u in self.nodes()])

    def find_clusters(
        self, clusterer: AbstractClusterer, with_singletons: bool = True
    ) -> Iterator[IntangibleSubgraph]:
        """ (VR) Find clusters using the given clusterer"""
        log.info(
            f"Finding clusters using clusterer",
            id=self.index,
            n=self.n(),
            m=self.m(),
            clusterer=clusterer,
        )
        if with_singletons:
            return clusterer.cluster(self)
        else:
            return clusterer.cluster_without_singletons(self)

class Graph(AbstractGraph):
    """ Wrapped graph over a networkit graph with an ID label """

    def __init__(self, data, index):
        self._data = data  # nk graph
        self._data.removeSelfLoops()
        self.index = index

    def to_realized_subgraph(self):
        return RealizedSubgraph(IntangibleSubgraph(list(range(self.n())), self.index), self)

    @staticmethod
    def from_nk(graph, index=""):
        """ (VR) Create a wrapped graph from a networkit graph """
        return Graph(graph, index)

    @staticmethod
    def from_edgelist(path):
        """ (VR) Read a graph from an edgelist file """
        edgelist_reader = nk.graphio.EdgeListReader("\t", 0, continuous = False)
        nk_graph = edgelist_reader.read(path)
        return Graph.from_nk(nk_graph)

    @staticmethod
    def from_metis(path):
        """ (VR) Read from .metis format """
        metis_reader = nk.graphio.METISGraphReader()
        return Graph.from_nk(metis_reader.read(path))
        
    def n(self) -> int:
        """ Number of nodes """
        return self._data.numberOfNodes()

    def m(self) -> int:
        """ Number of edges """
        return self._data.numberOfEdges()

    @cache
    def mcd(self) -> int:
        """ Get the minimum degree value """
        if self.n() == 0:
            return 0
        return min(self._data.degree(n) for n in self._data.iterNodes())

    def find_mincut(self) -> MincutResult:
        """ Find a mincut wrapped over Viecut """
        return mincut.viecut(self)

    def neighbors(self, u):
        yield from self._data.iterNeighbors(u)

    def remove_node(self, u):
        self._data.removeNode(u)

    def cut_by_mincut(
        self, mincut_res: MincutResult
    ) -> Tuple[Union[Graph, RealizedSubgraph], Union[Graph, RealizedSubgraph]]:
        """ (VR) Cut the graph by the mincut result """
        light = self.induced_subgraph(mincut_res.get_light_partition(), "a")
        heavy = self.induced_subgraph(mincut_res.get_heavy_partition(), "b")
        return light, heavy

    @cached_property
    def continuous_ids(self):
        return nk.graphtools.getContinuousNodeIds(self._data)

    def induced_subgraph(self, ids: List[int], suffix: str):
        assert suffix != "", "Suffix cannot be empty"
        data = nk.graphtools.subgraphFromNodes(self._data, ids)
        index = self.index + suffix
        return Graph(data, index)

    def degree(self, u):
        return self._data.degree(u)

    def nodes(self):
        """ Iterate over the nodes """
        return self._data.iterNodes()

    def modularity_of(self, g: IntangibleSubgraph) -> float:
        """ (VR) Calculate the modularity of the subset `g` with respect to `self`
        
        Modularity is higher when clusters are densely connected within clusters but sparsely 
        connected between clusters
        """
        ls = g.count_edges(self)
        big_l = self.m()
        ds = sum(self._data.degree(n) for n in g.subset)
        return (ls / big_l) - (ds / (2 * big_l)) ** 2

    @staticmethod
    def from_space_edgelist(filepath: str, index=""):
        return Graph(nk.graphio.readGraph(filepath, nk.Format.EdgeListSpaceZero), index)

    @staticmethod
    def from_erdos_renyi(n, p, index=""):
        return Graph(nk.generators.ErdosRenyiGenerator(n, p).generate(), index)

    @staticmethod
    def from_edges(edges: List[Tuple[int, int]], index=""):
        n = max(max(u, v) for u, v in edges) + 1
        g = nk.graph.Graph(n)
        for u, v in edges:
            g.addEdge(u, v)
        return Graph(g, index)

    @staticmethod
    def from_straight_line(n: int, index=""):
        """ A linked-list graph with n nodes """
        return Graph.from_edges([(i, i + 1) for i in range(n - 1)], index)

    @staticmethod
    def from_clique(n: int, index=""):
        return Graph.from_edges(
            [(i, j) for i in range(n - 1) for j in range(i + 1, n)], index
        )

    def to_intangible(self, graph):
        return IntangibleSubgraph(list(self.nodes()), self.index)

class RealizedSubgraph(AbstractGraph):
    _graph: Graph

    def __init__(self, intangible: IntangibleSubgraph, graph: Graph):
        """ (VR) Convert nodelist into adjacency list """
        self.index = intangible.index
        self.nodeset = intangible.nodeset
        self.adj: Dict[int, set[int]] = {}
        self._graph = graph
        for n in self.nodeset:
            if n not in self.adj:
                self.adj[n] = set()
            for m in graph.neighbors(n):
                if m not in self.nodeset:
                    continue
                if m not in self.adj:
                    self.adj[m] = set()
                self.adj[n].add(m)
        self._n = len(self.nodeset)
        self._m = sum(len(self.adj[n]) for n in self.nodeset) // 2

    def degree(self, u) -> int:
        return len(self.adj[u])

    def neighbors(self, u) -> Iterator[int]:
        yield from self.adj[u]

    def to_intangible(self, graph):
        return IntangibleSubgraph(list(self.nodeset), self.index)

    def remove_node(self, u: int):
        self._n -= 1
        self._m -= len(self.adj[u])
        for v in self.adj[u]:
            self.adj[v].remove(u)
        del self.adj[u]
        self.nodeset.remove(u)

    def n(self):
        return self._n

    def m(self):
        return self._m

    def nodes(self):
        yield from self.nodeset

    @cache
    def mcd(self) -> int:
        if self.n() == 0:
            return 0
        return min(self.degree(n) for n in self.nodes())

    def find_mincut(self) -> MincutResult:
        return mincut.viecut(self)

    def cut_by_mincut(
        self, mincut_res: MincutResult
    ) -> Tuple[Union[Graph, RealizedSubgraph], Union[Graph, RealizedSubgraph]]:
        """Cut the graph by the mincut result"""
        light = RealizedSubgraph(IntangibleSubgraph(mincut_res.get_light_partition(), self.index + "a"), self._graph)
        heavy = RealizedSubgraph(IntangibleSubgraph(mincut_res.get_heavy_partition(), self.index + "b"), self._graph)
        return light, heavy
    
    def as_pygraph(self) -> CGraph:
        edges = []
        nodes = list(self.nodeset)
        for u in nodes:
            for v in self.adj[u]:
                edges.append((u, v))
        return PyGraph(nodes, edges)

@dataclass
class IntangibleSubgraph:
    """ A yet to be realized subgraph, containing only the node ids """
    subset: List[int]
    index: str

    def realize(self, graph: Graph) -> RealizedSubgraph:
        """ Realize the subgraph """
        return RealizedSubgraph(self, graph)

    def __len__(self):
        return len(self.subset)

    def n(self):
        return len(self)

    @staticmethod
    def from_assignment_pairs(
        pairs: Iterator[Tuple[int, str]]
    ) -> List[IntangibleSubgraph]:
        clusters: Dict[str, IntangibleSubgraph] = {}
        for node, cluster in pairs:
            if cluster not in clusters:
                clusters[cluster] = IntangibleSubgraph([], cluster)
            clusters[cluster].subset.append(node)
        res = list(v for v in clusters.values() if v.n() > 0)
        if not res:
            raise ValueError("No non-singleton clusters found. Aborting.")
        return res

    @cached_property
    def nodeset(self):
        return set(self.subset)

    def edges(self, graph: Graph) -> Iterator[Tuple[int, int]]:
        for n in self.subset:
            for e in graph._data.iterNeighbors(n):
                if e in self.nodeset:
                    yield n, e

    def nodes(self) -> Iterator[int]:
        return iter(self.subset)

    def count_edges(self, global_graph: Graph):
        return sum(1 for _ in self.edges(global_graph)) // 2

    def internal_degree(self, u, graph: Graph) -> int:
        return sum(1 for v in graph._data.iterNeighbors(u) if v in self.nodeset)

    def count_mcd(self, graph: Graph) -> int:
        if self.n() == 0:
            return 0
        return min(self.internal_degree(u, graph) for u in self.subset)

    def is_tree_like(self, global_graph: Graph) -> bool:
        m = self.count_edges(global_graph)
        n = self.n()
        return m == n - 1
