from collections import OrderedDict
from source.default_config import DefaultConfig
from source.cleanup import Cleanup
from source.clustering import Clustering
from source.filtering_bf_cm import FilteringBfCm
from source.filtering_af_cm import FilteringAfCm
from source.connectivity_modifier import ConnectivityModifier
from source.timeit import timeit
from source.constants import *
import logging

# Create a custom logger
hostlogger = logging.getLogger(__name__)

class Workflow:
    def __init__(self, config):
        self.stages = OrderedDict()
        self.config = config

        # Read the default config.
        self.default_config = DefaultConfig(dict(config[DEFAULT]))

        stage_num = 0
        # Note: maintain the order in which the sections are parsed
        if config.has_section(CLEANUP_SECTION):
            stage_num = stage_num + 1
            self._add_stage(Cleanup, CLEANUP_SECTION, stage_num)
        
        if config.has_section(CLUSTERING_SECTION):
            stage_num = stage_num + 1
            self._add_stage(Clustering, CLUSTERING_SECTION, stage_num)
            
        if config.has_section(FILTERING_BF_CM_SECTION):
            stage_num = stage_num + 1
            self._add_stage(FilteringBfCm, FILTERING_BF_CM_SECTION, stage_num)
        
        if config.has_section(CONNECTIVITY_MODIFIER_SECTION):
            stage_num = stage_num + 1
            self._add_stage(ConnectivityModifier, CONNECTIVITY_MODIFIER_SECTION, stage_num)
        
        if config.has_section(FILTERING_AF_CM_SECTION):
            stage_num = stage_num + 1
            self._add_stage(FilteringAfCm, FILTERING_AF_CM_SECTION, stage_num)
            
    def _add_stage(self, StageClass, section_name, stage_num):
        stage_class_obj = StageClass(
                                config = self.config.items(section_name), 
                                default_config = self.default_config,
                                stage_num = stage_num,
                                prev_stages = self.stages  
                        )
        self.stages[section_name]=stage_class_obj

    @timeit
    def start(self):
        hostlogger.info("******** STARTED CM WORKFLOW ********")
        for stage in self.stages.values():
            stage.execute() 
        hostlogger.info("******** FINISHED CM WORKFLOW ********")

