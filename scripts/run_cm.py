import click
import os
import glob
from pathlib import Path
import re

@click.command()
@click.option("--input", type=click.Path(exists=True), help="The input network")
@click.option("--working-directory", type=click.Path(exists=True), help="Working directory")
@click.option("--existing-clustering", required=False, default="", type=click.Path(), help="The existing clustering of the input network to be reclustered")
@click.option("--quiet", is_flag=True, help="Silence output messages")
@click.option("--no-prune", is_flag=True, help="Skip the pruning step")
@click.option("--clusterer", required=True, type=click.Choice(["leiden", "ikc", "leiden_mod", "nop", "external"]), help="Clustering algorithm used to obtain the existing clustering")

@click.option("--clusterer_file", required=False, type=str, default="", help="If using an external clusterer, specify the file path to the clusterer object")
@click.option("--clusterer_args", required=False, type=str, default="", help="If using an external clusterer, specify the arguments here")
@click.option("--k", required=False, type=int, default=-1, help="(IKC Only) k parameter")
@click.option("--resolution", required=False, type=float, default=-1, help="(Leiden Only) Resolution parameter")
@click.option("--threshold", required=True, type=str, help="Connectivity threshold wich all clusters should be above")
@click.option("--output", required=True, type=click.Path(), help="Output filename")
@click.option("--nprocs", required=False, type=int, default=1, help="Number of cores to run in parallel")
def run_cm(input, working_directory, existing_clustering, quiet, no_prune, clusterer, clusterer_file, clusterer_args, k, resolution, threshold, output, nprocs):
    original_input_network = input
    converted_input_network = f"{working_directory}/network.tsv"
    original_existing_clustering = existing_clustering
    converted_existing_clustering = f"{working_directory}/existing_clustering.tsv"
    original_csv_output = output
    tsv_output = f"{working_directory}/output.tsv"

    with open(original_input_network, "r") as fr:
        with open(converted_input_network, "w") as fw:
            for line_number,line in enumerate(fr):
                if line_number == 0:
                    continue
                fw.write(line.replace(",", "\t"))
    if original_existing_clustering != "":
        with open(original_existing_clustering, "r") as fr:
            with open(converted_existing_clustering, "w") as fw:
                for line_number,line in enumerate(fr):
                    if line_number == 0:
                        continue
                    fw.write(line.replace(",", "\t"))

    cm_required_arguments = f"--input {converted_input_network} --clusterer {clusterer} --threshold {threshold} --output {tsv_output} --nprocs {nprocs}"
    cm_optional_arguments = f""
    if existing_clustering != "":
        cm_optional_arguments += f" --existing-clustering {converted_existing_clustering}"
    if quiet:
        cm_optional_arguments += f" --quiet"
    if no_prune:
        cm_optional_arguments += f" --no-prune"
    if clusterer_file != "":
        cm_optional_arguments += f" --clusterer_file {clusterer_file}"
    if clusterer_args != "":
        cm_optional_arguments += f" --clusterer_args {clusterer_args}"
    if k != -1:
        cm_optional_arguments += f" --k {k}"
    if resolution != -1:
        cm_optional_arguments += f" --resolution {resolution}"
    print(f"python -m hm01.cm {cm_required_arguments} {cm_optional_arguments}")

    with open(tsv_output, "r") as fr:
        with open(original_csv_output, "w") as fw:
            fw.write("node_id,cluster_id\n")
            for line in fr:
                fw.write(line.replace("\t", ","))

if __name__ == "__main__":
    run_cm()
