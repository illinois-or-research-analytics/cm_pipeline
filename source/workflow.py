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

        # Read the network name, output_dir from the config file.
        try:
            self.network_name = dict(config[DEFAULT])[NETWORK_NAME_KEY]
            self.output_dir = dict(config[DEFAULT])[OUTPUT_DIR_KEY]
        except KeyError:
            raise Exception("defualt section with network name, output directory is missing / misspelled in the config file.")
        

        # Note: maintain the order in which the sections are parsed
        if config.has_section(CLEANUP_SECTION):
            cleanup = Cleanup(config.items(CLEANUP_SECTION), self.network_name, self.output_dir)
            self.stages.append(cleanup)
        
        if config.has_section(CLUSTERING_SECTION):
            clustering = Clustering(config.items(CLUSTERING_SECTION), self.network_name, self.output_dir)
            self.stages.append(clustering)
        
        if config.has_section(FILTERING_SECTION):
            filtering = Filtering(config.items(FILTERING_SECTION), self.network_name, self.output_dir)
            self.stages.append(filtering)


    def run(self):
        hostlogger.info("Starting the CM Workflow..")
        for stage in self.stages:
            stage.execute() 
        hostlogger.info("Finished the CM Workflow")

