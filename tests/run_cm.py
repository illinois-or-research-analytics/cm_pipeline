import os
import json

from sys import argv
from datetime import datetime

def navigate_out():
    # Get the current directory
    current_directory = os.getcwd()

    # Move one level up
    parent_directory = os.path.dirname(current_directory)

    # Change the current directory to the parent directory
    os.chdir(parent_directory)

def get_max_timestamp(timestamps):
    ''' Get most recent timestamp out of a list of YYYYMMDD-HH:MM:SS strings '''
    return max(timestamps, key=lambda x: datetime.strptime(x, "%Y%m%d-%H:%M:%S"))

def get_run_name(json_file):
    ''' Get name of the CM pipeline run as noted in the json '''
    with open(json_file, "r") as file:
        json_data = json.load(file)
    
    return json_data["title"]

def get_latest_stage()

def get_recent_run(dirs, run_name):
    ''' Get most recent CM run from outputs directory '''
    timestamps = [d[len(run_name)+1:] for d in dirs if d.startswith(run_name)]
    max_timestamp = get_max_timestamp(timestamps)
    return f'{run_name}-{max_timestamp}'

def run_cm(data_dir: str):
    ''' Wrapper for running the cm pipeline and fetching outputs
    
    parameters
    ----------
    data_dir: directory holding the test-case dataset
    '''
    full_path = os.path.abspath(data_dir)

    navigate_out()

    os.system(f'python3 -m main {full_path}/pipeline.json')

    run_name = get_run_name(f'{full_path}/pipeline.json')
    dirs = os.listdir(f'{full_path}/samples/')

    # Navigate to the directory where the cm_pipeline final output is stored
    output_dir = get_recent_run(dirs, run_name)
    output_dirs = os.listdir(f'{full_path}/samples/{output_dir}/')
    data_output_dir = [d for d in output_dirs if d.startswith(('res', 'k'))][0]
    stage_outputs = os.listdir(f'{full_path}/samples/{output_dir}/{data_output_dir}/')
    print(stage_outputs)



def main():
    run_cm(argv[1])

if __name__ == '__main__':
    main()