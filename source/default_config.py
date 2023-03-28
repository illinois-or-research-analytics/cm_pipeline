import os
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
                self.output_dir, 'executin_time.csv')
        except KeyError:
            raise Exception(
                "default section with network name "
                "output directory/ algorithm /resolutions "
                "is missing / misspelled in the config file."
                )

    def _create_output_dir_with_time_stamp(self):
        output_dir_name = f'{self.network_name}-cm-{self.cm_version}-pp-output-{self.timestamp}'
        output_dir = os.path.join(self.root_output_dir, output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
