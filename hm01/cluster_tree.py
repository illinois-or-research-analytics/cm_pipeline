from treeswift import Node
from typing import Optional

class ClusterTreeNode(Node):
    """ Object to represent a cluster in the mincut/recluster recursion tree 
    
    The root of the tree is the entire graph. When a a cluster is cut and reclustered into new clusters,
    the original cluster is a parent node to the children clusters.
    """
    extant: bool
    graph_index: str
    num_nodes: int
    cut_size: Optional[int]
    validity_threshold: Optional[float]