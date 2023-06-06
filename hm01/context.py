import glob
from typing import Optional
import os
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Context:
    def __init__(self):
        # (VR) hm01 working dir to store intermediate files
        self._working_dir = "hm01_working_dir"

    @property
    def ikc_path(self):
        # (VR) path to IKC clusterer
        return "{project_root}/hm01/tools/ikc.py".format(project_root=PROJECT_ROOT)

    def request_graph_related_path(self, graph, suffix):
        """ (VR) Get filepath to write intermediate graphs to
        
        Parameters:
            graph (AbstractGraph)   : graph object to store
            suffix (str)            : format (ex. metis, edgelist)

        Returns:
            graph info filepath
        """
        return os.path.join(
            self.working_dir,
            hashlib.sha256(graph.index.encode("utf-8")).hexdigest()[:10] + "." + suffix,
        )

    def request_subpath(self, suffix) -> str:
        # (VR) (For Checkpointing) Get file in working directory
        return os.path.join(self.working_dir, suffix)

    def find_latest_checkpoint(self) -> Optional[str]:
        # (VR) (For Checkpointing) Get last checkpoint from CM run
        checkpoints = glob.glob(os.path.join(self.working_dir, "*.pkl"))
        if not checkpoints:
            return None
        return max(checkpoints, key=os.path.getctime)


# we export the context as a singleton
context = Context()