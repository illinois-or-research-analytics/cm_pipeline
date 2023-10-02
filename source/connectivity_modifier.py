from source.stage import Stage


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
        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            self.output_file = {
                frozenset([resolution, iteration]): f'{self.working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.tsv.after.tsv'
                for resolution in self.resolutions
                for iteration in self.iterations
            }
        else:
            self.output_file = {
                k: f'{self.working_dir}/k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{self.name}.tsv.after.tsv'
                for k in self.resolutions
            }

    def get_stage_commands(self, project_root, prev_file):
        cmd = []

        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            for k, v in self.output_file.items():
                res, niter = self.unpack(k)
                cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')
                output_file = v

                c = f'{project_root}/hm01/tests/mp-memprofile/profiler.sh ' if self.memprof else ''

                c = c + f'python3 {project_root}/hm01/cm.py -i {self.network} -e {self.get_previous_file()[k]} -o {output_file[:-10]} -c {self.algorithm} {self.args}'

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
                    cmd.append(f'mv profile_* res-{res}-i{niter}')
        else:
            for k, v in self.output_file.items():
                cmd.append(f'echo "Currently on k={k}"')
                output_file = v

                c = f'{project_root}/hm01/tests/mp-memprofile/profiler.sh ' if self.memprof else ''
                c = c + f'python3 {project_root}/hm01/cm.py -i {self.network} -e {self.get_previous_file()[k]} -o {output_file[:-10]} -c {self.algorithm} {self.args}'
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
                    cmd.append(f'mv profile_* k-{k}')

        return cmd