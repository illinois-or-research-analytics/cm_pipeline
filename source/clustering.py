import logging
import os
import time
from source.stage import Stage
from source.cmd import run
from source.constants import *

logger = logging.getLogger(__name__)

class Clustering(Stage):
    def __init__(self, config):
        super().__init__(config)
        
        os.makedirs(self.config[OUTPUT_DIR_KEY], exist_ok=True)
        # Todo: replace placeholder with a fixed output file name
        self.output_file = os.path.join(self.config[OUTPUT_DIR_KEY], f"placeholder_{time.strftime('%Y%m%d-%H%M%S')}.tsv")
        self.resolutions = self.config[RESOLUTION_KEY].split(',')
    
    def execute(self):
        for resolution in self.resolutions:
            logger.info("Executing Leiden with resolution %s", resolution)
            cmd = ["runleiden", "-i", self.config[INPUT_FILE_KEY], "-r", resolution, "-o", self.output_file]
            run(cmd)
