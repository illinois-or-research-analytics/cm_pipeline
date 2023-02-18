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

FILTERING_OUTPUT_FILE_NAME = "S${stage_num}.1_${clustering_file}_treestarcounts.tsv"
CM_READY_OUTPUT_FILE_NAME = "S${stage_num}.2_${clustering_file}_cm_ready.tsv"

class FilteringBfCm(Stage):
    def __init__(self, config, network_name, output_dir, stage_num, prev_stages):
        super().__init__(config, network_name, output_dir, stage_num, prev_stages)
        self.cm_ready_filtered_files = OrderedDict()

    def get_clustering_input_files(self):
        try:
            
            if INPUT_CLUSTERING_FILE_DIR_KEY in self.config:
                # To do: make sure to get the resolution values for each specified file. Define the syntax in config file
                clustering_input_files = os.listdir(self.config[INPUT_CLUSTERING_FILE_DIR_KEY])
            elif CLUSTERING_SECTION in self.prev_stages:
                clustering_stage = self.prev_stages.get(CLUSTERING_SECTION)
                clustering_input_files = clustering_stage.clustering_output_files
            else:
                raise Exception(f"{INPUT_CLUSTERING_FILE_DIR_KEY} not specified in config file or Clustering stage failed to generate the files")
        
        except FileNotFoundError as e:
            error_msg = f"{INPUT_CLUSTERING_FILE_DIR_KEY} does not exist"
            raise FileNotFoundError(error_msg, e)
        return clustering_input_files

    def _get_output_file_name_from_template(self, template_str, clustering_file):
        template = Template(template_str)

        _, clustering_file_name = os.path.split(clustering_file)
        # remove the stage number from the clustering file name
        # e.g. S2_cit_patents_leiden.0.5.tsv
        clustering_file_name = re.split('S\d_', clustering_file_name)[1].split('.tsv')[0]

        output_file_name = template.substitute(clustering_file=clustering_file_name,
                                               stage_num = self.stage_num)
        return output_file_name

    def execute(self):
        logging.info("******** STARTED FILTERING BEFORE CM STAGE ********")
        clustering_files = self.get_clustering_input_files() 
        for resolution in clustering_files.keys():
            
            logger.info("Filtering to get clusters with N>10 and non-trees")
            # Step 1: takes a Leiden clustering output in tsv and returns an annotation of its clusters (those above size 10)
            clustering_file = clustering_files.get(resolution)
            filtering_op_file_name = self._get_output_file_name_from_template(FILTERING_OUTPUT_FILE_NAME,
                                                                              clustering_file)
            filtering_output_file =  os.path.join(self.output_dir, filtering_op_file_name)
            cmd = ["Rscript", 
                   self.config[FILTERING_SCRIPT_KEY], 
                   clustering_file, 
                   filtering_output_file
                   ] 
            run(cmd)

            # Step 2: takes the output of Step 1, selects non-tree clusters, 
            # and reduces the original Leiden clustering to non-tree clusters of size > 10
            logger.info("Making the filtered output file compatible with Connectivity modifier")
            cm_ready_output_file_name = self._get_output_file_name_from_template(CM_READY_OUTPUT_FILE_NAME,
                                                                                 clustering_file)
            cm_ready_output_file = os.path.join(self.output_dir, cm_ready_output_file_name)   
            self.cm_ready_filtered_files[resolution]= cm_ready_output_file
            
            cmd = ["Rscript", 
                   self.config[CM_READY_SCRIPT_KEY], 
                   filtering_output_file, 
                   cm_ready_output_file
                   ] 
            run(cmd)
            logging.info("******** FINISHED FILTERING BEFORE CM STAGE ********")