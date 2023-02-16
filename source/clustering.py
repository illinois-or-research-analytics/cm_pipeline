import logging
import os
import time
from source.stage import Stage
from source.cmd import run
from source.constants import *
from string import Template

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = "$network_name $sep_u $algorithm $sep_d.tsv"

class Clustering(Stage):
    def __init__(self, config_params, network_name, output_dir):
        super().__init__(config_params, network_name, output_dir)

        self.resolutions = self.config[RESOLUTION_KEY].split(',')

        # list of clustering files for different resolutions
        self.output_files = []
    
    def _get_output_file_name_from_template(self, template_str):
        template =  Template(template_str)
        output_file_name = template.substitute(network_name = self.network_name,
                                               algorithm = self.config[ALGORITHM_KEY], 
                                               sep_u='_', 
                                               sep_d='.')
        return output_file_name
    
    def execute(self):
        for resolution in self.resolutions:
            logger.info("Executing Leiden with resolution %s", resolution)
            
            output_file = os.path.join(self.output_dir, 
                                        self._get_output_file_name_from_template(OUTPUT_FILE_NAME))
            self.output_files.append(output_file)

            cmd = ["runleiden", "-i", self.config[INPUT_FILE_KEY], "-r", resolution, "-o", output_file]
            run(cmd)
