from os import path

class Stage:
    def __init__(
            self, 
            data, 
            input_file, 
            network_name, 
            resolutions, 
            iterations, 
            algorithm, 
            working_dir,
            index):
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
            
        # Check if this is a memprof stage
        try:
            self.memprof = data['memprof']
        except:
            self.memprof = False
        
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
                    frozenset([resolution, iteration]): f'{working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{filtering_operation}.tsv'
                    for resolution in resolutions
                    for iteration in iterations
                }
            elif self.name == 'connectivity_modifier':
                self.output_file = {
                    frozenset([resolution, iteration]): f'{working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.tsv.after.tsv'
                    for resolution in resolutions
                    for iteration in iterations
                }
            elif self.name != 'stats':
                self.output_file = {
                    frozenset([resolution, iteration]): f'{working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.tsv'
                    for resolution in resolutions
                    for iteration in iterations
                }
            else:
                self.output_file = {
                    frozenset([resolution, iteration]): f'{working_dir}/res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{self.algorithm}.{resolution}_i{iteration}_{self.name}.csv'
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
        # Get the absolute path of the current script
        current_script = path.abspath(__file__)

        # Get the project root directory
        project_root = path.dirname(path.dirname(current_script))

        # Ouptut stage start and initialize stage time
        cmd = [
            f'echo "*** Starting {self.name} STAGE ***"',
            'stage_start_time=$SECONDS',
            ]

        # Getting the previous file via linked list structure
        prev_file = self.get_previous_file()

        # Get command depending on stage type
        if self.name == 'cleanup':
            cmd.append(f'Rscript {project_root}/scripts/cleanup_el.R {prev_file} {self.output_file}')
        elif self.name == 'clustering':
            if self.algorithm == 'leiden':
                for k, v in self.output_file.items():
                    res, niter = list(sorted(list(k)))
                    cmd.append(f'echo "Currently on resolution {res}, iteration {niter}"')
                    output_file = v
                    input_file = prev_file if type(prev_file) != dict else prev_file[k]
                    cmd.append(f'python {project_root}/scripts/run_leiden.py -i {input_file} -r {res} -o {output_file} -n {niter} &')
                cmd.append('wait')
            # TODO: Get support for IKC
            else:
                raise ValueError('Come back later for IKC support!')
        elif self.name == 'stats':
            for k, v in self.output_file.items():
                res, niter = list(sorted(list(k)))
                cmd.append(f'echo "Currently on resolution {res}, iteration {niter}"')
                output_file = v
                input_file = prev_file if type(prev_file) != dict else prev_file[k]
                c = f'python {project_root}/cluster-statistics/stats.py -i {self.network} -e {input_file} -c {self.algorithm} -o {output_file} '
                
                # Set leiden param, TODO: IKC support for -k
                if self.algorithm == 'leiden':
                    c = c + f'-g {res} '
                else:
                    raise ValueError('Come back later for IKC support!')
                c = c + self.args 
                cmd.append(c + ' &')
            cmd.append('wait')
        elif self.name == 'filtering':
            for k, v in self.output_file.items():
                res, niter = list(sorted(list(k)))
                cmd.append(f'echo "Currently on resolution {res}, iteration {niter}"')
                
                # Iterate through filtering scripts
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
                        cmd.append(f'Rscript {project_root}/scripts/subset_graph_nonetworkit_treestar.R {self.network} {input_file} {output_file}')
                    elif script == "./scripts/make_cm_ready.R":
                        cmd.append(f'Rscript {project_root}/scripts/make_cm_ready.R {input_files[0]} {input_file} {output_file}')
                    elif script == "./scripts/post_cm_filter.R":
                        cmd.append(f'Rscript {project_root}/scripts/post_cm_filter.R {input_file} {output_file}')
        elif self.name == 'connectivity_modifier':
            for k, v in self.output_file.items():
                res, niter = list(sorted(list(k)))
                cmd.append(f'echo "Currently on resolution {res}, iteration {niter}"')
                output_file = v

                # Profile memory usage if the memprof param is true for cm
                if self.memprof:
                    cmd.append(f'{project_root}/hm01/tests/mp-memprofile/profiler.sh python {project_root}/hm01/cm.py -i {self.network} -e {self.get_previous_file()[k]} -o {output_file[:-10]} -c {self.algorithm} -g {res} {self.args}')
                    cmd.append(f'mv profile_* res-{res}-i{niter}')
                else:
                    cmd.append(f'python {project_root}/hm01/cm.py -i {self.network} -e {self.get_previous_file()[k]} -o {output_file[:-10]} -c {self.algorithm} -g {res} {self.args}')
        
        # Output runtime and finish sage
        cmd = cmd + [
            'end_time=$SECONDS',
            'elapsed_time=$((end_time - stage_start_time))',
            'hours=$(($elapsed_time / 3600))',
            'minutes=$(($elapsed_time % 3600 / 60))',
            'seconds=$(($elapsed_time % 60))',
            'formatted_time=$(printf "%02d:%02d:%02d" $hours $minutes $seconds)',
            f'echo "Stage {self.index} Time Elapsed: $formatted_time"',
            f'echo "Stage {self.index} {self.name},$formatted_time" >> execution_times.csv',
            'echo "*** DONE ***"'
        ]

        return cmd


            