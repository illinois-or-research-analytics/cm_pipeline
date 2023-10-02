from os import path
from source.stage import Stage
from math import inf


class Clustering(Stage):
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
        if self.algorithm == 'ikc':
            self.output_file = {
                k: f'{self.working_dir}/k-{k}/S{self.index}_{self.network_name}_{self.algorithm}.{k}_{self.name}_reformatted.tsv'
                for k in self.resolutions
            }
        else:
            self.output_file = {
                frozenset([resolution, iteration]): f'{self.working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.csv'
                for resolution in self.resolutions
                for iteration in self.iterations
            }

    def get_stage_commands(self, project_root, prev_file):
        cmd = []

        if self.algorithm == 'leiden':
            counter = 1
            for k, v in self.output_file.items():
                res, niter = list(sorted(list(k)))
                cmd.append(f'echo "Currently on resolution {res}, running {niter} iterations"')
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                cmd.append(f'python3 {project_root}/scripts/run_leiden.py -i {input_file} -r {res} -o {output_file} -n {niter} &')
                if counter % self.parallel_limit == 0:
                    cmd.append('wait')
                counter += 1
            cmd.append('wait')
        elif self.algorithm == 'leiden_mod':
            counter = 1
            print(self.output_file)
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
        # TODO: Get support for IKC
        else:
            for k, v in self.output_file.items():
                cmd.append(f'echo "Currently on k={k}"')
                pre_output_file, ext = path.splitext(v)
                pre_output_file = pre_output_file[:-12] + '.tsv'
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                cmd.append(f'python3 {project_root}/hm01/tools/ikc.py -e {input_file} -o {pre_output_file} -k {k}')
                cmd.append(f'python3 {project_root}/scripts/format_ikc_output.py {pre_output_file}')

        return cmd