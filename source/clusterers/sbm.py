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
        block_states = [param["block_state"] for param in self.params]
        degree_correcteds = [param["degree_corrected"] if "degree_corrected" in param else "NA" for param in self.params]

        # self.output_file =  f'{self.working_dir}/{self.algorithm}_degree_corrected{self.params[0]["degree_corrected"]}_block_state{self.params[0]["block_state"]}/S{self.index}_{self.network_name}_{self.algorithm}_{self.name}.tsv'
        output_files = []
        for param in self.params:
            current_output_file = f'{self.working_dir}/{self.algorithm}'
            for k, v in param.items():
                if k != 'existing_clustering':
                    current_output_file += f'_{k}{v}'
            current_output_file += f"/S{self.index}_{self.network_name}_{self.algorithm}_{self.name}.tsv"
            output_files.append(current_output_file)
        self.output_file = output_files

        # self.output_file = [
        #     f'{self.working_dir}/{self.algorithm}_block_state{block_state}_degree_corrected{degree_corrected}/S{self.index}_{self.network_name}_{self.algorithm}_{self.name}.tsv'
        #     for block_state,degree_corrected in zip(block_states, degree_correcteds)
        # ]

    def get_stage_commands(self, project_root, prev_file):
        # return [
        #     f'python3 {project_root}/scripts/run_sbm.py -i {prev_file} -o {self.output_file} -b {self.params[0]["block_state"]} -d {self.params[0]["degree_corrected"]}'
        # ]

        block_states = [param["block_state"] for param in self.params]
        degree_correcteds = [param["degree_corrected"] if "degree_corrected" in param else "NA" for param in self.params]
        cmd = []

        for i, (block_state, degree_corrected, v) in enumerate(zip(block_states, degree_correcteds, self.output_file)):
            cmd.append(f'echo "Currently on degree_corrected={degree_corrected}, block_state={block_state}"')
            output_file = v
            input_file = prev_file if type(prev_file) != list else prev_file[i]
            cmd.append(f'python3 {project_root}/scripts/run_sbm.py -i {input_file} -o {output_file} -b {block_state} -d {degree_corrected}')
        return cmd
