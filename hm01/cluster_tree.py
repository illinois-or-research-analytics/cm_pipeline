from treeswift import Node
from typing import Optional

class ClusterTreeNode(Node):
    """ (VR) Object to represent a cluster in the mincut/recluster recursion tree 
    
    The root of the tree is the entire graph. When a a cluster is cut and reclustered into new clusters,
    the original cluster is a parent node to the children clusters.
    """
    extant: bool                            # Def Extant: The cluster has been untouched by CM (i.e. it hasn't been pruned or cut)
    graph_index: str
    num_nodes: int
    cut_size: Optional[int]
    validity_threshold: Optional[float]
    cm_valid: bool                          # Def CM Valid: The cluster need not be operated on by CM anymore (Note: Every extant cluster is also CM Valid)