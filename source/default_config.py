from source.constants import *
class DefaultConfig(object):
    def __init__(self, default_section):
        try:
            self.network_name = default_section[NETWORK_NAME_KEY]
            self.output_dir = default_section[OUTPUT_DIR_KEY]
            self.algorithm = default_section[ALGORITHM_KEY]
            self.resolutions = [resolution.strip() for resolution in default_section[RESOLUTION_KEY].split(',')]
        except KeyError:
            raise Exception("default section with network name " 
                            "output directory/ algorithm /resolutions is missing / misspelled " 
                            "in the config file.")
        