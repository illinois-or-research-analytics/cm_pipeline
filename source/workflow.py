from datetime import datetime
import os

class Workflow:
    def __init__(self, data):
        # Load global parameters
        self.title = data['title']
        self.output_dir = data['output_dir']
        self.input_file = data['input_file']
        self.resolution = data['resolution'] if type(data['resolution']) == list else [data['resolution']]
        self.iterations = data['iterations'] if type(data['iterations']) == list else [data['iterations']]

        # Get timestamp of algo run
        self.timestamp = datetime.now().strftime("%Y%m%d-%H:%M:%S")

        # Initialize first set of commands
        self.commands = [
            '#!/bin/bash',
            'global_start_time=$(date +%s)',
            'echo "*** INITIALIZING OUTPUT DIRECTORIES ***"',
            f'[ ! -d {self.title}-{self.timestamp} ] && mkdir -p {self.title}-{self.timestamp} > /dev/null',
            f'cd {self.title}-{self.timestamp}'
        ]

        # Create directories for the resolutions and iterations
        for res in self.resolution:
            for niter in self.iterations:
                self.commands.append(f'mkdir -p res-{res}-i{niter}')

        # Output that 
    
    def write_script(self):
        with open(f"{self.output_dir}/commands.sh", "w") as file:
            file.writelines(line + "\n" for line in self.commands)

    def execute(self):
        os.system(f'cd {self.output_dir}; chmod +x commands.sh; ./commands.sh')

