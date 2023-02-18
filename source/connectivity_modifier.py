import logging
import os
import re
import json
from collections import OrderedDict
from source.stage import Stage
from source.cmd import run
from source.constants import *
from string import Template

logger = logging.getLogger(__name__)

CM_PREPROCESS_OP_FILE_NAME = "S${stage_num}.1_${network_name}_${algorithm}.${resolution}_preprocessed_cm.tsv"
CM_UNI_PREPROCESS_OP_FILE_NAME = "S${stage_num}.2_${network_name}_${algorithm}.${resolution}_preprocessed_cm_uni.tsv"
CM_FINAL_OP_FILE_NAME = "S${stage_num}.3_${network_name}_${algorithm}.${resolution}_cm_final.tsv"

class ConnectivityModifier(Stage):
    def __init__(self, config, network_name, output_dir, stage_num, prev_stages):
        super().__init__(config, network_name, output_dir, stage_num, prev_stages)
        self.cm_output_files = OrderedDict()
        self.clustering_algorithm = self._get_clustering_algorithm()

    def get_cm_ready_input_files(self):
        try:
            if INPUT_CM_READY_FILE_DIR_KEY in self.config:
                cm_ready_input_files = os.listdir(self.config[INPUT_CM_READY_FILE_DIR_KEY])
            elif FILTERING_BF_CM_SECTION in self.prev_stages:
                filtering_stage = self.prev_stages.get(FILTERING_BF_CM_SECTION)
                cm_ready_input_files = filtering_stage.cm_ready_filtered_files
            else:
                raise Exception(f"{INPUT_CM_READY_FILE_DIR_KEY} not specified in config file or Filtering stage failed to generate the files")
        
        except FileNotFoundError as e:
            error_msg = f"{INPUT_CM_READY_FILE_DIR_KEY} does not exist"
            raise FileNotFoundError(error_msg, e)
        return cm_ready_input_files

    # def _get_output_file_name_from_template(self, template_str, clustering_file):
    #     template = Template(template_str)

    #     _, clustering_file_name = os.path.split(clustering_file)
    #     # remove the stage number from the clustering file name
    #     # e.g. S2_cit_patents_leiden.0.5.tsv
    #     filtering_file_name = re.split('S\d_', clustering_file_name)[1].split('.tsv')[0]

    #     output_file_name = template.substitute(clustering_file_name=clustering_file_name,
    #                                            stage_num = self.stage_num)
    #     return output_file_name

    def _get_output_file_name_from_template(self, template_str, resolution):
        template =  Template(template_str)
        output_file_name = template.substitute(network_name = self.network_name,
                                               algorithm = self.clustering_algorithm, 
                                               resolution=resolution,
                                               stage_num=self.stage_num)
        return output_file_name

    def _get_cleaned_input_file(self):
        if CLEANED_INPUT_FILE_KEY in self.config:
            cleaned_input_file = self.config[CLEANED_INPUT_FILE_KEY]
        elif CLEANUP_SECTION in self.prev_stages:
            cleanup_stage = self.prev_stages[CLEANUP_SECTION]
            cleaned_input_file = cleanup_stage.cleaned_output_file
        else:
            raise Exception(f"{CLEANED_INPUT_FILE_KEY} not specified in config file or Cleanup stage failed to generate the cleaned file")
        return cleaned_input_file
    
    def _get_clustering_algorithm(self):
        if CLUSTERING_ALGORITHM_KEY in self.config:
            clustering_algorithm = self.config[CLUSTERING_ALGORITHM_KEY]
        elif CLUSTERING_SECTION in self.prev_stages:
            clustering_stage = self.prev_stages[CLUSTERING_SECTION]
            clustering_algorithm = clustering_stage.algorithm
        else:
            raise Exception(f"{CLUSTERING_ALGORITHM_KEY} not specified in config file or Clustering stage has no attribute called algorithm")
        return clustering_algorithm

    def execute(self):
        logging.info("******** STARTED CONNECTIVITY MODIFIER STAGE ********")
        cm_ready_input_files = self.get_cm_ready_input_files()
       
        for resolution in cm_ready_input_files.keys():
            logger.info("Running CM for resolution %s", resolution)
            
            # Step 1: CM
            cm_ready_input_file = cm_ready_input_files.get(resolution)
            cm_preprocess_op_file_name = self._get_output_file_name_from_template(CM_PREPROCESS_OP_FILE_NAME, resolution)
            cm_preprocess_output_file =  os.path.join(self.output_dir, cm_preprocess_op_file_name)
            cleaned_input_file = self._get_cleaned_input_file()
            
            cmd = [
                   "cm",
                   "-i" ,
                   cleaned_input_file, 
                   "-c",
                   self.clustering_algorithm,
                   "-g",
                   resolution,
                   "-t",
                   self.config[THRESHOLD_KEY],
                   "-e",
                   cm_ready_input_file,
                   "-o",
                   cm_preprocess_output_file
                   ] 
            run(cmd)

            # Step 2: CM Universal
            logger.info("Running CM Universal for resolution %s", resolution)
            cm_uni_preprocessed_op_file_name = self._get_output_file_name_from_template(CM_UNI_PREPROCESS_OP_FILE_NAME,
                                                                                        resolution)
            cm_uni_preprocessed_op_file = os.path.join(self.output_dir, cm_uni_preprocessed_op_file_name)
            cmd = [
                    "cm2universal",
                    "-g",
                    cleaned_input_file,
                    "-i",
                    cm_preprocess_output_file,
                    "-o",
                    cm_uni_preprocessed_op_file
                   ] 
            run(cmd)

            # Step 3: json2membership
            cm_uni_preprocessed_op_json_file_name = f"{cm_uni_preprocessed_op_file_name}.after.json"
            cm_uni_preprocessed_op_json_file = os.path.join(self.output_dir, cm_uni_preprocessed_op_json_file_name)
            cm_final_op_file_name = self._get_output_file_name_from_template(CM_FINAL_OP_FILE_NAME,
                                                                             resolution)
            cm_final_op_file = os.path.join(self.output_dir, cm_final_op_file_name)
            self.cm_output_files[resolution] = cm_final_op_file

            # Todo: Move this to a function
            try:
                with open(cm_uni_preprocessed_op_json_file, 'r') as f:
                    with open(cm_final_op_file, 'w+') as g:
                        for line in f:
                            cluster = json.loads(line)
                            label = cluster["label"]
                            for node in cluster["nodes"]:
                                g.write(f"{node}\t{label}\n")
                self.cm_output_files[resolution] = cm_final_op_file
            except FileNotFoundError:
                raise Exception("%s output file from cm universal not found", cm_uni_preprocessed_op_json_file)

        logging.info("******** FINISHED CONNECTIVITY MODIFIER STAGE ********")