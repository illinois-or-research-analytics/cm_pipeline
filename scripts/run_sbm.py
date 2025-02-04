# modification of syt3's run_leiden.py that
# sets n_iterations to 5 and seed to 1234
# 2/19/2023

import graph_tool.all as gt
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script for running sbm.')
    parser.add_argument(
        '-i', metavar='ip_net', type=str, required=True,
        help='input network edge-list path'
        )
    parser.add_argument(
        '-b', metavar='block_state', type=str, required=True,
        help='non_nested_sbm or planted_partition_model'
        )
    parser.add_argument(
        '-d', metavar='degree_corrected', type=bool, required=True,
        help='whether to run degree corrected or not'
        )
    parser.add_argument(
        '-o', metavar='output', type=str, required=True,
        help='output membership path'
        )

    args = parser.parse_args()

    sbm_graph = gt.Graph(directed=False)
    def edge_list_iterable():
        with open(args.i, "r") as f:
            for line in f:
                u,v = line.strip().split()
                yield u,v
    vpm_name = sbm_graph.add_edge_list(edge_list_iterable(), hashed=True, hash_type="string")
    # vpm_name = sbm_graph.add_edge_list(edgelist_arr, hashed=True, hash_type="int")

    sbm_clustering = None
    if args.b == "non_nested_sbm":
        if args.d:
            sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state=gt.BlockState, state_args={"deg_corr": True})
        else:
            sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state=gt.BlockState, state_args={"deg_corr": False})
    elif args.b == "planted_partition_model":
        sbm_clustering = gt.minimize_blockmodel_dl(sbm_graph, state=gt.PPBlockState)

    block_membership = sbm_clustering.get_blocks()

    cluster_dict = {}
    with open(args.o, "w") as f:
        for new_node_id in sbm_graph.vertices():
            current_cluster_id = block_membership[new_node_id]
            f.write(f"{vpm_name[new_node_id]}\t{current_cluster_id}\n")
