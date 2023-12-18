import networkx as nx
import matplotlib.pyplot as plt

# Parameters for the Erdos-Renyi Graph
n = 150  # Number of nodes
p = 0.05  # Probability of edge creation

# Generate the graph
G = nx.erdos_renyi_graph(n, p)

# Save the graph as an edge list in TSV format
edge_list_file = 'graph2.tsv'
nx.write_edgelist(G, edge_list_file, delimiter='\t', data=False)

# Draw the graph
nx.draw(G, with_labels=True, node_color='lightblue', edge_color='gray')
plt.show()
