from datetime import datetime
from os import path
import os

from source.stage import Stage

class Workflow:
    def __init__(self, data, pipeline):
        # Load working dirs
        self.working_dir = path.dirname(path.abspath(pipeline))
        self.current_script = path.dirname(path.dirname(path.abspath(__file__)))

        # Load global parameters
        self.title = data['title']
        self.algorithm = data['algorithm']
        self.network_name = data['name']
        self.output_dir = data['output_dir']
        self.input_file = data['input_file'] if data['input_file'][0] == '/' else f'{self.working_dir}/{data["input_file"]}'
        
        # Load and process existing clustering
        self.existing_clustering = {}
        try:
            if self.algorithm == 'leiden':
                for k, v in data['existing'].items():
                    res, i = k.split(", ")
                    if v[0] == '/':
                        self.existing_clustering[frozenset([float(res), int(i)])] = v
                    else:
                        self.existing_clustering[frozenset([float(res), int(i)])] = f'{self.working_dir}/{v}'
            elif self.algorithm == 'leiden_mod':
                for k, v in data['existing'].items():
                    i = int(k)
                    if v[0] == '/':
                        self.existing_clustering[frozenset(['mod', int(i)])] = v
                    else:
                        self.existing_clustering[frozenset(['mod', int(i)])] = f'{self.working_dir}/{v}'
            else:
                for k, v in data['existing'].items():
                    i = int(k)
                    if v[0] == '/':
                        self.existing_clustering[int(i)] = v
                    else:
                        self.existing_clustering[int(i)] = f'{self.working_dir}/{v}'
        except KeyError:
            self.existing_clustering = None

        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            self.iterations = data['iterations'] if type(data['iterations']) == list else [data['iterations']]
        else:
            self.iterations = None

        if self.algorithm == 'leiden':
            self.resolution = data['resolution'] if type(data['resolution']) == list else [data['resolution']]
        elif self.algorithm == 'leiden_mod':
            self.resolution = ['mod']
        else:
            self.resolution = data['k'] if type(data['k']) == list else [data['k']]

        # Get timestamp of algo run
        self.timestamp = datetime.now().strftime("%Y%m%d-%H:%M:%S")

        # Initialize first set of commands
        self.commands = [
            '#!/bin/bash',
            'global_start_time=$SECONDS',
            'echo "*** INITIALIZING OUTPUT DIRECTORIES ***"',
            'stage_start_time=$SECONDS',
            f'[ ! -d {self.title}-{self.timestamp} ] && mkdir -p {self.title}-{self.timestamp} > /dev/null',
            f'cd {self.title}-{self.timestamp}',
            'echo "Stage,Time (HH:MM:SS)" >> execution_times.csv'
        ]

        # Create directories for the resolutions and iterations
        for res in self.resolution:
            if self.iterations:
                for niter in self.iterations:
                    self.commands.append(f'mkdir -p res-{res}-i{niter}')
            else:
                self.commands.append(f'mkdir -p k-{res}')

        # Output the initialization stage finished
        self.commands = self.commands + [
            'end_time=$SECONDS',
            'elapsed_time=$((end_time - stage_start_time))',
            'hours=$(($elapsed_time / 3600))',
            'minutes=$(($elapsed_time % 3600 / 60))',
            'seconds=$(($elapsed_time % 60))',
            'formatted_time=$(printf "%02d:%02d:%02d" $hours $minutes $seconds)',
            'echo "Stage 0 Time Elapsed: $formatted_time"',
            'echo "*** DONE ***"'
        ]

        # Get the project root directory
        project_root = self.working_dir

        # Initialize and link stages
        self.stages = [Stage(
                stage, 
                self.input_file, 
                self.network_name, 
                self.resolution, 
                self.iterations,
                self.algorithm,
                self.existing_clustering,
                f'{project_root}/{self.output_dir}/{self.title}-{self.timestamp}',
                i+1
            ) for i, stage in enumerate(data['stages'])]

        for i, stage in enumerate(self.stages):
            if i > 0:
                stage.link_previous_stage(self.stages[i-1])

        for stage in self.stages:
            stage.cast()

        # Fetch cleaned network
        cleaned_file = None
        for stage in self.stages:
            if stage.name == 'cleanup':
                cleaned_file = stage.output_file
        
        if not cleaned_file:
            cleaned_file = self.input_file

        # Fetch CM++ output
        cm_out = None
        for stage in self.stages:
            if stage.name == 'connectivity_modifier':
                cm_out  = stage.output_file      

        # Set network files post cleanup to the cleaned file and set before.json files post CM++ stage
        post_cleaned = False
        post_cm = False
        for stage in self.stages:
            if post_cleaned:
                stage.set_network(f'{project_root}/{self.output_dir}/{self.title}-{self.timestamp}/{cleaned_file}')
            if post_cm:
                stage.set_ub(cm_out)
            if stage.name == 'cleanup':
                post_cleaned = True
            if stage.name == 'connectivity_modifier':
                post_cm = True

        # Get commands for each stage
        for stage in self.stages:
            self.commands = self.commands + stage.get_command()

        # Analysis stage
        self.commands.append('echo "*** ANALYSIS ***"')
        self.commands.append('mkdir analysis')
        self.commands.append('stage_start_time=$SECONDS')

        # Fetch other arguments and run commands
        ind = 0
        for res in self.resolution:
            if self.iterations:
                for iter in self.iterations:
                    other_files = []
                    k = frozenset([res, iter])
                    for stage in self.stages:
                        if stage.name != 'cleanup' and stage.name != 'stats':
                            other_files.append(stage.output_file if type(stage.output_file) != dict else stage.output_file[k])
                    other_args = ' '.join(other_files)
                    self.commands.append(f'Rscript {self.current_script}/scripts/analysis.R {cleaned_file} analysis/{self.network_name}_{res}_n{iter}_analysis.csv {other_args} &')
            else:
                other_files = []
                for stage in self.stages:
                    if stage.name != 'cleanup' and stage.name != 'stats':
                        other_files.append(stage.output_file if type(stage.output_file) != dict else stage.output_file[res])
                    other_args = ' '.join(other_files)
                self.commands.append(f'Rscript {self.current_script}/scripts/analysis.R {cleaned_file} analysis/{self.network_name}_k{res}_analysis.csv {other_args} &')
            
            # Get PIDs
            self.commands.append(f'pids[{ind}]=$!')
            ind += 1

        # Finish stage with timing
        self.commands = self.commands + [
            'for pid in "${pids[@]}"; do',
            '\twait $pid',
            '\texit_status=$?',
            '\tif [ $exit_status -ne 0 ]; then',
            '\t\techo "Analysis Stage Failed"',
            '\tfi',
            'done',
            'end_time=$SECONDS',
            'elapsed_time=$((end_time - stage_start_time))',
            'hours=$(($elapsed_time / 3600))',
            'minutes=$(($elapsed_time % 3600 / 60))',
            'seconds=$(($elapsed_time % 60))',
            'formatted_time=$(printf "%02d:%02d:%02d" $hours $minutes $seconds)',
            f'echo "Analysis Time Elapsed: $formatted_time"',
            f'echo "Analysis,$formatted_time" >> execution_times.csv',
            'echo "*** DONE ***"'
        ]

        # Get overall timing
        self.commands = self.commands + [
            'end_time=$SECONDS',
            'elapsed_time=$((end_time - global_start_time))',
            'hours=$(($elapsed_time / 3600))',
            'minutes=$(($elapsed_time % 3600 / 60))',
            'seconds=$(($elapsed_time % 60))',
            'formatted_time=$(printf "%02d:%02d:%02d" $hours $minutes $seconds)',
            f'echo "Overall Time Elapsed: $formatted_time"',
            'echo "*** PIPELINE DONE ***"'
        ]
    
    def write_script(self):
        os.system(f'mkdir -p {self.working_dir}/{self.output_dir}')
        with open(f"{self.working_dir}/{self.output_dir}/commands.sh", "w") as file:
            file.writelines(line + "\n" for line in self.commands)

    def execute(self):
        try:
            os.system(f'''
                cd {self.working_dir};
                cd {self.output_dir}; 
                chmod +x commands.sh; 
                ./commands.sh | tee pipeline_{self.timestamp}.log; 
                mv commands.sh {self.title}-{self.timestamp}/;
                mv pipeline_{self.timestamp}.log {self.title}-{self.timestamp}/
            ''')
        except KeyboardInterrupt:
            print('Aborted!')
            return

