import logging
import os
from source.stage import Stage
from source.constants import *
from string import Template
from source.timeit import timeit

logger = logging.getLogger(__name__)

OUTPUT_FILE_NAME = 'S${stage_num}_${network_name}_cleaned.tsv'


class Cleanup(Stage):
    def __init__(self, config, default_config, stage_num, prev_stages):
        super().__init__(config, default_config, stage_num, prev_stages)

        self.cleaned_output_file = os.path.join(
            self.default_config.output_dir,
            self._get_output_file_name_from_template(OUTPUT_FILE_NAME)
            )
        Cleanup.files_to_analyse[
            CLEANED_INPUT_FILE_KEY] = self.cleaned_output_file

    def _get_output_file_name_from_template(
            self, template_str, resolution=None
            ):
        template = Template(template_str)
        output_file_name = template.substitute(
            network_name=self.default_config.network_name,
            stage_num=self.stage_num
            )
        return output_file_name

    @timeit
    def execute(self):
        logging.info("******** STARTED CLEANUP STAGE ********")
        logger.debug("Removing duplicate rows, parallel edges, and self-loops")
        cmd = ["Rscript", self.config[CLEANUP_SCRIPT_KEY],
               self.config[INPUT_FILE_KEY], self.cleaned_output_file]
        self.cmd_obj.run(cmd)
        logging.info("******** FINISHED CLEANUP STAGE ********")
