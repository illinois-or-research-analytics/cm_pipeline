import os
from collections import OrderedDict
from string import Template
from source.constants import *

class Stage(object):
    def __init__(self, config, default_config, stage_num, prev_stages=OrderedDict()):
        self.config = dict(config)
        self.default_config = default_config
        self.stage_num = stage_num
        self.prev_stages = prev_stages
        self._check_paths()
        
    def execute(self):
        raise NotImplementedError("Implement the execute function in each subclass")
    
    def _get_output_file_name_from_template(self, template_str, resolution):
        template =  Template(template_str)
        output_file_name = template.substitute(network_name=self.default_config.network_name,
                                               algorithm=self.default_config.algorithm, 
                                               resolution=resolution,
                                               stage_num=self.stage_num)
        return output_file_name
    
    def generate_metrics_report(self):
        
        pass 

    def _check_paths(self):
        """
        1. Checks the input and output paths for ~ in the paths and replace it with user home directory.
        """
        # default dir
        self.default_config.output_dir = os.path.expanduser(self.default_config.output_dir)
        os.makedirs(self.default_config.output_dir, exist_ok=True)

        # other paths in config file
        path_keys = [INPUT_FILE_KEY, 
                     CLUSTERING_SCRIPT_KEY, 
                     CLEANUP_SCRIPT_KEY,
                     CLUSTERING_FILE_KEY, 
                     INPUT_CLUSTERING_FILE_DIR_KEY, 
                     CLEANED_INPUT_FILE_KEY,
                     FILTERING_SCRIPT_KEY]
        for key in path_keys:
            if key in self.config:
                self.config[key] = os.path.expanduser(self.config[key])