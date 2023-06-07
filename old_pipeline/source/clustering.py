import logging
from collections import defaultdict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = "S${stage_num}_${network_name}_${algorithm}.${" \
                   "resolution}_i${n_iter}.tsv"


class Clustering(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
        # list of clustering files for different resolutions
        self.clustering_output_files = defaultdict(lambda: defaultdict(str))

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

    @timeit
    def execute(self):
        logging.info("******** STARTED CLUSTERING STAGE ********")
        cleaned_input_file = self._get_cleaned_input_file()
        clustering_script = self._get_clustering_script()

        for resolution in self.default_config.resolutions:
            for n_iter in self.default_config.n_iterations:
                op_file_name = self._get_output_file_name_from_template(
                    template_str=OUTPUT_FILE_NAME,
                    resolution=resolution,
                    n_iter=n_iter
                    )
                output_file = self._get_op_file_path_for_resolution(
                    resolution=resolution,
                    op_file_name=op_file_name,
                    n_iter=n_iter
                    )

                self.clustering_output_files[resolution][n_iter] = output_file
                logger.info(
                    "Running %s with resolution=%s,n=%s",
                    self.default_config.algorithm,
                    resolution, n_iter
                    )

                script_args = [
                    "-i",
                    cleaned_input_file,
                    "-r",
                    resolution,
                    "-o",
                    output_file
                    ]
                cmd = clustering_script + script_args + ["-n", n_iter]
                self.cmd_obj.run(cmd)

                # add the clustering output file to files_to_analyse dict
                Clustering.files_to_analyse[RESOLUTION_KEY][resolution][
                    n_iter].append(output_file)
            logging.info("******** FINISHED CLUSTERING STAGE ********")
