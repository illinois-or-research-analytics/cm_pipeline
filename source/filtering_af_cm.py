import logging
import os
from collections import defaultdict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

FILTERING_AF_CM_OP_FILE_NAME = "S${stage_num}_${network_name}_${" \
                               "algorithm}.${resolution}_" \
                               "i${n_iter}_filtered_final.tsv"


class FilteringAfCm(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        self.cm_ready_filtered_files = defaultdict(lambda: defaultdict(str))

    def _get_cm_files(self):
        try:
            if INPUT_CM_FILE_DIR_KEY in self.config:
                # Todo: make sure to get the resolution values for each
                #  specified file. Define the syntax in config file
                cm_input_files = os.listdir(self.config[INPUT_CM_FILE_DIR_KEY])
            elif CONNECTIVITY_MODIFIER_SECTION in self.prev_stages:
                cm_stage = self.prev_stages.get(CONNECTIVITY_MODIFIER_SECTION)
                cm_input_files = cm_stage.cm_output_files
            else:
                raise Exception(
                    f"{INPUT_CM_FILE_DIR_KEY} not specified in config file "
                    f"or CM stage failed to generate the files"
                    )
        except FileNotFoundError as e:
            error_msg = f"{INPUT_CM_FILE_DIR_KEY} does not exist"
            raise FileNotFoundError(error_msg, e)
        return cm_input_files

    @timeit
    def execute(self):
        logging.info("******** STARTED POST CM FILTERING ********")
        cm_files = self._get_cm_files()
        for resolution in self.default_config.resolutions:
            for n_iter in self.default_config.n_iterations:
                logger.info(
                    "Filtering to get clusters with N>10 and "
                    "for resolution %s, n %s", resolution, n_iter
                    )
                # Step 1: takes a Leiden clustering output in tsv and returns an
                # annotation of its clusters (those above size 10)
                cm_file = cm_files.get(resolution).get(n_iter)
                filtering_op_file_name = self._get_output_file_name_from_template(
                    template_str=FILTERING_AF_CM_OP_FILE_NAME,
                    resolution=resolution,
                    n_iter=n_iter
                    )
                filtering_output_file = self._get_op_file_path_for_resolution(
                    resolution=resolution,
                    op_file_name=filtering_op_file_name,
                    n_iter=n_iter
                    )
                self.cm_ready_filtered_files[resolution][
                    n_iter] = filtering_output_file

                cmd = ["Rscript",
                       self.config[FILTERING_SCRIPT_KEY],
                       cm_file,
                       filtering_output_file
                       ]
                self.cmd_obj.run(cmd)

                # add the final filtered output file to files_to_analyse dict
                FilteringAfCm.files_to_analyse[RESOLUTION_KEY][resolution][
                    n_iter].append(
                    filtering_output_file
                    )
            logging.info("******** FINISHED POST CM FILTERING ********")
