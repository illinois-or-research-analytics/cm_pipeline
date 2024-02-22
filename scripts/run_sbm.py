import argparse

import graph_tool.all as gt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script for running SBM.')

    parser.add_argument(
        '-i', metavar='ip_net', type=str, required=True,
        help='input network edge-list path'
        )
    parser.add_argument(
        '-o', metavar='output', type=str, required=True,
        help='output membership path'
        )

    args = parser.parse_args()

    sbm_graph = gt.Graph(directed=False)

    def edge_list_iterable():
        with open(args.i) as f:
            for line in f:
                u,v = line.strip().split()
                yield int(u),int(v)
    vpm_name = sbm_graph.add_edge_list(edge_list_iterable(), hashed=True, hash_type="int")

    sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state_args={"deg_corr": True})
    block_membership = sbm_clustering.get_blocks()


    cluster_dict = {}
    for new_node_id in sbm_graph.vertices():
        current_cluster_id = block_membership[new_node_id]
        if(current_cluster_id not in cluster_dict):
            cluster_dict[current_cluster_id] = []
        cluster_dict[current_cluster_id].append(vpm_name[new_node_id])

    with open(args.o, "w") as f:
        for key in cluster_dict:
            for val in cluster_dict[key]:
                f.write(f'{val}\t{key}\n')
