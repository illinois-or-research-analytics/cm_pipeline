from abc import abstractmethod
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
        
    def initialize(self, data):
        for key, val in data.items():
            if \
                key != 'name' and \
                key != 'parallel_limit' and \
                key != 'memprof':

                self.args = self.args + '--' + key + ' '
                if type(val) != bool:
                    self.args = self.args + str(val) + ' '

        try:
            self.parallel_limit = data['parallel_limit']
        except:
            self.parallel_limit = inf

    @abstractmethod
    def get_stage_commands(self, project_root, prev_file):
        pass
    
    @abstractmethod
    def initialize_clustering(self):
        pass