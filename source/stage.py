import os
import time
import logging
from source.constants import *

class Stage(object):
    def __init__(self, config):
        self.config = dict(config)
        self._check_paths()
    
    def execute(self):
        
        raise NotImplementedError("Implement the execute function in each subclass")

    def generate_metrics_report(self):
        
        pass 

    def _check_paths(self):
        """
        1. Checks the input and output paths for ~ in the paths and replace it with user home directory.
        """
        path_keys = [INPUT_FILE_KEY, OUTPUT_DIR_KEY, SCRIPT_KEY, CLUSTERINGFILE_KEY]

        for key in path_keys:
            if key in self.config:
                self.config[key] = os.path.expanduser(self.config[key])