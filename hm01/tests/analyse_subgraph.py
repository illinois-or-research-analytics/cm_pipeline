f = open('graph_details.txt')
lines = f.readlines()

nodes = set()

for line in lines:
    u, v = line[1:-2].split(', ')
    u, v = int(u), int(v)
    nodes.add(u)
    nodes.add(v)

nodes = list(nodes)
nodes.sort()
print(nodes[:10])