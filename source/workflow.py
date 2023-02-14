from source.cleanup import Cleanup
from source.clustering import Clustering
import logging

# Create a custom logger
hostlogger = logging.getLogger(__name__)

class Workflow:
    def __init__(self, config):

        self.stages = []
        
        # Note: maintain the order in which the sections are parsed
        if config.has_section('cleanup'):
            cleanup = Cleanup(config.items('cleanup'))
            self.stages.append(cleanup)
        
        if config.has_section('clustering'):
            clustering = Clustering(config.items('clustering'))
            self.stages.append(clustering)

    def run(self):
        hostlogger.info("Starting the CM Workflow..")
        for stage in self.stages:
            stage.execute() 
        hostlogger.info("Finished the CM Workflow")

