from source.clustering import Clustering

class LeidenClustering(Clustering):
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
        resolutions = [param['res'] for param in self.params]
        iterations = [param['i'] for param in self.params]

        self.output_file = [
            f'{self.working_dir}/{self.algorithm}_res{resolution}_i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.tsv'
            for resolution, iteration in zip(resolutions, iterations)
        ]

    def get_stage_commands(self, project_root, prev_file):
        resolutions = [param['res'] for param in self.params]
        iterations = [param['i'] for param in self.params]
        cmd = []

        counter = 1
        for i, (res, niter, v) in enumerate(zip(resolutions, iterations, self.output_file)):
            cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')
            output_file = v
            input_file = prev_file if type(prev_file) != dict else prev_file[i]
            cmd.append(f'python3 {project_root}/scripts/run_leiden.py -i {input_file} -r {res} -o {output_file} -n {niter} &')
            if counter % self.parallel_limit == 0:
                cmd.append('wait')
            counter += 1
        cmd.append('wait')

        return cmd
