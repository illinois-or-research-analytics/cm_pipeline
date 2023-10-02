from source.clustering import Clustering

class LeidenModClustering(Clustering):
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
        self.output_file = {
            frozenset([resolution, iteration]): f'{self.working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.csv'
            for resolution in self.resolutions
            for iteration in self.iterations
        }

    def get_stage_commands(self, project_root, prev_file):
        cmd = []

        counter = 1
        for k, v in self.output_file.items():
            res, niter = self.unpack(k)
            cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')
            output_file = v
            input_file = prev_file if type(prev_file) != dict else prev_file[k]
            cmd.append(f'python3 {project_root}/scripts/run_leiden_mod.py -i {input_file} -o {output_file} -n {niter} &')
            if counter % self.parallel_limit == 0:
                cmd.append('wait')
            counter += 1
        cmd.append('wait')