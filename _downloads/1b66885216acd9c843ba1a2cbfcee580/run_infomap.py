import argparse
from infomap import Infomap

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script for running leiden.')

    parser.add_argument(
        '-i', metavar='ip_net', type=str, required=True,
        help='input network edge-list path'
        )
    parser.add_argument(
        '-o', metavar='output', type=str, required=True,
        help='output membership path'
        )
    
    args = parser.parse_args()
    
    im = Infomap() # add options such as the level or the directed ness
    
    with open(args.i) as f:
        for line in f:
            u, v = line.split()

            im.add_link(int(u), int(v))

    im.run()
    cluster_dict = {}
    for node in im.tree:
        if node.is_leaf:
            if(node.module_id not in cluster_dict):
                cluster_dict[node.module_id] = []
            cluster_dict[node.module_id].append(node.node_id)

    with open(args.o, "w") as f:
        for key in cluster_dict:
            for val in cluster_dict[key]:
                f.write(f'{val}\t{key}\n')