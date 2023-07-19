import os
import json
import csv
from pathlib import Path

from datetime import datetime
from collections import Counter


def navigate_out():
    # Change the current directory to the parent directory
    project_root = Path(__file__).parents[1]
    os.chdir(project_root)


def navigate_back():
    project_root = Path(__file__).parents[0]
    os.chdir(project_root)


def get_max_timestamp(timestamps):
    ''' Get most recent timestamp out of a list of YYYYMMDD-HH:MM:SS strings '''
    return max(timestamps,
               key=lambda x: datetime.strptime(x, "%Y%m%d-%H:%M:%S"))


def get_run_name(json_file):
    ''' Get name of the CM pipeline run as noted in the json '''
    with open(json_file, "r") as file:
        json_data = json.load(file)

    return json_data["title"]


def get_recent_run(dirs, run_name):
    ''' Get most recent CM run from outputs directory '''
    timestamps = [
        d[len(run_name) + 1:] for d in dirs if d.startswith(run_name)
    ]
    max_timestamp = get_max_timestamp(timestamps)
    return f'{run_name}-{max_timestamp}'


def count_nodes(file):
    line_count = 0
    with open(file, 'r') as file:
        for line in file:
            line_count += 1
    return line_count


def count_clusters(file):
    column_index = 1
    unique_values = set()

    with open(file, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            value = row[column_index]
            unique_values.add(value)

    count = len(unique_values)

    return count


def get_cluster_sizes(file):
    ''' The cluster sizes will be a sorted array '''
    column_index = 1  # Index of the column (0-based) to calculate frequencies

    frequencies = Counter()

    with open(file, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            value = row[column_index]
            frequencies[value] += 1

    frequency_array = list(frequencies.values())
    frequency_array.sort()
    return frequency_array


def get_final_tsv_leiden(files, res, iter):
    ''' Get the final clustering output for a leiden clustering '''
    tsvs = [f for f in files[f'res-{res}-i{iter}'] if f.endswith('.tsv')]
    return max(tsvs, key=lambda x: int(x.rsplit("/", 1)[-1][1]))


def get_final_tsv_ikc(files, k):
    ''' Get the final clustering for an ikc output '''
    tsvs = [f for f in files[f'k-{k}'] if f.endswith('.tsv')]
    return max(tsvs, key=lambda x: int(x.rsplit("/", 1)[-1][1]))


def run_cm(data_dir: str):
    ''' Wrapper for running the cm pipeline and fetching outputs
    
    parameters
    ----------
    data_dir: directory holding the test-case dataset

    returns
    -------
    A dictionary mapping algorithm parameters to stage outputs
    '''
    full_path = Path(__file__).parent / data_dir

    navigate_out()

    os.system(f'python3 -m main {full_path}/pipeline.json')

    run_name = get_run_name(f'{full_path}/pipeline.json')
    dirs = os.listdir(f'{full_path}/samples/')

    # Navigate to the directory where the cm_pipeline final output is stored
    output_dir = get_recent_run(dirs, run_name)
    output_dirs = os.listdir(f'{full_path}/samples/{output_dir}/')
    data_output_dir = [d for d in output_dirs if d.startswith(('res', 'k'))]
    stage_outputs = {
        d: [
            f"{full_path}/samples/{output_dir}/{d}/{f}"
            for f in os.listdir(f'{full_path}/samples/{output_dir}/{d}/')
        ]
        for d in data_output_dir
    }

    navigate_back()

    return stage_outputs