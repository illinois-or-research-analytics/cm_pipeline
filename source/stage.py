import os
from collections import OrderedDict, defaultdict
from string import Template
from source.constants import *
from source.cmd import Cmd


class Stage(object):
    """
    This is a class variable and hence all the instances will have access
     files_to_analyse = {
                         'cleaned_ip_file': 'S1_cit_patents_cleaned.tsv',
                         '0.1': [],
                         '0.5': []
                         }
    """
    files_to_analyse = {
            CLEANED_INPUT_FILE_KEY: "",
            RESOLUTION_KEY: defaultdict(lambda: defaultdict(list))
        }

    def __init__(
            self, config, default_config, stage_num, prev_stages=None
            ):
        if prev_stages is None:
            prev_stages = OrderedDict()

        self.config = dict(config)
        self.default_config = default_config
        self.stage_num = stage_num
        self.prev_stages = prev_stages
        self._check_paths()
        self.cmd_obj = Cmd(default_config)
        self.files_to_analyse = OrderedDict()

    def execute(self):
        raise NotImplementedError(
            "Implement the execute function in each subclass"
            )

    def _get_output_file_name_from_template(self, template_str, resolution,
                                            n_iter):
        template = Template(template_str)
        output_file_name = template.substitute(
            network_name=self.default_config.network_name,
            algorithm=self.default_config.algorithm,
            resolution=resolution,
            stage_num=self.stage_num,
            n_iter=n_iter
            )
        return output_file_name

    def _get_cleaned_input_file(self):
        """
        This function checks if the input file should be the output files from
        the previous stage unless specified in the param.config file.
        """

        if CLEANED_INPUT_FILE_KEY in self.config:
            cleaned_input_file = self.config[CLEANED_INPUT_FILE_KEY]
        elif CLEANUP_SECTION in self.prev_stages:
            cleanup_stage = self.prev_stages.get(CLEANUP_SECTION)
            cleaned_input_file = cleanup_stage.cleaned_output_file
        else:
            raise Exception(
                "Cleaned input file not found in config file was not "
                "generated in the cleanup stage"
                )
        return cleaned_input_file

    def generate_metrics_report(self):

        pass

    def _check_paths(self):
        """
        1. Checks the input and output paths for ~ in the paths and replace
        it with user home directory.
        """
        # default dir
        self.default_config.output_dir = os.path.expanduser(
            self.default_config.output_dir
            )
        os.makedirs(self.default_config.output_dir, exist_ok=True)

        # other paths in config file
        path_keys = [INPUT_FILE_KEY,
                     CLUSTERING_SCRIPT_KEY,
                     CLEANUP_SCRIPT_KEY,
                     CLUSTERING_FILE_KEY,
                     INPUT_CLUSTERING_FILE_DIR_KEY,
                     CLEANED_INPUT_FILE_KEY,
                     FILTERING_SCRIPT_KEY]
        for key in path_keys:
            if key in self.config:
                self.config[key] = os.path.expanduser(self.config[key])

    def _get_op_file_path_for_resolution(self, resolution, op_file_name, n_iter):
        op_folder_name = f'res-{resolution}-n-{n_iter}'
        op_folder = os.path.join(
            self.default_config.output_dir, op_folder_name
            )
        os.makedirs(op_folder, exist_ok=True)
        op_file_name = os.path.join(op_folder, op_file_name)
        return op_file_name
