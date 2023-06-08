from os import path

class Stage:
    def __init__(self, data, input_file, network_name, resolutions, iterations, algorithm, index):
        # Get input params as object params
        self.name = data['name']
        self.network = input_file
        self.network_name = network_name
        self.index = index
        self.algorithm = algorithm

        # Get scripts if this is a filtering stage
        if self.name == 'filtering':
            try:
                self.scripts = data['scripts']
            except:
                raise ValueError('Filtering stages need filtering scripts')
        
        # Get extra arguments
        self.args = ''
        for key, val in data.items():
            if key != 'scripts' and key != 'memprof' and key != 'name':
                self.args = self.args + '--' + key + ' '
                if type(val) != bool:
                    self.args = self.args + str(val) + ' '

        # Output file nomenclature
        if self.index == 1:
            if self.name == 'stats':
                raise ValueError("First stage cannot be a stats stage.")
            self.output_file = f'S1_{self.network_name}_{self.name}.tsv'
        else:
            if self.name == 'filtering':
                filtering_operation = path.basename(self.scripts[-1])
                self.output_file = {
                    frozenset([resolution, iteration]): f'res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{filtering_operation}.tsv'
                    for resolution in resolutions
                    for iteration in iterations
                }
            elif self.name != 'stats':
                self.output_file = {
                    frozenset([resolution, iteration]): f'res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.tsv'
                    for resolution in resolutions
                    for iteration in iterations
                }
            else:
                self.output_file = {
                    frozenset([resolution, iteration]): f'res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.csv'
                    for resolution in resolutions
                    for iteration in iterations
                }

    def link_previous_stage(self, stage):
        ''' Build reverse linked list from stage array '''
        self.prev = stage

    def get_previous_file(self):
        ''' Get the previous file to use for the current stages input '''
        if self.index == 1:
            return self.network
        else:
            if self.prev.name == 'stats':
                return self.prev.prev.output_file
        return self.prev.output_file
    
    def get_command(self):
        prev_file = self.get_previous_file()
        if self.name == 'cleanup':
            cmd = [f'Rscript ./scripts/cleanup_el.R {prev_file} {self.output_file}']
        elif self.name == 'clustering':
            if self.algorithm == 'leiden':
                cmd = []
                for k, v in self.output_file.items():
                    res, niter = list(sorted(list(k)))
                    output_file = v
                    input_file = prev_file if type(prev_file) != dict else prev_file[k]
                    cmd.append(f'python ./scripts/run_leiden.py -i {input_file} -r {res} -o {output_file} -n {niter} &')
            else:
                raise ValueError('Come back later for IKC support!')
            cmd.append('wait')
        elif self.name == 'stats':
            cmd = []
            for k, v in self.output_file.items():
                res, niter = list(sorted(list(k)))
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                c = f'python ./cluster-statistics/stats.py -i {self.network} -e {input_file} -c {self.algorithm} -o {output_file} '
                if self.algorithm == 'leiden':
                    c = c + f'-g {res} '
                else:
                    raise ValueError('Come back later for IKC support!')
                c = c + self.args + ' &'
                cmd.append(c)
            cmd.append('wait')
        elif self.name == 'filtering':
            cmd = []
            for k, v in self.output_file.items():
                res, niter = list(sorted(list(k)))
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
                    if script == "./scripts/subset_graph_nonetworkit_treestar.R":
                        cmd.append(f'Rscript {script} {self.network} {input_file} {output_file}')
                    elif script == "./scripts/make_cm_ready.R":
                        cmd.append(f'Rscript {script} {input_files[0]} {input_file} {output_file}')
                    elif script == "./scripts/post_cm_filter.R":
                        cmd.append(f'Rscript {script} {input_file} {output_file}')
        else:
            cmd = []
        return cmd


            