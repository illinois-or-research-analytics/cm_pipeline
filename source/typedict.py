from source.cleanup import Cleanup
from source.connectivity_modifier import CM
from source.filtering import Filtering
from source.stats import Stats
from source.clustering import Clustering

from source.clusterers.ikc import IKCClustering
from source.clusterers.leiden import LeidenClustering
from source.clusterers.leiden_mod import LeidenModClustering


stage_classes = {
    'connectivity_modifier': CM,
    'stats': Stats,
    'filtering': Filtering,
    'cleanup': Cleanup,
    'clustering': Clustering
}

clusterer_classes = {
    'ikc': IKCClustering,
    'leiden': LeidenClustering,
    'leiden_mod': LeidenModClustering
}

def cast(stage, name):
    stage.__class__ = stage_classes[name]

def cast_clusterer(stage, algo):
    stage.__class__ = clusterer_classes[algo]