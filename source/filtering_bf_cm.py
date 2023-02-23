import logging
import os
from collections import OrderedDict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

FILTERING_OUTPUT_FILE_NAME = "S${stage_num}.1_${network_name}_${" \
                             "algorithm}.${resolution}_treestarcounts.tsv"
CM_READY_OUTPUT_FILE_NAME = "S${stage_num}.2_cm_ready_${network_name}_" \
                            "${algorithm}.${resolution}_nontree_n10.tsv"


class FilteringBfCm(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        self.cm_ready_filtered_files = OrderedDict()

    def get_clustering_input_files(self):
        try:
            if INPUT_CLUSTERING_FILE_DIR_KEY in self.config:
                # Todo: make sure to get the resolution values for each
                #  specified file. Define the syntax in config file
                clustering_input_files = os.listdir(
                    self.config[INPUT_CLUSTERING_FILE_DIR_KEY]
                    )
            elif CLUSTERING_SECTION in self.prev_stages:
                clustering_stage = self.prev_stages.get(CLUSTERING_SECTION)
                clustering_input_files = clustering_stage.clustering_output_files
            else:
                raise Exception(
                    f"{INPUT_CLUSTERING_FILE_DIR_KEY} not specified in config "
                    f"file or Clustering stage failed to generate the files"
                    )
        except FileNotFoundError as e:
            error_msg = f"{INPUT_CLUSTERING_FILE_DIR_KEY} does not exist"
            raise FileNotFoundError(error_msg, e)
        return clustering_input_files

    @timeit
    def execute(self):
        logging.info("******** STARTED FILTERING BEFORE CM STAGE ********")
        clustering_files = self.get_clustering_input_files()
        cleaned_input_file = self._get_cleaned_input_file()

        for resolution in self.default_config.resolutions:
            logger.info(
                "Filtering to get clusters with N>10 "
                "and non-trees for resolution %s",
                resolution
                )
            # Step 1: takes a Leiden clustering output in tsv and
            # returns an annotation of its clusters (those above size 10)
            clustering_file = clustering_files.get(resolution)
            filtering_op_file_name = self._get_output_file_name_from_template(
                FILTERING_OUTPUT_FILE_NAME, resolution
                )
            filtering_output_file = self._get_op_file_path_for_resolution(
                resolution, filtering_op_file_name
                )

            cmd = ["Rscript",
                   self.config[FILTERING_SCRIPT_KEY],
                   cleaned_input_file,
                   clustering_file,
                   filtering_output_file
                   ]
            self.cmd_obj.run(cmd)

            # Step 2: takes the output of Step 1, selects non-tree clusters, 
            # and reduces the original Leiden clustering to
            # non-tree clusters of size > 10
            logger.info(
                "Making the filtered output file compatible "
                "with Connectivity modifier for %s",
                resolution
                )

            cm_ready_op_file_name = self._get_output_file_name_from_template(
                CM_READY_OUTPUT_FILE_NAME, resolution
                )
            cm_ready_output_file = self._get_op_file_path_for_resolution(
                resolution, cm_ready_op_file_name
                )
            self.cm_ready_filtered_files[resolution] = cm_ready_output_file

            cmd = ["Rscript",
                   self.config[CM_READY_SCRIPT_KEY],
                   clustering_file,
                   filtering_output_file,
                   cm_ready_output_file
                   ]
            self.cmd_obj.run(cmd)

            # add the cm_ready output file to files_to_analyse dict
            FilteringBfCm.files_to_analyse[RESOLUTION_KEY][resolution].append(
                cm_ready_output_file
                )
            logging.info(
                "******** FINISHED FILTERING BEFORE CM STAGE ********"
                )
