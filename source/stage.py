import os
import time
import logging
from source.cmd import run

class Stage(object):
    def __init__(self, config):
        self.config = dict(config)

    def execute(self):
        
        raise NotImplementedError("Implement the execute function in each subclass")

    def generate_metrics_report(self):
        
        pass 