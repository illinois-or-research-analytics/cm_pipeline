# pylint: disable=import-error

import sys
sys.path.append('../hm01')
sys.path.append('../hm01/tools/python-mincut/build')
sys.path.append('../hm01/tools/python-mincut/src')
from graph import Graph, RealizedSubgraph

print("Loading graph...")
G = Graph.from_edgelist('/shared/rsquared/vikrams_ikc_cluster_el.tsv')
print("Done")

print("Printing Graph details")
print(f"Number of edges: {G.m()}")
print(f"Number of nodes: {G.n()}")

print("Converting to realized subgraph...")
G = G.to_realized_subgraph()
print("Done")

print("Printing Realized Subgraph details")
print(f"Number of edges: {G.m()}")
print(f"Number of nodes: {G.n()}")

print("Computing Mincut...")
mc = G.find_mincut()
print("Done")
print(f"Mincut Size: {mc.get_cut_size()}")

print("Splitting Graph by Mincut")
light, heavy = G.cut_by_mincut(mc)
print("Done")

print(f"Graph L:\n\t{light.n()} nodes\n\t{light.m()} edges")
print(f"Graph H:\n\t{heavy.n()} nodes\n\t{heavy.m()} edges")