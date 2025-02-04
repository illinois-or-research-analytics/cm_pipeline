from source.stage import Stage
from json import dumps
from os import path


class CM(Stage):
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
        self.args = ''
        for key, val in data.items():
            if \
                key != 'name' and \
                key != 'memprof' and \
                key != 'universal_before' and \
                key != 'cfile':

                self.args = self.args + '--' + key + ' '
                if type(val) != bool:
                    self.args = self.args + str(val) + ' '

        # Set universal before and summarize values if they exist
        try:
            self.universal_before = data['universal_before']
        except:
            self.universal_before = False

        try:
            self.cfile = path.realpath(data['cfile'])
        except:
            self.cfile = None

        self.output_file = []
        for param in self.params:
            param_string = ''
            for k, v in param.items():
                param_string += f'_{k}{v}'
            
            self.output_file.append(f'{self.working_dir}/{self.algorithm}{param_string}/S{self.index}_{self.network_name}_{self.algorithm}.{self.name}{param_string}.tsv')

    def stage_commands_leiden(self, project_root):
        cmd = []
        resolutions = [param['res'] for param in self.params]
        iterations = [param['i'] for param in self.params]

        for i, (res, niter, output_file) in enumerate(zip(resolutions, iterations, self.output_file)):
            cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')

            c = f'{project_root}/hm01/tests/mp-memprofile/profiler.sh ' if self.memprof else ''

            c = c + f'python3 -m hm01.cm \
                -i {self.network} \
                    -e {self.get_previous_file()[i]} \
                        -o {output_file} \
                            -c {self.algorithm} {self.args}'

            if self.algorithm == 'leiden':
                c = c + f'-g {res}'
            
            cmd.append(c)

            cmd = cmd + [
                'exit_status=$?',
                'if [ $exit_status -ne 0 ]; then',
                f'\techo "{output_file} failed to generate"',
                f'\texit',
                'fi'
            ]

            # Profile memory usage if the memprof param is true for cm
            if self.memprof:
                cmd.append(f'mv profile_* {self.algorithm}_res{res}_i{niter}')

        return cmd
    
    def stage_commands_leidenmod(self, project_root):
        cmd = []
        iterations = [param['i'] for param in self.params]

        for i, (niter, output_file) in enumerate(zip(iterations, self.output_file)):
            cmd.append(f'echo "Currently running {niter} iterations"')

            c = f'{project_root}/hm01/tests/mp-memprofile/profiler.sh ' if self.memprof else ''

            c = c + f'python3 -m hm01.cm \
                -i {self.network} \
                    -e {self.get_previous_file()[i]} \
                        -o {output_file} \
                            -c {self.algorithm} {self.args}'
            
            cmd.append(c)

            cmd = cmd + [
                'exit_status=$?',
                'if [ $exit_status -ne 0 ]; then',
                f'\techo "{output_file} failed to generate"',
                f'\texit',
                'fi'
            ]

            # Profile memory usage if the memprof param is true for cm
            if self.memprof:
                cmd.append(f'mv profile_* {self.algorithm}_i{niter}')

        return cmd
    
    def stage_commands_ikc(self, project_root):
        cmd = []
        ks = [param['k'] for param in self.params]

        for i, (k, output_file) in enumerate(zip(ks, self.output_file)):
            cmd.append(f'echo "Currently on k={k}"')

            c = f'{project_root}/hm01/tests/mp-memprofile/profiler.sh ' if self.memprof else ''
            c = c + f'python3 -m hm01.cm \
                -i {self.network} \
                    -e {self.get_previous_file()[i]} \
                        -o {output_file} \
                            -c {self.algorithm} {self.args}'
            c = c + f' -k {k}'

            cmd.append(c)

            cmd = cmd + [
                'exit_status=$?',
                'if [ $exit_status -ne 0 ]; then',
                f'\techo "{output_file} failed to generate"',
                f'\texit',
                'fi'
            ]

            # Profile memory usage if the memprof param is true for cm
            if self.memprof:
                cmd.append(f'mv profile_* {self.algorithm}_k{k}')

        return cmd
    
    def stage_commands_other(self, project_root, prev_file):
        cmd = []

        for i, (param, output_file) in enumerate(zip(self.params, self.output_file)):
            cmd.append(f'echo "Currently on param set {i}"')

            cmd.append(f"echo '{dumps(param)}' > cargs.json")

            c = f'{project_root}/hm01/tests/mp-memprofile/profiler.sh ' if self.memprof else ''
            c = c + f'python3 -m hm01.cm \
                -i {self.network} \
                    -e {prev_file[i] if type(prev_file) == list else prev_file} \
                        -o {output_file} \
                            -c external \
                                -cfile {self.cfile} \
                                    -cargs cargs.json {self.args}'
            
            cmd.append(c)

            cmd = cmd + [
                'exit_status=$?',
                'if [ $exit_status -ne 0 ]; then',
                f'\techo "{output_file} failed to generate"',
                f'\texit',
                'fi'
            ]

            # Profile memory usage if the memprof param is true for cm
            if self.memprof:
                cmd.append(f'mv profile_* {self.get_folder_name(param)}')

        return cmd


    def get_stage_commands(self, project_root, prev_file):
        if self.algorithm == 'leiden':
            return self.stage_commands_leiden(project_root)
        elif self.algorithm == 'leiden_mod':
            return self.stage_commands_leidenmod(project_root)
        elif self.algorithm == 'ikc':
            return self.stage_commands_ikc(project_root)
        else:
            return self.stage_commands_other(project_root, prev_file)
