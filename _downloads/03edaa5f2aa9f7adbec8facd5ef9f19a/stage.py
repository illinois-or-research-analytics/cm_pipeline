from abc import abstractmethod
from os import path


class Stage:
    def __init__(
            self, 
            data, 
            input_file, 
            network_name, 
            params, 
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
        self.params = params

        # Exclude the passed in existing clustering from the params
        for i, param in enumerate(self.params):
            if 'existing_clustering' in param:
                del self.params[i]['existing_clustering']

        # For the analysis stage
        self.outputs_clustering = True

        # A chainable stage is one whose output can be used for the next stage
        # non-e.g. is stats
        self.chainable = True
            
        # Check if this is a memprof stage
        try:
            self.memprof = data['memprof']
        except:
            self.memprof = False

    def set_ub(self, cm_output):
        ''' Set the universal before file from CM2Universal dynamically '''

        # Reformat filename to fetch before.json file
        ub_output = [
            f'{path.splitext(path.splitext(cm_output[k])[0])[0]}.before.json'
            for k, _ in enumerate(cm_output)
        ]

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
            
        if not self.prev.chainable:
            try:
                return self.prev.prev.output_file
            except:
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
    
    def get_folder_name(self, param):
        ret = self.algorithm

        for k, v in param.items():
            ret += f'_{k}{v}'

        return ret
    
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
    
    @abstractmethod
    def get_stage_commands(self, project_root, prev_file):
        pass

    @abstractmethod
    def initialize(self, data):
        pass