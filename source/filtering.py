from os import path
from source.stage import Stage


class Filtering(Stage):
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
        # Filtering stages require scripts
        try:
            self.scripts = data['scripts']
        except:
            raise ValueError('Filtering stages need filtering scripts')
        
        # Set the output file
        filtering_operation = path.basename(self.scripts[-1])
        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            self.output_file = {
                frozenset([resolution, iteration]): f'{self.working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{filtering_operation}.tsv'
                for resolution in self.resolutions
                for iteration in self.iterations
            }
        else:
            self.output_file = {
                k: f'{self.working_dir}/k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{filtering_operation}.tsv'
                for k in self.resolutions
            }
    
    def get_stage_commands(self, project_root, prev_file):
        cmd = []
        
        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            for k, v in self.output_file.items():
                res, niter = self.unpack(k)
                cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')
                
                # Iterate through filtering scripts
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                input_files = [input_file]
                output_files = []
                for i, script in enumerate(self.scripts):
                    filtering_operation = path.basename(script)
                    output_files.append(f'res-{res}-i{niter}/S{self.index}_{self.network_name}_{self.algorithm}.{res}_i{niter}_{filtering_operation}.tsv')
                    if i != len(self.scripts) - 1:
                        input_files.append(f'res-{res}-i{niter}/S{self.index}_{self.network_name}_{self.algorithm}.{res}_i{niter}_{filtering_operation}.tsv')
                for script, input_file, output_file in zip(self.scripts, input_files, output_files):
                    script_file = script.split('/')[-1]
                    if script_file == "subset_graph_nonetworkit_treestar.R":
                        cmd.append(f'Rscript {project_root}/scripts/subset_graph_nonetworkit_treestar.R {self.network} {input_file} {output_file}')
                    elif script_file == "make_cm_ready.R":
                        cmd.append(f'Rscript {project_root}/scripts/make_cm_ready.R {input_files[0]} {input_file} {output_file}')
                    elif script_file == "post_cm_filter.R":
                        cmd.append(f'Rscript {project_root}/scripts/post_cm_filter.R {input_file} {output_file}')
                    cmd = cmd + [
                        'exit_status=$?',
                        'if [ $exit_status -ne 0 ]; then',
                        f'\techo "{output_file} failed to generate"',
                        f'\texit',
                        'fi'
                    ]
        else:
            for k, v in self.output_file.items():
                cmd.append(f'echo "Currently on k={k}"')
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                input_files = [input_file]
                output_files = []
                for i, script in enumerate(self.scripts):
                    filtering_operation = path.basename(script)
                    output_files.append(f'k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{filtering_operation}.tsv')
                    if i != len(self.scripts) - 1:
                        input_files.append(f'k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{filtering_operation}.tsv')
                for script, input_file, output_file in zip(self.scripts, input_files, output_files):
                    script_file = script.split('/')[-1]
                    if script_file == "subset_graph_nonetworkit_treestar.R":
                        cmd.append(f'Rscript {project_root}/scripts/subset_graph_nonetworkit_treestar.R {self.network} {input_file} {output_file}')
                    elif script_file == "make_cm_ready.R":
                        cmd.append(f'Rscript {project_root}/scripts/make_cm_ready.R {input_files[0]} {input_file} {output_file}')
                    elif script_file == "post_cm_filter.R":
                        cmd.append(f'Rscript {project_root}/scripts/post_cm_filter.R {input_file} {output_file}')
                    cmd = cmd + [
                        'exit_status=$?',
                        'if [ $exit_status -ne 0 ]; then',
                        f'\techo "{output_file} failed to generate"',
                        f'\texit',
                        'fi'
                    ]

        return cmd