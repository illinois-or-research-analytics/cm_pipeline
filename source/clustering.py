import logging
from collections import OrderedDict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = "S${stage_num}_${network_name}_${algorithm}.${" \
                   "resolution}.tsv"


class Clustering(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        # list of clustering files for different resolutions
        self.clustering_output_files = OrderedDict()

    @timeit
    def execute(self):
        logging.info("******** STARTED CLUSTERING STAGE ********")
        cleaned_input_file = self._get_cleaned_input_file()

        for resolution in self.default_config.resolutions:
            op_file_name = self._get_output_file_name_from_template(
                OUTPUT_FILE_NAME, resolution
                )
            output_file = self._get_op_file_path_for_resolution(
                resolution, op_file_name
                )

            self.clustering_output_files[resolution] = output_file
            logger.info(
                "Running %s with resolution %s", self.default_config.algorithm,
                resolution
                )

            cmd = [self.config[CLUSTERING_SCRIPT_KEY], "-i",
                   cleaned_input_file, "-r", resolution, "-o", output_file]
            self.cmd_obj.run(cmd)
        logging.info("******** FINISHED CLUSTERING STAGE ********")
