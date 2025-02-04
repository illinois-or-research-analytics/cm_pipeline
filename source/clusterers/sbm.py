from source.clustering import Clustering
from os import path

class SBMClustering(Clustering):
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

    def initialize_clustering(self):
        self.output_file =  f'{self.working_dir}/{self.algorithm}_degree_corrected{self.params[0]["degree_corrected"]}_block_state{self.params[0]["block_state"]}/S{self.index}_{self.network_name}_{self.algorithm}_{self.name}.tsv'

    def get_stage_commands(self, project_root, prev_file):
        return [
            f'python3 {project_root}/scripts/run_sbm.py -i {prev_file} -o {self.output_file} -b {self.params[0]["block_state"]} -d {self.params[0]["degree_corrected"]}'
        ]
