import logging
import os
from collections import defaultdict
from source.stage import Stage
from source.timeit import timeit
from source.constants import *

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = "S${stage_num}_${network_name}_${algorithm}.${" \
                   "resolution}_i${n_iter}.tsv"


class Stats(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)
    
    @timeit
    def execute(self):
        logging.info("******** STARTED POST FILTERING STATS ********")
        cleaned_input_file = self._get_cleaned_input_file()

        for resolution in self.default_config.resolutions:
            for n_iter in self.default_config.n_iterations:
                logger.info(
                    "Reporting stats "
                    "for resolution %s, n %s", resolution, n_iter
                    )

                filtering_op_file_name = self._get_output_file_name_from_template_prev(
                    template_str=self.config[TEMPLATE_STR],
                    resolution=resolution,
                    n_iter=n_iter
                    )
                filtering_output_file = self._get_op_file_path_for_resolution(
                    resolution=resolution,
                    op_file_name=filtering_op_file_name,
                    n_iter=n_iter
                    )
                
                cmd = ["python3",
                       self.config[STATS_SCRIPT],
                       "-i",
                       cleaned_input_file,
                       "-c",
                       self.default_config.algorithm,
                       "-g",
                       resolution,
                       "-e",
                       filtering_output_file
                       ]
                self.cmd_obj.run(cmd)
        
        logging.info(
            "******** FINISHED POST FILTERING STATS STAGE ********"
            )