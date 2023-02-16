import logging
import os
import time
from source.stage import Stage
from source.cmd import run
from source.constants import *
from string import Template

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = '${network_name}_cleaned.tsv'

class Cleanup(Stage):
    def __init__(self, config_params, network_name, output_dir):
        super().__init__(config_params, network_name, output_dir)
        
        self.output_file = os.path.join(self.output_dir, self._get_output_file_name_from_template(OUTPUT_FILE_NAME))
    
    def _get_output_file_name_from_template(self, template_str):
        template =  Template(template_str)
        output_file_name = template.substitute(network_name = self.network_name)
        return output_file_name
    
    def execute(self):
        logger.info("Removing duplicate rows, parallel edges, and self-loops")
        cmd = ["Rscript", self.config[SCRIPT_KEY], self.config[INPUT_FILE_KEY], self.output_file ]
        run(cmd)
