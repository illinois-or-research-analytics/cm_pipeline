from os import path
from source.stage import Stage


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
    
    def get_output():
        pass