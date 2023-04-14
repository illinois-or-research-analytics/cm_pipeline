import os
import json
from source.constants import *
from datetime import datetime


class DefaultConfig(object):
    def __init__(self, default_section):
        try:
            self.network_name = default_section[NETWORK_NAME_KEY]
            self.root_output_dir = os.path.expanduser(
                default_section[OUTPUT_DIR_KEY]
                )
            self.algorithm = default_section[ALGORITHM_KEY]
            self.resolutions = [resolution.strip() for resolution in
                                default_section[RESOLUTION_KEY].split(',')]
            self.n_iterations = [n_iteration.strip() for n_iteration in
                                 default_section[
                                     NUMBER_OF_ITERATIONS_KEY].split(',')]
            self.cm_version = default_section[CM_VERSION_KEY]
            self.timestamp = datetime.now().strftime("%Y%m%d-%H:%M:%S")
            self.output_dir = self._create_output_dir_with_time_stamp()
            self.execution_info_csv = os.path.join(
                self.output_dir, 'execution_time.csv'
                )
            self.existing_ip_json = default_section.get(EXISTING_OP_JSON, {})
            self.existing_ip_dict = self.get_existing_op_file_paths()
        except KeyError:
            raise Exception(
                "default section with network name "
                "output directory/ algorithm /resolutions "
                "is missing / misspelled in the config file."
                )

    def get_existing_op_file_paths(self):
        existing_ip_dict = {}
        if self.existing_ip_json:
            with open(self.existing_ip_json, 'r') as fp:
                existing_ip_dict = json.load(fp)
            self._validate_config(existing_ip_dict)
        return existing_ip_dict

    def _validate_config(self, existing_ip_dict):
        if CLUSTERED_NW_FILES in existing_ip_dict.keys():
            res_vals = existing_ip_dict[CLUSTERED_NW_FILES].keys()

        elif CM_READY_FILES in existing_ip_dict.keys():
            res_vals = existing_ip_dict[CM_READY_FILES].keys()

        res_diff = set(res_vals).symmetric_difference(set(self.resolutions))

        if res_diff:
            message = f"The resolution values in the config file and json file " \
                      f"do not match. config file: {self.resolutions}, " \
                      f"json file: {list(res_vals)}"
            raise Exception(message)
        else:
            for res in res_vals:
                n_iters = existing_ip_dict[CLUSTERED_NW_FILES][res].keys()
                n_iter_diff = set(n_iters).symmetric_difference(
                    set(self.n_iterations)
                    )
                if n_iter_diff:
                    message = f"The number_of_iterations values in the config " \
                              f"file and json file " \
                              f"do not match for resolution {res}" \
                              f" config file: {self.n_iterations}," \
                              f" json file:  {list(n_iters)}"
                    raise Exception(message)

    def _create_output_dir_with_time_stamp(self):
        output_dir_name = f'{self.network_name}-cm-{self.cm_version}-pp-output-{self.timestamp}'
        output_dir = os.path.join(self.root_output_dir, output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
