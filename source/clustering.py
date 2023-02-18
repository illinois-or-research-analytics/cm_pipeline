import logging
import os
from collections import OrderedDict
from source.stage import Stage
from source.cmd import run
from source.constants import *

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = "S${stage_num}_${network_name}_${algorithm}.${resolution}.tsv"

class Clustering(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        # list of clustering files for different resolutions
        self.clustering_output_files = OrderedDict()
    
    def _get_cleaned_input_file(self):
        """
        This function checks if the input file should be the output files from the previous stage
        unless specifed in the param.config file.
        """
        
        if CLEANED_INPUT_FILE_KEY in self.config:
            cleaned_input_file = self.config[CLEANED_INPUT_FILE_KEY]
        elif CLEANUP_SECTION in self.prev_stages:
            cleanup_stage = self.prev_stages.get(CLEANUP_SECTION)
            cleaned_input_file = cleanup_stage.cleaned_output_file
        else:
            raise Exception("Cleaned input file not found in config file was not generated in the cleanup stage")
        return cleaned_input_file

    def execute(self):
        logging.info("******** STARTED CLUSTERING STAGE ********")
        cleaned_input_file = self._get_cleaned_input_file()
        
        for resolution in self.default_config.resolutions:
            output_file = os.path.join(self.default_config.output_dir, 
                                        self._get_output_file_name_from_template(OUTPUT_FILE_NAME, resolution))
            self.clustering_output_files[resolution] = output_file
            logger.info("Running %s with resolution %s", self.default_config.algorithm, resolution)
            
            cmd = [self.config[CLUSTERING_SCRIPT_KEY], "-i", cleaned_input_file , "-r", resolution, "-o", output_file]
            run(cmd)
        logging.info("******** FINISHED CLUSTERING STAGE ********")
