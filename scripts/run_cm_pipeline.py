import click
import os
import glob
from pathlib import Path
import re


@click.command()
@click.option("--pipeline-file", required=True, type=click.Path(exists=True), help="Pipeline.json file")
@click.option("--working-directory", required=True, type=click.Path(exists=True), help="Working directory for intermeidate files")
def run_cm_pipeline(pipeline_file, working_directory):
    original_input_file = ""
    original_output_directory = ""
    converted_input_file_name_only = "network.tsv"
    converted_input_file =f"{working_directory}/{converted_input_file_name_only}"
    with open(pipeline_file, "r") as fr:
        with open(f"{working_directory}/pipeline.json", "w") as fw:
            for line in fr:
                if "\"input_file\":" in line:
                    original_input_file = line.split("\"input_file\":")[1].strip()[1:-2] # technically not robust because of quotes and commas
                    fw.write(f"\"input_file\": \"{converted_input_file_name_only}\",\n")
                else:
                    if "\"output_dir\":" in line:
                        original_output_directory = line.split("\"output_dir\":")[1].strip()[1:-2]
                    fw.write(line)

    with open(original_input_file, "r") as fr:
        with open(converted_input_file, "w") as fw:
            for line_no,line in enumerate(fr):
                if line_no == 0:
                    continue
                fw.write(line.replace(",", "\t"))

    os.system(f"python -m main {working_directory}/pipeline.json")

    original_output_directory = "./output"
    sub_run_directories = glob.glob(f"{working_directory}/output/*/*")
    for sub_run_directory in sub_run_directories:
        current_path = Path(sub_run_directory)
        if current_path.is_dir() and current_path.name != "analysis":
            # print(current_path.name)
            os.system(f"mkdir {original_output_directory}/{current_path.name}")
            tsv_files = glob.glob(f"{working_directory}/output/*/{current_path.name}/*.tsv")
            max_stage_file = ""
            max_stage_num = -1
            for tsv_file in tsv_files:
                tsv_file_name = Path(tsv_file).name
                stage_num = int(tsv_file_name.split("_")[0][1:])
                if stage_num > max_stage_num:
                    max_stage_num = stage_num
                    max_stage_file = tsv_file
            max_stage_file_name = Path(max_stage_file).name
            max_stage_file_csv = re.sub(".tsv$", ".csv", f"{original_output_directory}/{current_path.name}/{max_stage_file_name}")
            with open(max_stage_file, "r") as fr:
                with open(max_stage_file_csv, "w") as fw:
                    fw.write("node_id,cluster_id\n")
                    for line in fr:
                        fw.write(line.replace("\t", ","))

if __name__ == "__main__":
    run_cm_pipeline()
