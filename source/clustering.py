import logging
import os
from collections import OrderedDict
from source.stage import Stage
from source.cleanup import Cleanup
from source.cmd import run
from source.constants import *
from string import Template

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = "S${stage_num}_${network_name}_${algorithm}.${resolution}.tsv"

class Clustering(Stage):
    def __init__(self, config, network_name, output_dir, stage_num,  prev_stages):
        super().__init__(config, network_name, output_dir, stage_num, prev_stages)
        self.resolutions = [resolution.strip() for resolution in self.config[RESOLUTION_KEY].split(',')]
        # list of clustering files for different resolutions
        self.clustering_output_files = OrderedDict()
        self.algorithm = self.config[ALGORITHM_KEY]
    
    def _get_output_file_name_from_template(self, template_str, resolution):
        template =  Template(template_str)
        output_file_name = template.substitute(network_name = self.network_name,
                                               algorithm = self.algorithm, 
                                               resolution=resolution,
                                               stage_num=self.stage_num)
        return output_file_name
    
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
        for resolution in self.resolutions:
            output_file = os.path.join(self.output_dir, 
                                        self._get_output_file_name_from_template(OUTPUT_FILE_NAME, resolution))
            self.clustering_output_files[resolution] = output_file
            logger.info("Executing Leiden with resolution %s", resolution)
            cmd = ["runleiden", "-i", cleaned_input_file , "-r", resolution, "-o", output_file]
            run(cmd)
        logging.info("******** FINISHED CLUSTERING STAGE ********")
