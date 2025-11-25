# modification of syt3's run_leiden.py that
# sets n_iterations to 5 and seed to 1234
# 2/19/2023

import leidenalg
import igraph
import argparse
import csv
import pandas as pd

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
    parser.add_argument(
        '-s', type=str, default = '\t',
        help='output separator'
        )
    args = parser.parse_args()

    with open(args.i, "r") as f:
        sample = f.read(1024)
        delim, header = csv.Sniffer().sniff(sample).delimiter, csv.Sniffer().has_header(sample)

    edgelist = pd.read_csv( args.i, sep = delim, skiprows = int(header) )
    vertices = pd.DataFrame(pd.unique(edgelist.values.ravel()))
    net = igraph.Graph.DataFrame(edgelist, directed = False, use_vids = False, vertices = vertices)
    partition = leidenalg.find_partition(
        net, leidenalg.CPMVertexPartition, resolution_parameter=args.r,
        seed=1234, n_iterations=args.n
    )
    with open(args.o, "w") as f:
        for n, m in enumerate(partition.membership):
            f.write(f"{vertices.iloc[n].iloc[0]}{args.s}{m}\n")
