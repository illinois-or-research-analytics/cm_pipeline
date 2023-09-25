from pathlib import Path

from hm01.graph import Graph, RealizedSubgraph, IntangibleSubgraph


def test_cgraph():
    graph_path = Path(
        Path(__file__).parent,
        'disconnected_dataset2_ikc',
        'network.tsv',
    )

    G = Graph.from_edgelist(str(graph_path))

    assert G.m() == 12
    assert G.n() == 11

    G = G.to_realized_subgraph()

    assert G.m() == 12
    assert G.n() == 11

    mc = G.find_mincut()

    assert mc[-1] == 0

    light, heavy = mc[:-1]
    light = RealizedSubgraph(IntangibleSubgraph(light, 'a'), G)
    heavy = RealizedSubgraph(IntangibleSubgraph(heavy, 'b'), G)

    assert light.m() == 3
    assert light.n() == 3
    assert heavy.m() == 9
    assert heavy.n() == 8
