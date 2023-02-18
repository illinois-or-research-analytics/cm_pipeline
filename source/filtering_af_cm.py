import logging
import os
from collections import OrderedDict
from source.stage import Stage
from source.cmd import run
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

FILTERING_AF_CM_OP_FILE_NAME = "S${stage_num}.1_${network_name}_${algorithm}.${resolution}_treestarcounts.tsv"
FINAL_OUTPUT_FILE_NAME = "S${stage_num}.2_${network_name}_${algorithm}.${resolution}_final.tsv"


class FilteringAfCm(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        self.cm_ready_filtered_files = OrderedDict()

    def _get_cm_files(self):
        try:
            
            if INPUT_CM_FILE_DIR_KEY in self.config:
                # To do: make sure to get the resolution values for each specified file. Define the syntax in config file
                cm_input_files = os.listdir(self.config[INPUT_CM_FILE_DIR_KEY])
            elif CONNECTIVITY_MODIFIER_SECTION in self.prev_stages:
                cm_stage = self.prev_stages.get(CONNECTIVITY_MODIFIER_SECTION)
                cm_input_files = cm_stage.cm_output_files
            else:
                raise Exception(f"{INPUT_CM_FILE_DIR_KEY} not specified in config file or CM stage failed to generate the files")
        
        except FileNotFoundError as e:
            error_msg = f"{INPUT_CM_FILE_DIR_KEY} does not exist"
            raise FileNotFoundError(error_msg, e)
        return cm_input_files

    @timeit
    def execute(self):
        logging.info("******** STARTED FILTERING AFTER CM STAGE ********")
        cm_files = self._get_cm_files()
        cleaned_input_file = self._get_cleaned_input_file()
        
        for resolution in self.default_config.resolutions:
            
            logger.info("Filtering to get clusters with N>10 and non-trees for resolution %s", resolution)
            # Step 1: takes a Leiden clustering output in tsv and returns an annotation of its clusters (those above size 10)
            cm_file = cm_files.get(resolution)
            filtering_op_file_name = self._get_output_file_name_from_template(FILTERING_AF_CM_OP_FILE_NAME,
                                                                              resolution)
            filtering_output_file =  os.path.join(self.default_config.output_dir, filtering_op_file_name)
            
            cmd = ["Rscript", 
                   self.config[FILTERING_SCRIPT_KEY], 
                   cleaned_input_file,
                   cm_file, 
                   filtering_output_file
                   ] 
            run(cmd)

            # Step 2: takes the output of Step 1, selects non-tree clusters, 
            # and reduces the original Leiden clustering to non-tree clusters of size > 10
            logger.info("Making the filtered output file to have node id and cluster id columns for %s", resolution)
            final_output_file_name = self._get_output_file_name_from_template(FINAL_OUTPUT_FILE_NAME, resolution)
            final_output_file = os.path.join(self.default_config.output_dir, final_output_file_name)   
            self.cm_ready_filtered_files[resolution] = final_output_file
            
            cmd = ["Rscript", 
                   self.config[CM_READY_SCRIPT_KEY],
                   cleaned_input_file, 
                   filtering_output_file, 
                   final_output_file
                   ] 
            run(cmd)
            logging.info("******** FINISHED FILTERING AFTER CM STAGE ********")