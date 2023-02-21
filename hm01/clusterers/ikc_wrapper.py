from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import List, Iterator, Dict, Optional, Tuple, Union
from collections import defaultdict
import csv

import networkit as nk

from clusterers.abstract_clusterer import AbstractClusterer

from graph import Graph, IntangibleSubgraph, RealizedSubgraph
from context import context


@dataclass
class IkcClusterer(AbstractClusterer):
    k: int

    def cluster(self, graph: Union[Graph, RealizedSubgraph]) -> Iterator[IntangibleSubgraph]:
        """Returns a list of (labeled) subgraphs on the graph"""
        cluster_id = graph.index  # the cluster id such as 5a6b2

        old_to_new_node_id_mapping = graph.continuous_ids
        new_to_old_node_id_mapping = {
            v: k for k, v in old_to_new_node_id_mapping.items()
        }
        raw_ikc_clustering_output_filename = context.request_graph_related_path(
            graph, "ikc.raw"
        )
        self.run_ikc(
            graph.as_compact_edgelist_filepath(),
            graph,
            raw_ikc_clustering_output_filename,
        )

        ikc_clustering_output_filename = context.request_graph_related_path(
            graph, "ikc"
        )
        self.parse_ikc_output(
            raw_ikc_clustering_output_filename, ikc_clustering_output_filename
        )
        clustering_mappings = self.ikc_output_to_dict(ikc_clustering_output_filename)
        cluster_to_id_dict = clustering_mappings["cluster_to_id_dict"]
        id_to_cluster_dict = clustering_mappings["id_to_cluster_dict"]

        for local_cluster_id, local_cluster_member_arr in cluster_to_id_dict.items():
            global_cluster_id = f"{cluster_id}{local_cluster_id}"
            global_cluster_member_arr = [
                int(new_to_old_node_id_mapping[local_id])
                for local_id in local_cluster_member_arr
            ]
            yield graph.intangible_subgraph(
                global_cluster_member_arr, str(local_cluster_id)
            )
        # return retarr

    def run_ikc(self, edge_list_path, graph: Union[Graph, RealizedSubgraph], output_file):
        """Runs IKC given an edge list and writes a CSV"""
        ikc_path = context.ikc_path
        stderr_p = context.request_graph_related_path(graph, f"_ikc_k={self.k}.stderr")
        stdout_p = context.request_graph_related_path(graph, f"_ikc_k={self.k}.stdout")
        with open(stderr_p, "w") as f_err:
            with open(stdout_p, "w") as f_out:
                subprocess.run(
                    [
                        "/usr/bin/time",
                        "-v",
                        "/usr/bin/env",
                        "python3",
                        ikc_path,
                        "-e",
                        edge_list_path,
                        "-o",
                        output_file,
                        "-k",
                        str(self.k),
                    ]
                )

    def parse_ikc_output(self, raw_clustering_output, clustering_output):
        with open(raw_clustering_output, "r") as f_raw:
            with open(clustering_output, "w") as f:
                for line in f_raw:
                    [node_id, cluster_number, k, modularity] = line.strip().split(",")
                    f.write(f"{cluster_number} {node_id}\n")

    def ikc_output_to_dict(self, clustering_output):
        cluster_to_id_dict = {}
        id_to_cluster_dict = {}
        with open(clustering_output, "r") as f:
            for line in f:
                [current_cluster_number, node_id] = line.strip().split()
                if int(current_cluster_number) not in cluster_to_id_dict:
                    cluster_to_id_dict[int(current_cluster_number)] = []
                if node_id not in id_to_cluster_dict:
                    id_to_cluster_dict[int(node_id)] = []
                cluster_to_id_dict[int(current_cluster_number)].append(int(node_id))
                id_to_cluster_dict[int(node_id)].append(int(current_cluster_number))

        return {
            "cluster_to_id_dict": cluster_to_id_dict,
            "id_to_cluster_dict": id_to_cluster_dict,
        }

    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        clusters = {}
        with open(filepath, newline="") as csvfile:
            #if 
            reader = csv.reader(csvfile, delimiter=",")
            for row in reader:
                node_id = int(row[0])
                cluster_id = row[1]
                if cluster_id not in clusters:
                    clusters[cluster_id] = IntangibleSubgraph([], cluster_id)
                clusters[cluster_id].subset.append(node_id)
        return list(clusters.values())

    # TODO: Need to factor in if .tsv
    def from_existing_clustering(self, filepath) -> List[IntangibleSubgraph]:
        # node_id cluster_id format
        clusters: Dict[str, IntangibleSubgraph] = {}
        with open(filepath) as f:
            for line in f:
                node_id, cluster_id = line.split()
                clusters.setdefault(
                    cluster_id, IntangibleSubgraph([], cluster_id)
                ).subset.append(int(node_id))
        return list(v for v in clusters.values() if v.n() > 1)