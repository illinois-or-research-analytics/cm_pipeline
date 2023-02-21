import logging
import os
import json
from collections import OrderedDict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

CM_PREPROCESS_OP_FILE_NAME = "S${stage_num}.1_${network_name}_${" \
                             "algorithm}.${resolution}_preprocessed_cm.tsv"
CM_UNI_PREPROCESS_OP_FILE_NAME = "S${stage_num}.2_${network_name}_${" \
                                 "algorithm}.${" \
                                 "resolution}_preprocessed_cm_uni.tsv"
CM_FINAL_OP_FILE_NAME = "S${stage_num}.3_${network_name}_${algorithm}.${" \
                        "resolution}_after_cm.tsv"


class ConnectivityModifier(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        self.cm_output_files = OrderedDict()

    def _get_cm_ready_input_files(self):
        try:
            if INPUT_CM_READY_FILE_DIR_KEY in self.config:
                cm_ready_input_files = os.listdir(
                    self.config[INPUT_CM_READY_FILE_DIR_KEY]
                    )
            elif FILTERING_BF_CM_SECTION in self.prev_stages:
                filtering_stage = self.prev_stages.get(FILTERING_BF_CM_SECTION)
                cm_ready_input_files = filtering_stage.cm_ready_filtered_files
            else:
                raise Exception(
                    f"{INPUT_CM_READY_FILE_DIR_KEY} not specified in config "
                    f"file or Filtering stage failed to generate the files"
                    )

        except FileNotFoundError as e:
            error_msg = f"{INPUT_CM_READY_FILE_DIR_KEY} does not exist"
            raise FileNotFoundError(error_msg, e)
        return cm_ready_input_files

    @staticmethod
    def _gen_cm_final_tsv_from_json(
            cm_uni_preprocessed_op_json_file, cm_final_op_file
            ):
        try:
            with open(cm_uni_preprocessed_op_json_file, 'r') as f:
                with open(cm_final_op_file, 'w+') as g:
                    for line in f:
                        cluster = json.loads(line)
                        label = cluster["label"]
                        for node in cluster["nodes"]:
                            g.write(f"{node}\t{label}\n")
        except FileNotFoundError:
            raise Exception(
                "%s output file from cm universal not found",
                cm_uni_preprocessed_op_json_file
                )

    @timeit
    def execute(self):
        logging.info("******** STARTED CONNECTIVITY MODIFIER STAGE ********")
        cm_ready_input_files = self._get_cm_ready_input_files()
        cleaned_input_file = self._get_cleaned_input_file()

        for resolution in self.default_config.resolutions:
            # Step 1: CM
            logger.info(
                "Running CM with %s for resolution %s",
                self.default_config.algorithm, resolution
                )
            cm_ready_input_file = cm_ready_input_files.get(resolution)
            cm_preprocess_op_file_name = self._get_output_file_name_from_template(
                CM_PREPROCESS_OP_FILE_NAME, resolution
                )
            cm_preprocess_output_file = self._get_op_file_path_for_resolution(
                resolution, cm_preprocess_op_file_name
                )

            cmd = [
                "cm",
                "-i",
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
            self.cmd_obj.run(cmd)

            # Step 2: CM Universal
            logger.info("Running CM Universal for resolution %s", resolution)

            cm_uni_preprocessed_op_file_name = self._get_output_file_name_from_template(
                CM_UNI_PREPROCESS_OP_FILE_NAME, resolution
                )
            cm_uni_preprocessed_op_file = self._get_op_file_path_for_resolution(
                resolution, cm_uni_preprocessed_op_file_name
                )

            cmd = [
                "cm2universal",
                "-g",
                cleaned_input_file,
                "-i",
                cm_preprocess_output_file,
                "-o",
                cm_uni_preprocessed_op_file
                ]
            self.cmd_obj.run(cmd)

            # Step 3: json2membership
            cm_uni_preprocessed_op_json_file_name = f"{cm_uni_preprocessed_op_file_name}.after.json"
            cm_uni_preprocessed_op_json_file = self._get_op_file_path_for_resolution(
                resolution, cm_uni_preprocessed_op_json_file_name
                )

            cm_final_op_file_name = self._get_output_file_name_from_template(
                CM_FINAL_OP_FILE_NAME, resolution
                )
            cm_final_op_file = self._get_op_file_path_for_resolution(
                resolution, cm_final_op_file_name
                )

            logger.info("Converting Json to tsv for resolution %s", resolution)
            self.cm_output_files[resolution] = cm_final_op_file

            # Comment the below line for quick testing of workflow paths
            self._gen_cm_final_tsv_from_json(
                cm_uni_preprocessed_op_json_file, cm_final_op_file
                )

        logging.info("******** FINISHED CONNECTIVITY MODIFIER STAGE ********")
