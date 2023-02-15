import logging
import os
import time
from source.stage import Stage
from source.cmd import run

logger = logging.getLogger(__name__)

class Clustering(Stage):
    def __init__(self, config):
        super().__init__(config)
        
         # Todo: replace placeholder with a fixed output file name
        os.makedirs(self.config['outputdir'], exist_ok=True)
        self.output_file = os.path.join(self.config['outputdir'], f"placeholder_{time.strftime('%Y%m%d-%H%M%S')}.tsv")
        self.resolutions = self.config['resolution'].split(',')
    
    def execute(self):
        for resolution in self.resolutions:
            logger.info("Executing Leiden with resolution %s", resolution)
            cmd = ["runleiden", "-i", self.config['inputfile'], "-r", resolution, "-o", self.output_file]
            run(cmd)
