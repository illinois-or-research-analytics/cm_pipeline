import os
import time
import logging
from string import Template
from source.constants import *

class Stage(object):
    def __init__(self, config, network_name, output_dir, stage_num, prev_stage=None):
        self.config = dict(config)
        self.network_name = network_name
        self.stage_num = stage_num
        self.prev_stage = prev_stage
        self.output_dir = output_dir
        self._check_paths()
        
    def execute(self):
        raise NotImplementedError("Implement the execute function in each subclass")

    def generate_metrics_report(self):
        
        pass 

    def _check_paths(self):
        """
        1. Checks the input and output paths for ~ in the paths and replace it with user home directory.
        """
        # default dir
        self.output_dir = os.path.expanduser(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        # other paths in config file
        path_keys = [INPUT_FILE_KEY, SCRIPT_KEY, CLUSTERING_FILE_KEY, INPUT_CLUSTERING_FILE_DIR_KEY, CLEANED_INPUT_FILE_KEY]
        for key in path_keys:
            if key in self.config:
                self.config[key] = os.path.expanduser(self.config[key])