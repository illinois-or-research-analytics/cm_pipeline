from source.cleanup import Cleanup
from source.clustering import Clustering
from source.constants import *
import logging

# Create a custom logger
hostlogger = logging.getLogger(__name__)

class Workflow:
    def __init__(self, config):

        self.stages = []
        
        # Note: maintain the order in which the sections are parsed
        if config.has_section(CLEANUP_SECTION):
            cleanup = Cleanup(config.items(CLEANUP_SECTION))
            self.stages.append(cleanup)
        
        if config.has_section(CLUSTERING_SECTION):
            clustering = Clustering(config.items(CLUSTERING_SECTION))
            self.stages.append(clustering)

    def run(self):
        hostlogger.info("Starting the CM Workflow..")
        for stage in self.stages:
            stage.execute() 
        hostlogger.info("Finished the CM Workflow")

