import logging
import os
import time
from source.stage import Stage
from source.cmd import run

logger = logging.getLogger(__name__)

class Cleanup(Stage):
    def __init__(self, config_params):
        super().__init__(config_params)
        # Todo: replace placeholder with a fixed output file name
        self.output_file = os.path.join(self.config['outputdir'], f"network_name_{time.strftime('%Y%m%d-%H%M%S')}.tsv")

    def execute(self):
        logger.info("Removing duplicate rows, parallel edges, and self-loops")
        cmd = ["Rscript", self.config['script'], self.config['inputfile'], self.output_file ]
        run(cmd)
