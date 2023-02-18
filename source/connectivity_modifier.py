import logging
import os
import json
from collections import OrderedDict
from source.stage import Stage
from source.cmd import run
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

CM_PREPROCESS_OP_FILE_NAME = "S${stage_num}.1_${network_name}_${algorithm}.${resolution}_preprocessed_cm.tsv"
CM_UNI_PREPROCESS_OP_FILE_NAME = "S${stage_num}.2_${network_name}_${algorithm}.${resolution}_preprocessed_cm_uni.tsv"
CM_FINAL_OP_FILE_NAME = "S${stage_num}.3_${network_name}_${algorithm}.${resolution}_cm_final.tsv"

class ConnectivityModifier(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        self.cm_output_files = OrderedDict()

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

    @timeit
    def execute(self):
        logging.info("******** STARTED CONNECTIVITY MODIFIER STAGE ********")
        cm_ready_input_files = self.get_cm_ready_input_files()
        cleaned_input_file = self._get_cleaned_input_file()

        for resolution in self.default_config.resolutions:
            # Step 1: CM
            logger.info("Running CM with %s for resolution %s", self.default_config.algorithm, resolution)
            cm_ready_input_file = cm_ready_input_files.get(resolution)
            cm_preprocess_op_file_name = self._get_output_file_name_from_template(CM_PREPROCESS_OP_FILE_NAME, resolution)
            cm_preprocess_output_file =  os.path.join(self.default_config.output_dir, cm_preprocess_op_file_name) 
            
            cmd = [
                   "cm",
                   "-i" ,
                   cleaned_input_file, 
                   "-c",
                   self.default_config.algorithm,
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
            cm_uni_preprocessed_op_file_name = self._get_output_file_name_from_template(CM_UNI_PREPROCESS_OP_FILE_NAME, resolution)
            cm_uni_preprocessed_op_file = os.path.join(self.default_config.output_dir, cm_uni_preprocessed_op_file_name)
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
            cm_uni_preprocessed_op_json_file = os.path.join(self.default_config.output_dir, cm_uni_preprocessed_op_json_file_name)
        
            cm_final_op_file_name = self._get_output_file_name_from_template(CM_FINAL_OP_FILE_NAME,resolution)
            cm_final_op_file = os.path.join(self.default_config.output_dir, cm_final_op_file_name)

            logger.info("Converting Json to tsv for resolution %s", resolution)
            
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