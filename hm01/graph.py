from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from functools import cache, cached_property
from sys import path
from typing import Dict, Iterator, List, Tuple, Union

import networkit as nk
import networkx as nx

import hm01.mincut as mincut
from hm01.clusterers.abstract_clusterer import AbstractClusterer
from hm01.context import context

# (VR) Importing the C++/Python wrapped modules requires appending paths via sys
from mincut_wrapper import MincutResult
from pymincut.pygraph import PyGraph


class AbstractGraph:
    """ (VR) Inheritable abstract class for the different graph classes """
    hydrator: List[int]  # (VR) Compress node ids into continuous ids
    index: str  # (VR) Graph identifier

    def intangible_subgraph(self, nodes: List[int],
                            suffix: str) -> IntangibleSubgraph:
        """ (VR) Convert to intangible subgraph """
        return IntangibleSubgraph(nodes, self.index + suffix)

    """ Basic properties for all the inherited graph types """

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

    def intangible_subgraph_from_compact(self, ids: List[int], suffix: str):
        """ Create an intangible subgraph from a list of ids that represent nodes in the compacted (i.e., made continuous) graph
        """
        return self.intangible_subgraph([self.hydrator[i] for i in ids],
                                        suffix)

    def find_clusters(
            self,
            clusterer: AbstractClusterer,
            with_singletons: bool = True) -> Iterator[IntangibleSubgraph]:
        """ (VR) Find clusters using the given clusterer """
        if with_singletons:
            return clusterer.cluster(self)
        else:
            return clusterer.cluster_without_singletons(self)


class Graph(AbstractGraph):
    """ Wrapped graph over a networkit graph with an ID label """

    def __init__(self, data, index):
        # (VR) Create nk graph and remove self loops
        self._data = data  # nk graph
        self._data.removeSelfLoops()
        self.index = index
        self.construct_hydrator()

    def to_realized_subgraph(self):
        return RealizedSubgraph(
            IntangibleSubgraph(list(range(self.n())), self.index), self)

    @staticmethod
    def from_nk(graph, index=""):
        """ (VR) Create a wrapped graph from a networkit graph """
        return Graph(graph, index)

    @staticmethod
    def from_edgelist(path):
        """ (VR) Read a graph from an edgelist file """
        edgelist_reader = nk.graphio.EdgeListReader("\t", 0, continuous=False)
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
    
    def cpm(self, g: IntangibleSubgraph, resolution: int) -> float:
        e_c = g.count_edges(self)
        n_c = len(g.subset)
        exp = n_c*(n_c - 1) / 2
        return e_c - resolution * exp

    def find_mincut(self):
        """ Find a mincut wrapped over Viecut """
        return mincut.viecut(self)

    def neighbors(self, u):
        yield from self._data.iterNeighbors(u)

    def remove_node(self, u):
        self._data.removeNode(u)

    def cut_by_mincut(self, mincut_res):
        """ (VR) Cut the graph by the mincut result """
        light = self.induced_subgraph(mincut_res.get_light_partition(), "a")
        heavy = self.induced_subgraph(mincut_res.get_heavy_partition(), "b")
        return light, heavy

    @cached_property
    def continuous_ids(self):
        return nk.graphtools.getContinuousNodeIds(self._data)

    def construct_hydrator(self):
        """ Hydrator: a mapping from the compacted id to the original id """
        n = self.n()
        hydrator = [0] * n
        continuous_ids = self.continuous_ids  # .items()
        assert len(continuous_ids
                   ) == n, f"Expected {n} ids, got {len(continuous_ids)}"
        for old_id, new_id in continuous_ids.items():
            hydrator[new_id] = old_id
        self.hydrator = hydrator

    def induced_subgraph(self, ids: List[int], suffix: str):
        """ (VR) Construct subgraph from a list of nodes """
        assert suffix != "", "Suffix cannot be empty"
        data = nk.graphtools.subgraphFromNodes(self._data, ids)
        index = self.index + suffix
        return Graph(data, index)

    def induced_subgraph_from_compact(self, ids: List[int], suffix: str):
        """ (VR) Same as above but with 'hydrated' nodes """
        return self.induced_subgraph([self.hydrator[i] for i in ids], suffix)

    def as_compact_edgelist_filepath(self):
        """ Get a filepath to the graph as a compact/continuous edgelist file """
        p = context.request_graph_related_path(self, "edgelist")
        towrite = nk.graphtools.getCompactedGraph(self._data,
                                                  self.continuous_ids)
        nk.graphio.writeGraph(towrite, p, nk.Format.EdgeListTabZero)
        return p

    def degree(self, u):
        return self._data.degree(u)

    def as_metis_filepath(self):
        """ Get a filepath to the graph to a (continuous) METIS file """
        p = context.request_graph_related_path(self, "metis")
        nk.graphio.writeGraph(self._data, p, nk.Format.METIS)
        return p

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
        return (ls / big_l) - (ds / (2 * big_l))**2

    @staticmethod
    def from_space_edgelist(filepath: str, index=""):
        return Graph(
            nk.graphio.readGraph(filepath, nk.Format.EdgeListSpaceZero), index)

    @staticmethod
    def from_erdos_renyi(n, p, index=""):
        return Graph(nk.generators.ErdosRenyiGenerator(n, p).generate(), index)

    @staticmethod
    def from_edges(edges: List[Tuple[int, int]], index=""):
        """ Construct from a n*2 array edgelist """
        n = max(max(u, v) for u, v in edges) + 1
        g = nk.graph.Graph(n)
        for u, v in edges:
            g.addEdge(u, v)
        return Graph(g, index)

    """ (VR) For testing: These just get shapes and construct graph objects from them """

    @staticmethod
    def from_straight_line(n: int, index=""):
        """ A linked-list graph with n nodes """
        return Graph.from_edges([(i, i + 1) for i in range(n - 1)], index)

    @staticmethod
    def from_clique(n: int, index=""):
        return Graph.from_edges([(i, j) for i in range(n - 1)
                                 for j in range(i + 1, n)], index)

    def to_intangible(self):
        return IntangibleSubgraph(list(self.nodes()), self.index)

    def to_igraph(self):
        import igraph as ig

        cont_ids = nk.graphtools.getContinuousNodeIds(self._data)
        compact_graph = nk.graphtools.getCompactedGraph(self._data, cont_ids)
        edges = [(u, v) for u, v in compact_graph.iterEdges()]
        return ig.Graph(self.n(), edges)


