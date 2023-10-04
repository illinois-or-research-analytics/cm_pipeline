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
        for key, val in data.items():
            if \
                key != 'scripts' and \
                key != 'name' and \
                key != 'memprof':

                self.args = self.args + '--' + key + ' '
                if type(val) != bool:
                    self.args = self.args + str(val) + ' '

        # Filtering stages require scripts
        try:
            self.scripts = data['scripts']
        except:
            raise ValueError('Filtering stages need filtering scripts')
        
        # Set the output file
        filtering_operation = path.basename(self.scripts[-1])

        self.output_file = []
        for param in self.params:
            folder_name = self.get_folder_name(param)
            suffix = ''
            for k, v in param.items():
                suffix += f'{k}{v}_'
            
            self.output_file.append(f'{self.working_dir}/{folder_name}/S{self.index}_{self.network_name}_{self.algorithm}.{suffix}{filtering_operation}.tsv')
    
    def get_stage_commands(self, project_root, prev_file):
        cmd = []

        for j, (param, output_file) in enumerate(zip(self.params, self.output_file)):
            folder_name = self.get_folder_name(param)
            suffix = ''
            for k, v in param.items():
                suffix += f'{k}{v}_'
            
            cmd.append(f"echo Currently on parameter set {j}")

            input_file = prev_file if type(prev_file) != list else prev_file[j]
            input_files = [input_file]
            output_files = []

            for i, script in enumerate(self.scripts):
                filtering_operation = path.basename(script)
                curr_output_file = f'{folder_name}/S{self.index}_{self.network_name}_{self.algorithm}.{suffix}{filtering_operation}.tsv'
                output_files.append(curr_output_file)
                if i != len(self.scripts) - 1:
                    input_files.append(curr_output_file)

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