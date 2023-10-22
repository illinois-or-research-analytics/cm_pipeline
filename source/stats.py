from os import path
from source.stage import Stage
from math import inf


class Stats(Stage):
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
            index
    ):
        super().__init__(
            data, 
            input_file, 
            network_name,
            resolutions,
            iterations,
            algorithm,
            existing_clustering,
            working_dir,
            index)
        
    def initialize(self, data):
        self.chainable = False
        self.outputs_clustering = False

        try:
            self.summarize = data['summarize']
        except:
            self.summarize = False

        self.args = ''
        for key, val in data.items():
            if \
                key != 'summarize' and \
                key != 'parallel_limit' and \
                key != 'name' and \
                key != 'memprof' and \
                key != 'universal_before':

                self.args = self.args + '--' + key + ' '
                if type(val) != bool:
                    self.args = self.args + str(val) + ' '
        
        try:
            self.universal_before = data["universal_before"]
        except:
            self.universal_before = False

        try:
            self.parallel_limit = data['parallel_limit']
        except:
            self.parallel_limit = inf

        self.output_file = []
        for param in self.params:
            folder_name = self.get_folder_name(param)

            suffix = ''
            for k, v in param.items():
                suffix += f'{k}{v}_'

            self.output_file.append(f'{self.working_dir}/{folder_name}/S{self.index}_{self.network_name}_{self.algorithm}.{suffix}{self.name}.csv')
        
    def get_stage_commands(self, project_root, prev_file):
        cmd = []
        counter = 1

        for i, param in enumerate(self.params):
            cmd.append(f'echo "Currently on param set {i}"')

            output_file = self.output_file[i]
            input_file = prev_file if type(prev_file) != list else prev_file[i]

            c = f'python3 {project_root}/scripts/stats.py \
                -i {self.network} \
                    -e {input_file} \
                        -o {output_file} {self.args}'
            
            if 'res' in param:
                c += f'-g {param["res"]} '

            if self.universal_before:
                try:
                    c = c + ' --universal-before ' + self.ub[i]
                except:
                    raise ValueError('Cannot find a before.json file: double check that this stats stage comes after a CM++ stage.')
                
            cmd.append(c + ' &')

            if counter % self.parallel_limit == 0:
                cmd.append('wait')
            
            counter += 1
        cmd.append('wait')

        # If the summarize value is set to true, output summary stats
        if self.summarize:
            for v in self.output_file:
                cmd.append(f'python3 {project_root}/scripts/summarize.py {v} {self.network}')

        return cmd
    
        
        