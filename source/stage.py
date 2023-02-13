import os
import time
import logging
from source.cmd import run

logger = logging.getLogger(__name__)

class Stage(object):
    def __init__(self, config):
        self.config = dict(config)

    def execute(self):
        
        raise NotImplementedError("Implement the execute function in each subclass")

    def generate_metrics_report(self):
        
        pass 

class Cleanup(Stage):
    def __init__(self, config_params):
        super().__init__(config_params)
        # Todo: replace placeholder with a fixed output file name
        self.output_file = os.path.join(self.config['outputdir'], f"placeholder_{time.strftime('%Y%m%d-%H%M%S')}.tsv")

    def execute(self):
        logger.info("Removing duplicate rows, parallel edges, and self-loops")
        cmd = ["Rscript", self.config['script'], self.config['inputfile'], self.output_file ]
        run(cmd)

class Clustering(Stage):
    def __init__(self, config):
        super().__init__(config)
         # Todo: replace placeholder with a fixed output file name
        self.output_file = os.path.join(self.config['outputdir'], f"placeholder_{time.strftime('%Y%m%d-%H%M%S')}.tsv")
        self. resolutions = self.config['resolutions'].split(',')
    
    def execute(self):
        for resolution in self.resolutions:
            logger.info("Executing Leiden with resolution %s", resolution)
            cmd = ["run_leiden", "-i", self.config['inputfile'], "-r", resolution, "-o", self.output_file]
            run(cmd)