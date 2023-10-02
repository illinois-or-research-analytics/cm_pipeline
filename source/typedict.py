from source.cleanup import Cleanup
from source.connectivity_modifier import CM
from source.filtering import Filtering
from source.stats import Stats
from source.clustering import Clustering


stage_classes = {
    'connectivity_modifier': CM,
    'stats': Stats,
    'filtering': Filtering,
    'cleanup': Cleanup,
    'clustering': Clustering
}

def cast(stage, name):
    stage.__class__ = stage_classes[name]