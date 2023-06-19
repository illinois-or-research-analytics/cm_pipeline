import atexit
from functools import cached_property
import glob
import shutil
from typing import Optional
import os
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Context:
    def __init__(self):
        # (VR) hm01 working dir to store intermediate files
        self._working_dir = "hm01_working_dir"
        self.transient = False

    def as_transient(self):
        self.transient = True
        return self

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
    
    def with_working_dir(self, working_dir):
        self._working_dir = working_dir
        return self
    
    @cached_property
    def working_dir(self):
        if not os.path.exists(self._working_dir):
            os.mkdir(self._working_dir)
        else:
            if self.transient:
                raise Exception("Working directory already exists under transient mode")
        if self.transient:
            atexit.register(lambda: shutil.rmtree(self._working_dir))
        return self._working_dir


# we export the context as a singleton
context = Context()