class RealizedSubgraph(AbstractGraph):
    hydrator: List[int]  # (VR) mapping from compact id to original id
    inv: Dict[int, int]  # (VR) mapping from original id to compact id
    compacted: List[List[
        int]]  # (VR) compacted adjacency list that maps from index to nodes adjacent to index
    _dirty: bool  # (VR) has the graph been compacted ?
    _graph: Graph

    def __init__(self,
                 intangible: IntangibleSubgraph = None,
                 graph: Union[Graph, RealizedSubgraph] = None):
        # Return an empty object if constructor is empty
        if intangible is None:
            return
        """ (VR) Convert nodelist into adjacency list """
        self.index = intangible.index
        self.nodeset = intangible.nodeset

        # (VR) Construct adjacency list from the graph
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

        # (VR) Store the graph metrics
        self._n = len(self.nodeset)
        self._m = sum(len(self.adj[n]) for n in self.nodeset) // 2
        self._dirty = True
        # self.recompact()

    @staticmethod
    def from_adjlist(nodes, edges, cluster_id):
        subgraph = RealizedSubgraph()
        subgraph.nodeset = nodes.copy()
        subgraph.adj = edges
        subgraph.index = cluster_id
        subgraph._n = len(nodes)
        subgraph._m = sum(len(subgraph.adj[n]) for n in subgraph.nodeset) // 2
        subgraph._dirty = True
        return subgraph

    def recompact(self):
        """ (VR) When the graph is modified, reconstruct the compacted adjacency list """
        unallocated = 0
        hydrator: List[int] = []
        inv: Dict[int, int] = {}
        compacted: List[List[int]] = []

        for n in self.nodeset:
            if n not in inv:
                hydrator.append(
                    n
                )  # (VR) Allocate new compacted id and reflect the changes in the adj list
                inv[n] = unallocated
                compacted.append([])
                unallocated += 1
            for m in self.adj[n]:
                if m not in inv:
                    hydrator.append(m)
                    inv[m] = unallocated
                    compacted.append([])
                    unallocated += 1
                compacted[inv[n]].append(
                    inv[m]
                )  # (VR) Add m to be adjacent to n in the compacted adj list
        assert len(hydrator) == len(inv)
        self.hydrator = hydrator
        self.inv = inv
        self.compacted = compacted
        self._dirty = False  # (VR) Set dirty to be false since the graph was compacted

    def degree(self, u) -> int:
        return len(self.adj[u])

    def neighbors(self, u) -> Iterator[int]:
        yield from self.adj[u]

    def to_intangible(self, graph):
        return IntangibleSubgraph(list(self.nodeset), self.index)

    def remove_node(self, u: int):
        self._n -= 1  # (VR) Adjust node count and adj list
        self._m -= len(self.adj[u])
        for v in self.adj[u]:
            self.adj[v].remove(u)
        del self.adj[u]
        self.nodeset.remove(u)
        self._dirty = True  # (VR) The graph needs to be recompacted so set dirty to true

    def n(self):
        return self._n

    def m(self):
        return self._m

    def nodes(self):
        yield from self.nodeset

    @cache
    def mcd(self) -> int:
        """ Get the minimum degree in the graph """
        if self.n() == 0:
            return 0
        return min(self.degree(n) for n in self.nodes())

    def to_igraph(self):
        if self._dirty:
            self.recompact()
        import igraph as ig

        edges = []
        for u in self.nodes():
            for v in self.adj[u]:
                if u > v:
                    continue
                edges.append((self.inv[u], self.inv[v]))
        return ig.Graph(self.n(), edges)

    def as_metis_filepath(self):
        if self._dirty:  # (VR) METIS requires compact node ids
            self.recompact()
        p = context.request_graph_related_path(self, "metis")
        with open(p, "w+") as f:
            f.write(f"{self.n()} {self.m()}\n")
            for u in self.compacted:
                f.write(" ".join([str(v + 1) for v in u]) + "\n")
        return p

    def as_compact_edgelist_filepath(self):
        if self._dirty:
            self.recompact()
        p = context.request_graph_related_path(self, "edgelist")
        with open(p, "w+") as f:
            for u, adj in enumerate(self.compacted):
                for v in adj:
                    if u < v:
                        f.write(f"{u}\t{v}\n")
        return p

    def find_mincut(self) -> MincutResult:
        """ (VR) Compute mincut via the wrapped VieCut """
        return mincut.viecut(self)

    def cut_by_mincut(
        self, mincut_res: MincutResult
    ) -> Tuple[Union[Graph, RealizedSubgraph], Union[Graph, RealizedSubgraph]]:
        """Cut the graph by the mincut result"""
        light = RealizedSubgraph(
            IntangibleSubgraph(
                mincut_res.get_light_partition(),
                self.index + "a",
            ),
            self,
        )
        heavy = RealizedSubgraph(
            IntangibleSubgraph(
                mincut_res.get_heavy_partition(),
                self.index + "b",
            ),
            self,
        )
        return light, heavy
    
    def internal_degree(self, u, graph: Graph) -> int:
        return sum(1 for v in graph._data.iterNeighbors(u) if v in self.nodeset)

    def get_border_edges(self, graph: Graph):
        ret = 0
        for v in self.nodeset:
            neighbors = sum(1 for u in graph.neighbors(v) if u not in self.nodeset)
            ret += neighbors
        return ret

    def conductance(self, graph):
        num = self.get_border_edges(graph)
        deg_sum = sum(graph.degree(v) for v in self.nodeset)
        den = min(deg_sum, 2*graph.m() - deg_sum)
        return num/den

    @property
    def continuous_ids(self):
        if self._dirty:
            self.recompact()
        return self.inv

    def as_pygraph(self):
        edges = []
        nodes = list(self.nodeset)
        for u in nodes:
            for v in self.adj[u]:
                edges.append((u, v))
        return PyGraph(nodes, edges)
    
    def as_compact_networkit(self):
        # Recompact nodes if they are not currently
        if self._dirty:
            self.recompact()

        # Initialize an empty graph
        graph = nk.Graph(n=self.n())
        
        # Add edges in the graph
        for u, adj in enumerate(self.compacted):
            for v in adj:
                if u < v:
                    graph.addEdge(u, v)

        # Preprocess the graph (e.g., compute properties, sort edges, etc.)
        graph.indexEdges()

        return graph


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
            pairs: Iterator[Tuple[int, str]]) -> List[IntangibleSubgraph]:
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
        return sum(1 for v in graph._data.iterNeighbors(u)
                   if v in self.nodeset)

    def count_mcd(self, graph: Graph) -> int:
        if self.n() == 0:
            return 0
        return min(self.internal_degree(u, graph) for u in self.subset)

    def is_tree_like(self, global_graph: Graph) -> bool:
        m = self.count_edges(global_graph)
        n = self.n()
        return m == n - 1
