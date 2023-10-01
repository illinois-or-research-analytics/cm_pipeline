from abc import ABC, abstractmethod
from os import path
from typedict import stage_classes

class Stage:
    def __init__(
            self, 
            data, 
            input_file, 
            network_name, 
            resolutions, 
            iterations, 
            algorithm, 
            existing_clustering,
            working_dir,
            index):
        # Get input params as object params
        self.name = data['name']
        self.network = input_file
        self.network_name = network_name
        self.index = index
        self.algorithm = algorithm
        self.existing_clustering = existing_clustering
        self.working_dir = working_dir
        self.resolutions = resolutions
        self.iterations = iterations
            
        # Check if this is a memprof stage
        try:
            self.memprof = data['memprof']
        except:
            self.memprof = False
        
        # Get extra arguments
        # TODO: Args field in json
        self.args = ''
        for key, val in data.items():
            if key != 'scripts' and key != 'memprof' and key != 'name' and key != 'parallel_limit' and key != "universal_before" and key != 'summarize':
                self.args = self.args + '--' + key + ' '
                if type(val) != bool:
                    self.args = self.args + str(val) + ' '

        # Set universal before and summarize values if they exists
        try:
            self.universal_before = data['universal_before']
        except:
            self.universal_before = False

        try:
            self.summarize = data['summarize']
        except:
            self.summarize = False

        # Output file nomenclature
        if self.index == 1 and type(self.existing_clustering) != dict:
            self.output_file = f'S1_{self.network_name}_{self.name}.tsv'
        else:
            if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
                self.output_file = {
                    frozenset([resolution, iteration]): f'{working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.csv'
                    for resolution in resolutions
                    for iteration in iterations
                }
            else:
                self.output_file = {
                    k: f'{working_dir}/k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{self.name}.csv'
                    for k in resolutions
                }

            self.get_output()

    def set_ub(self, cm_output):
        ''' Set the universal before file from CM2Universal dynamically '''

        # Reformat filename to fetch before.json file
        ub_output = {
            k: f'{path.splitext(path.splitext(cm_output[k])[0])[0]}.before.json'
            for k in cm_output
        }

        self.ub = ub_output

    def set_network(self, network_file):
        ''' Set the input network file in case theres a cleaning stage '''
        self.network = network_file

    def link_previous_stage(self, stage):
        ''' Build reverse linked list from stage array '''
        self.prev = stage

    def get_previous_file(self):
        ''' Get the previous file to use for the current stages input '''
        if self.index == 1:
            if not self.existing_clustering:
                return self.network
            else:
                return self.existing_clustering

        return self.prev.output_file
    
    def unpack(self, k):
        try:
            res, niter = list(sorted(list(k)))
        except:
            for val in list(k):
                if type(val) == str:
                    res = val
                else:
                    niter = val
        return res, niter
    
    def get_command(self):
        # Get the absolute path of the current script
        current_script = path.abspath(__file__)

        # Get the project root directory
        project_root = path.dirname(path.dirname(current_script))

        # Getting the previous file via linked list structure
        prev_file = self.get_previous_file()

        # Ouptut stage start and initialize stage time
        cmd = [
            f'echo "*** Starting {self.name} STAGE ***"',
            'stage_start_time=$SECONDS',
            ]
        
        stage_commands = self.get_stage_commands(project_root, prev_file)

        # Output runtime and finish sage
        end_cmd = [
            'end_time=$SECONDS',
            'elapsed_time=$((end_time - stage_start_time))',
            'hours=$(($elapsed_time / 3600))',
            'minutes=$(($elapsed_time % 3600 / 60))',
            'seconds=$(($elapsed_time % 60))',
            'formatted_time=$(printf "%02d:%02d:%02d" $hours $minutes $seconds)',
            f'echo "Stage {self.index} Time Elapsed: $formatted_time"',
            f'echo "Stage {self.index} {self.name},$formatted_time" >> execution_times.csv',
            'echo "*** DONE ***"'
        ]

        return cmd + stage_commands + end_cmd
    
    def cast(self):
        if self.name in stage_classes.keys():
            self.__class__ = stage_classes[self.name]
    
    @abstractmethod
    def get_stage_commands(self, project_root, prev_file):
        pass

    @abstractmethod
    def get_output(self):
        pass