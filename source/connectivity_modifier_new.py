import logging
import os
import json
from collections import defaultdict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

CM_NEW_PREPROCESS_OP_FILE_NAME = "S${stage_num}.1_${network_name}_${" \
                                 "algorithm}.${resolution}_i${n_iter}_preprocessed_cm.tsv"
CM_NEW_FINAL_OP_FILE_NAME = "S${stage_num}.3_${network_name}_${algorithm}.${" \
                            "resolution}_i${n_iter}_after_cm.tsv"


# Todo: Create a parent ConnectivityModifier class to combine the common
#  functions
class ConnectivityModifierNew(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        self.cm_output_files = defaultdict(lambda: defaultdict(str))

    def _get_cm_ready_input_files(self):
        try:
            if CM_READY_FILES in self.default_config.existing_ip_dict:
                cm_ready_input_files = self.default_config.existing_ip_dict[
                    CM_READY_FILES]
            elif FILTERING_BF_CM_SECTION in self.prev_stages:
                filtering_stage = self.prev_stages.get(FILTERING_BF_CM_SECTION)
                cm_ready_input_files = filtering_stage.cm_ready_filtered_files
            else:
                raise Exception(
                    f"{CM_READY_FILES} not specified in {self.default_config.existing_ip_json}.json "
                    f"file or Filtering stage failed to generate the files"
                    )
        except KeyError as e:
            error_msg = f"{CM_READY_FILES} does not exist in json file"
            raise KeyError(error_msg, e)
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

    def _get_additional_args(self):
        cmd_args = []
        quiet = self.config.get(QUIET, "1")
        labelonly = self.config.get(LABELONLY, "1")
        nprocs = self.config.get(NPROCS, None)
        if quiet == "1":
            cmd_args.append(DOUBLE_HYP + QUIET)
        if labelonly == "1":
            cmd_args.append(DOUBLE_HYP + LABELONLY)
        if nprocs:
            cmd_args.extend([DOUBLE_HYP + NPROCS, nprocs])
        return cmd_args

    @timeit
    def execute(self):
        logging.info(
            "******** STARTED NEW CONNECTIVITY MODIFIER STAGE ********"
            )
        cm_ready_input_files = self._get_cm_ready_input_files()
        cleaned_input_file = self._get_cleaned_input_file()

        for resolution in self.default_config.resolutions:
            for n_iter in self.default_config.n_iterations:
                # Step 1: CM & CM Universal combined
                logger.info(
                    "Running CM with %s for resolution=%s, n=%s",
                    self.default_config.algorithm, resolution, n_iter
                    )
                cm_ready_input_file = cm_ready_input_files.get(resolution).get(
                    n_iter
                    )
                cm_nw_preprocess_op_file_name = self._get_output_file_name_from_template(
                    template_str=CM_NEW_PREPROCESS_OP_FILE_NAME,
                    resolution=resolution,
                    n_iter=n_iter
                    )
                cm_nw_preprocess_output_file = self._get_op_file_path_for_resolution(
                    resolution=resolution,
                    op_file_name=cm_nw_preprocess_op_file_name,
                    n_iter=n_iter
                    )
                # Todo: Comment the --quiet argument to run cm in verbose mode:wq
                cmd = [
                    "python",
                    "./hm01/cm.py",
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
                    cm_nw_preprocess_output_file
                    ]
                # quiet, nprocs, logtree node
                cmd.extend(self._get_additional_args())
                self.cmd_obj.run(cmd)
                # Step 2: json2membership
                cm_nw_preprocessed_op_json_file_name = f"{cm_nw_preprocess_output_file}.after.json"
                cm_nw_preprocessed_op_json_file = self._get_op_file_path_for_resolution(
                    resolution=resolution,
                    op_file_name=cm_nw_preprocessed_op_json_file_name,
                    n_iter=n_iter
                    )

                cm_final_op_file_name = self._get_output_file_name_from_template(
                    template_str=CM_NEW_FINAL_OP_FILE_NAME,
                    resolution=resolution,
                    n_iter=n_iter
                    )
                cm_nw_final_op_file = self._get_op_file_path_for_resolution(
                    resolution=resolution,
                    op_file_name=cm_final_op_file_name,
                    n_iter=n_iter
                    )

                logger.info(
                    "Converting Json to tsv for resolution %s", resolution
                    )
                self.cm_output_files[resolution][n_iter] = cm_nw_final_op_file

                # Comment the below line for quick testing of workflow paths
                self._gen_cm_final_tsv_from_json(
                    cm_nw_preprocessed_op_json_file, cm_nw_final_op_file
                    )

                # add the cm final output file to files_to_analyse dict
                ConnectivityModifierNew.files_to_analyse[RESOLUTION_KEY][
                    resolution][n_iter].append(cm_nw_final_op_file)

        logging.info(
            "******** FINISHED NEW CONNECTIVITY MODIFIER STAGE ********"
            )
