from os import path
from source.stage import Stage


class Cleanup(Stage):
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
        self.outputs_clustering = False
    
    def get_stage_commands(self, project_root, prev_file):
        return [f'Rscript {project_root}/scripts/cleanup_el.R {prev_file} {self.output_file}']
