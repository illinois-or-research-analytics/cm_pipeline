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

    def _get_clustering_script(self):
        clustering_script_name = self.config.get(
            CLUSTERING_SCRIPT_KEY,
            LEIDEN_ALG_SCRIPT_VALUE
            )
        if clustering_script_name == RUNLEIDEN_SCRIPT_VALUE:
            clustering_script = ["runleiden"]
        elif clustering_script_name == LEIDEN_ALG_SCRIPT_VALUE:
            clustering_script = ["python", "./scripts/run_leiden.py"]
        return clustering_script

    def _get_n_iteration(self):
        n_iteration = []
        clustering_script_name = self.config.get(
            CLUSTERING_SCRIPT_KEY,
            LEIDEN_ALG_SCRIPT_VALUE
            )
        if clustering_script_name == LEIDEN_ALG_SCRIPT_VALUE:
            n_iteration = ["-n", self.config.get(NUMBER_OF_ITERATIONS_KEY, 2)]
        return n_iteration

    @timeit
    def execute(self):
        logging.info("******** STARTED CLUSTERING STAGE ********")
        cleaned_input_file = self._get_cleaned_input_file()
        clustering_script = self._get_clustering_script()
        n_iterations = self._get_n_iteration()

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

            script_args = [
                "-i",
                cleaned_input_file,
                "-r",
                resolution,
                "-o",
                output_file
                ]
            cmd = clustering_script + script_args + n_iterations
            self.cmd_obj.run(cmd)

            # add the clustering output file to files_to_analyse dict
            Clustering.files_to_analyse[RESOLUTION_KEY][resolution].append(
                output_file
                )
        logging.info("******** FINISHED CLUSTERING STAGE ********")
