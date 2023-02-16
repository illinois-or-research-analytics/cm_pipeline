import logging
import os
import time
from source.stage import Stage
from source.cmd import run
from source.constants import *

logger = logging.getLogger(__name__)

class Filtering(Stage):
    def __init__(self, config_params):
        super().__init__(config_params)
        os.makedirs(self.config[OUTPUT_DIR_KEY], exist_ok=True)
        # Todo: replace placeholder with a fixed output file name at the end
        self.output_file = os.path.join(self.config[OUTPUT_DIR_KEY], f"placeholder_{time.strftime('%Y%m%d-%H%M%S')}.tsv")

    def execute(self):
        logger.info("Filtering to get clusters with N>10 and non-trees")
        cmd = ["Rscript", self.config[SCRIPT_KEY], self.config[INPUT_FILE_KEY], self.config[CLUSTERINGFILE_KEY, self.config[OUTPUTFILETAG_KEY]] ]
        run(cmd)
