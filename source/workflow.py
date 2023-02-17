from source.cleanup import Cleanup
from source.clustering import Clustering
from source.filtering import Filtering
from source.constants import *
import logging

# Create a custom logger
hostlogger = logging.getLogger(__name__)

class Workflow:
    def __init__(self, config):

        self.stages = []
        self.config = config

        # Read the network name, output_dir from the config file.
        try:
            self.network_name = dict(config[DEFAULT])[NETWORK_NAME_KEY]
            self.output_dir = dict(config[DEFAULT])[OUTPUT_DIR_KEY]
        except KeyError:
            raise Exception("defualt section with network name, output directory is missing / misspelled in the config file.")
    
        stage_num = 0
        # Note: maintain the order in which the sections are parsed
        if config.has_section(CLEANUP_SECTION):
            stage_num = stage_num + 1
            self._add_stage(Cleanup, CLEANUP_SECTION, stage_num)
        
        if config.has_section(CLUSTERING_SECTION):
            stage_num = stage_num + 1
            self._add_stage(Clustering, CLUSTERING_SECTION, stage_num)
            
        if config.has_section(FILTERING_SECTION):
             stage_num = stage_num + 1
             self._add_stage(Filtering, FILTERING_SECTION, stage_num)
            
    def _add_stage(self, StageClass, section_name, stage_num):
        stage_class_obj = StageClass(
                                config = self.config.items(section_name), 
                                network_name = self.network_name, 
                                output_dir = self.output_dir,
                                stage_num = stage_num,
                                prev_stage = self.previous_stage()  
                        )
        self.stages.append(stage_class_obj)
    
    def previous_stage(self):
        if self.stages:
            return self.stages[-1]
        else:
            return None

    def run(self):
        hostlogger.info("Starting the CM Workflow..")
        for stage in self.stages:
            stage.execute() 
        hostlogger.info("Finished the CM Workflow")

