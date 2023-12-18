import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# Load the clustering data
clustering_file = 'clustering.tsv'
clustering_data = pd.read_csv(clustering_file, sep='\t', header=None, names=['node_id', 'cluster_id'])

# Load the edge list data
edge_list_file = 'network.tsv'
G = nx.read_edgelist(edge_list_file, delimiter='\t', nodetype=int)

# Assign cluster IDs to nodes in the graph
node_cluster_mapping = dict(clustering_data.values)
nx.set_node_attributes(G, node_cluster_mapping, 'cluster')

# Generate a color map for clusters
unique_clusters = set(node_cluster_mapping.values())
color_map = plt.cm.get_cmap('viridis', len(unique_clusters))
colors = {cluster: color_map(i) for i, cluster in enumerate(unique_clusters)}

# Assign color to each node based on cluster
node_colors = [colors[node_cluster_mapping[node]] for node in G.nodes()]

# Plot the graph
plt.figure(figsize=(12, 8))
nx.draw(G, node_color=node_colors, with_labels=False, node_size=50, edge_color='gray')
plt.savefig('patitions.png')
plt.show()