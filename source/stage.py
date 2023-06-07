class Stage:
    def __init__(self, data, input_file, network_name, resolutions, iterations, algorithm, index):
        # Get input params as object params
        self.name = data['name']
        self.network = input_file
        self.network_name = network_name
        self.index = index

        # Get scripts if this is a filtering stage
        if self.name == 'filtering':
            self.scripts = data['scripts']
        
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
            self.output_file = {
                frozenset([resolution, iteration]): f'res-{resolution}-i{iteration}/S{self.index}_{self.network_name}_{algorithm}.{resolution}_i{iteration}_{self.name}.tsv'
                for resolution in resolutions
                for iteration in iterations
            }

    def link_previous_stage(self, stage):
        self.prev = stage

    def get_previous_file(self):
        if self.index == 1:
            return self.network
        else:
            if self.prev.name == 'stats':
                return self.prev.prev.output_file
        return self.prev.output_file