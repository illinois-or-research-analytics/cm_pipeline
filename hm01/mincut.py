import logging

from os import path, chdir

script_path = path.abspath(__file__)
dir_name = path.dirname(script_path)
chdir(dir_name)

from sys import path
path.append('tools/python-mincut/build')
path.append('tools/python-mincut/src')

from pygraph import PyGraph
from mincut_wrapper import MincutResult

logger = logging.getLogger(__name__)

def viecut(graph):
    if graph.n() == 2 and graph.m() == 1:
        nodes = list(graph.nodes())
        return MincutResult([nodes[0]], [nodes[1]], 1)
    pygraph = graph.as_pygraph()
    cut_result = run_viecut_command(pygraph)
    return cut_result


def run_viecut_command(pygraph, hydrator=None):
    """Run the viecut command and return the output path"""
    algorithm = 'noi'
    queue_implementation = 'bqueue'
    balanced = False

    light_partition, heavy_partition, cut_size = pygraph.mincut(algorithm, queue_implementation, balanced)

    if cut_size == 0:
        return MincutResult([], [], 0)

    return MincutResult(light_partition, heavy_partition, cut_size)