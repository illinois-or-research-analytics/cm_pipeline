def make_clique(arr):
    ret_edges = []
    for u in arr:
        for v in arr:
            if u < v:
                ret_edges.append((u, v))

    return ret_edges

num_clusters = 8
num_cliques = 4096
num_nodes = num_cliques * 4
cluster_size = num_nodes // num_clusters

nodelist = list(range(num_nodes))

edgelist = []

for u in range(0, num_nodes, 4):
    edgelist.extend(make_clique(nodelist[u:u+4]))
    edgelist.append((u+3, (u+4)%num_nodes))

with open('network.tsv', 'w+') as f:
    for u, v in edgelist:
        f.write(f'{u}\t{v}\n')

with open('clustering.tsv', 'w+') as f:
    for u in nodelist:
        f.write(f'{u}\t{u // cluster_size}\n')
