import logging
import os
import time
from source.stage import Stage
from source.cmd import run
from source.constants import *

logger = logging.getLogger(__name__)

class Filtering(Stage):
    def __init__(self, config_params, network_name, output_dir):
        super().__init__(config_params, network_name, output_dir)

    def execute(self):
        logger.info("Filtering to get clusters with N>10 and non-trees")
        cmd = ["Rscript", self.config[SCRIPT_KEY], self.config[INPUT_FILE_KEY], self.config[CLUSTERING_FILE_KEY], self.config[OUTPUT_FILE_TAG_KEY]] 
        run(cmd)
