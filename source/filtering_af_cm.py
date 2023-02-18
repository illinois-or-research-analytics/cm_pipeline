import logging
import os
import re
from collections import OrderedDict
from source.clustering import Clustering
from source.stage import Stage
from source.cmd import run
from source.constants import *
from string import Template

logger = logging.getLogger(__name__)

FILTERING_AF_CM_OP_FILE_NAME = "S${stage_num}.1_${network_name}_${algorithm}.${resolution}_treestarcounts.tsv"
FINAL_OUTPUT_FILE_NAME = "S${stage_num}.2_${network_name}_${algorithm}.${resolution}_final.tsv"


class FilteringAfCm(Stage):
    def __init__(self, config, network_name, output_dir, stage_num, prev_stages):
        super().__init__(config, network_name, output_dir, stage_num, prev_stages)
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

    def _get_cm_algorithm(self):
        if CM_ALGORITHM_KEY in self.config:
            cm_algorithm = self.config[CLUSTERING_ALGORITHM_KEY]
        elif CONNECTIVITY_MODIFIER_SECTION in self.prev_stages:
            cm_stage = self.prev_stages[CONNECTIVITY_MODIFIER_SECTION]
            cm_algorithm = cm_stage.clustering_algorithm
        else:
            raise Exception(f"{CM_ALGORITHM_KEY} not specified in config file or CM stage has no attribute called clustering_algorithm")
        return cm_algorithm

    def _get_output_file_name_from_template(self, template_str, resolution):
        template =  Template(template_str)
        output_file_name = template.substitute(network_name = self.network_name,
                                               algorithm = self._get_cm_algorithm(), 
                                               resolution=resolution,
                                               stage_num=self.stage_num)
        return output_file_name

    def execute(self):
        logging.info("******** STARTED FILTERING AFTER CM STAGE ********")
        cm_files = self._get_cm_files()
        for resolution in cm_files.keys():
            
            logger.info("Filtering to get clusters with N>10 and non-trees")
            # Step 1: takes a Leiden clustering output in tsv and returns an annotation of its clusters (those above size 10)
            cm_file = cm_files.get(resolution)
            filtering_op_file_name = self._get_output_file_name_from_template(FILTERING_AF_CM_OP_FILE_NAME,
                                                                              resolution)
            filtering_output_file =  os.path.join(self.output_dir, filtering_op_file_name)
            cmd = ["Rscript", 
                   self.config[FILTERING_SCRIPT_KEY], 
                   cm_file, 
                   filtering_output_file
                   ] 
            run(cmd)

            # Step 2: takes the output of Step 1, selects non-tree clusters, 
            # and reduces the original Leiden clustering to non-tree clusters of size > 10
            logger.info("Making the filtered output file to have node id and cluster id columns")
            final_output_file_name = self._get_output_file_name_from_template(FINAL_OUTPUT_FILE_NAME,
                                                                                 resolution)
            final_output_file = os.path.join(self.output_dir, final_output_file_name)   
            self.cm_ready_filtered_files[resolution]= final_output_file
            
            cmd = ["Rscript", 
                   self.config[CM_READY_SCRIPT_KEY], 
                   filtering_output_file, 
                   final_output_file
                   ] 
            run(cmd)
            logging.info("******** FINISHED FILTERING AFTER CM STAGE ********")