# modification of syt3's run_leiden.py that
# sets n_iterations to 5 and seed to 1234
# 2/19/2023

import leidenalg
import igraph
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script for running leiden.')
    # Todo: Can we make the input arguments similar to runleiden to maintain
    #  consistency. For e.g. "-i" is input file in runleiden and here it is
    #  "number of iterations" and "-n" is the input file
    parser.add_argument(
        '-i', metavar='ip_net', type=str, required=True,
        help='input network edge-list path'
        )
    parser.add_argument(
        '-r', metavar='resolution', type=float, required=True,
        help='resolution parameter (gamma)'
        )
    parser.add_argument(
        '-o', metavar='output', type=str, required=True,
        help='output membership path'
        )
    parser.add_argument(
        '-n', metavar='n_iterations', type=int, required=True,
        help='number of iterations'
        )
    args = parser.parse_args()

    net = igraph.Graph.Read_Ncol(args.i, directed=False)
    partition = leidenalg.find_partition(
        net, leidenalg.CPMVertexPartition, resolution_parameter=args.r,
        seed=1234, n_iterations=args.n
        )
    with open(args.o, "w") as f:
        for n, m in enumerate(partition.membership):
            f.write(f"{net.vs[n]['name']}\t{m}\n")
