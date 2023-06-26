import typer

import networkit as nk
import pandas as pd

from graph import Graph, IntangibleSubgraph
from typing import Dict, List
from os import path

def from_existing_clustering(filepath) -> List[IntangibleSubgraph]:
    ''' I just modified the original method to return a dict mappign from index to clustering '''
    # node_id cluster_id format
    clusters: Dict[str, IntangibleSubgraph] = {}
    with open(filepath) as f:
        for line in f:
            node_id, cluster_id = line.split()
            clusters.setdefault(
                cluster_id, IntangibleSubgraph([], cluster_id)
            ).subset.append(int(node_id))
    return {key: val for key, val in clusters.items() if val.n() > 1}

def main(
    input: str = typer.Option(..., "--input", "-i", help="The input network."),
    existing_clustering: str = typer.Option(..., "--existing-clustering", "-e", help="The existing clustering of the input network to be reclustered."),
):
    # Split ext
    base, ext = path.splitext(existing_clustering)

    # Load full graph into Graph object
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(input)
    global_graph = Graph(nk_graph, "")

    # Load clusters
    clusters = from_existing_clustering(existing_clustering)

    # Get list of forbidden clusters
    modularities = {key: global_graph.modularity_of(val) for key, val in clusters.items()}
    modularities_l0 = [key for key, val in modularities.items() if val <= 0]
    print('Cluster IDs with non-positive modularities:', modularities_l0)

    # If there are no forbidden clusters, dont do anything
    if len(modularities_l0) == 0:
        print('No need to filter... Done')
        return

    # Filter out the forbidden clusters otherwise
    df = pd.read_csv(existing_clustering, sep=" ", names=['node_id', 'cluster_id']).astype(str)
    df = df[~df['cluster_id'].isin(modularities_l0)]

    # Save it to a new tsv
    df.to_csv(f'{base}_modfiltered.tsv', sep='\t', header=False, index=False)

def entry_point():
    typer.run(main)

if __name__ == "__main__":
    entry_point()