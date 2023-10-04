from source.clustering import Clustering
from os import path

class IKCClustering(Clustering):
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
        ks = [params['k'] for params in self.params]

        self.output_file = [
            f'{self.working_dir}/{self.algorithm}_k{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{self.name}_reformatted.tsv'
            for k in ks
        ]

    def get_stage_commands(self, project_root, prev_file):
        ks = [params['k'] for params in self.params]
        cmd = []

        for i, (k, v) in enumerate(zip(ks, self.output_file)):
            cmd.append(f'echo "Currently on k={k}"')
            pre_output_file, _ = path.splitext(v)
            pre_output_file = pre_output_file[:-12] + '.tsv'
            input_file = prev_file if type(prev_file) != list else prev_file[i]
            cmd.append(f'python3 {project_root}/hm01/tools/ikc.py -e {input_file} -o {pre_output_file} -k {k}')
            cmd.append(f'python3 {project_root}/scripts/format_ikc_output.py {pre_output_file}')

        return cmd