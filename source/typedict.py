from source.cleanup import Cleanup
from source.connectivity_modifier import CM
from source.filtering import Filtering
from source.stats import Stats


stage_classes = {
    'connectivity_nodifier': CM,
    'stats': Stats,
    'filtering': Filtering,
    'cleanup': Cleanup
}