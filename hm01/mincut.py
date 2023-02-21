from dataclasses import dataclass
import coloredlogs, logging
from typing import List, Tuple, Union

# from hm01.graph import Graph, RealizedSubgraph

from context import context
import subprocess
import re
import os

logger = logging.getLogger(__name__)


@dataclass
class MincutResult:
    # FIXME: these are misnomers, "light_partition" is not guaranteed to have fewer nodes than "heavy_partition"
    light_partition: List[int]  # 0 labeled nodes
    heavy_partition: List[int]  # 1 labeled nodes
    cut_size: int


def viecut(graph):
    if graph.n() == 2 and graph.m() == 1:
        nodes = list(graph.nodes())
        return MincutResult([nodes[0]], [nodes[1]], 1)
    metis = graph.as_metis_filepath()
    cut_path = metis + ".cut"
    cut_result = run_viecut_command(metis, cut_path, hydrator=graph.hydrator)
    return cut_result


def run_viecut_command(metis_path, output_path, hydrator=None):
    """Run the viecut command and return the output path"""
    cmd = [context.viecut_path, "-b", "-s", "-o", output_path, metis_path, "cactus"]
    logger.debug(f"Running viecut command: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True)
    if "has multiple connected components" in res.stdout.decode("utf-8"):
        return MincutResult([], [], 0)
    labels = []
    if not os.path.exists(output_path):
        return MincutResult([], [], 0)
    with open(output_path, "r") as f:
        for l in f:
            labels.append(int(l))
    light_partition = []
    heavy_partition = []
    for i, l in enumerate(labels):
        if l == 0:
            light_partition.append(i)
        else:
            heavy_partition.append(i)
    lastline = res.stdout.splitlines()[-1]
    r_res = re.search(r"cut=(\d+)", lastline.decode("utf-8"))
    assert r_res, f"Could not find cut size in {lastline}"
    cut_size = int(r_res.group(1), 10)
    if hydrator:
        hydrated_light = [hydrator[i] for i in light_partition]
        hydrated_heavy = [hydrator[i] for i in heavy_partition]
        return MincutResult(hydrated_light, hydrated_heavy, cut_size)
    else:
        return MincutResult(light_partition, heavy_partition, cut_size)