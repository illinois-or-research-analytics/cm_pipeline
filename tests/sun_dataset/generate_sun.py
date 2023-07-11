def write_array_to_file(file_path, array):
    with open(file_path, 'w') as file:
        for item in array:
            file.write(item + '\n')

clique_edgelist = [f'{u} {v}' for u in range(8) for v in range(8) if u != v]
clique_edgelist = clique_edgelist + [f'{u+8} {u}' for u in range(8)]
write_array_to_file('network.tsv', clique_edgelist)

cluster = [f'{i} 0' for i in range(16)]
write_array_to_file('clustering.tsv', cluster)