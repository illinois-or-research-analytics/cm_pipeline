from os import path
from source.stage import Stage
from math import inf


class Stats(Stage):
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

        try:
            self.parallel_limit = data['parallel_limit']
        except:
            self.parallel_limit = inf
        
    def get_output(self):
        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            self.output_file = {
                frozenset([resolution, iteration]): f'{self.working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.tsv'
                for resolution in self.resolutions
                for iteration in self.iterations
            }
        else:
            self.output_file = {
                k: f'{self.working_dir}/k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{self.name}.tsv'
                for k in self.resolutions
            }
        
    def get_stage_commands(self, project_root, prev_file):
        cmd = []
        counter = 1
        if self.algorithm == 'leiden' or self.algorithm == 'leiden_mod':
            for k, v in self.output_file.items():
                res, niter = self.unpack(k)
                cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                c = f'python3 {project_root}/cluster-statistics/stats.py -i {self.network} -e {input_file} -c {self.algorithm} -o {output_file} '
                
                # Set leiden param, TODO: IKC support for -k
                if self.algorithm == 'leiden':
                    c = c + f'-g {res} '
                elif self.algorithm == 'ikc':
                    raise ValueError('Come back later for IKC support!')
                c = c + self.args 

                # If there is a universal before parameter, set it
                if self.universal_before:
                    try:
                        c = c + ' --universal-before ' + self.ub[k]
                    except:
                        raise ValueError('Cannot find a before.json file: double check that this stats stage comes after a CM++ stage.')

                cmd.append(c + ' &')

                if counter % self.parallel_limit == 0:
                    cmd.append('wait')
                
                counter += 1
            cmd.append('wait')
        else:
            for k, v in self.output_file.items():
                cmd.append(f'echo "Currently on k={k}"')
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                c = f'python3 {project_root}/cluster-statistics/stats.py -i {self.network} -e {input_file} -c {self.algorithm} -o {output_file} -k {k} '
                c = c + self.args 
                cmd.append(c)

        # If the summarize value is set to true, output summary stats
        if self.summarize:
            for k, v in self.output_file.items():
                cmd.append(f'python3 {project_root}/cluster-statistics/summarize.py {v} {self.network}')

        return cmd
    
    def get_previous_file(self):
        try:
            return self.prev.prev.output_file
        except:
            return self.existing_clustering
        
        