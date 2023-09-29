from typing import Optional

from treeswift import Node


class ClusterTreeNode(Node):
    """ (VR) Object to represent a cluster in the mincut/recluster recursion tree 
    
    The root of the tree is the entire graph. When a a cluster is cut and reclustered into new clusters,
    the original cluster is a parent node to the children clusters.
    """
    extant: bool  # Def Extant: The cluster has been untouched by CM (i.e. it hasn't been pruned or cut)
    graph_index: str
    num_nodes: int
    begin: int  # initial node of this cluster.
    end: int  # one after the final node of this cluster
    cut_size: Optional[int]
    validity_threshold: Optional[float]
    cm_valid: bool  # Def CM Valid: The cluster need not be operated on by CM anymore (Note: Every extant cluster is also CM Valid)

    def __init__(
        self,
        graph_index,
        num_nodes,
        begin,
        end,
        cut_size,
        validity_threshold,
    ):
        super().__init__()
        self.label = graph_index
        self.graph_index = graph_index
        self.num_nodes = num_nodes
        self.begin = begin
        self.end = end
        self.cut_size = cut_size
        self.validity_threshold = validity_threshold
        self.cm_valid = True
        self.extant = False
