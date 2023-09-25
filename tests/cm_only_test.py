from run_cm import *


def test_clique1():
    test_dir = 'clique_dataset/'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_leiden(out_dict, 0.5, 2)

    assert count_nodes(final_tsv) == 9
    assert count_clusters(final_tsv) == 1


def test_disconnected1():
    test_dir = 'disconnected_dataset/'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_leiden(out_dict, 0.5, 2)

    assert count_nodes(final_tsv) == 9
    assert count_clusters(final_tsv) == 3
    assert get_cluster_sizes(final_tsv) == [3, 3, 3]


def test_disconnected2():
    test_dir = 'disconnected_dataset2/'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_leiden(out_dict, 0.5, 2)

    assert count_nodes(final_tsv) == 11
    assert count_clusters(final_tsv) == 3
    assert get_cluster_sizes(final_tsv) == [3, 3, 5]


def test_sun():
    test_dir = 'sun_dataset/'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_leiden(out_dict, 0.5, 2)

    assert count_nodes(final_tsv) == 9
    assert count_clusters(final_tsv) == 1


def test_tail():
    test_dir = 'tail_dataset/'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_leiden(out_dict, 0.5, 2)

    assert count_nodes(final_tsv) == 9
    assert count_clusters(final_tsv) == 1


def test_disconnected_ikc():
    test_dir = 'disconnected_dataset2_ikc/'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_ikc(out_dict, 10)

    assert count_nodes(final_tsv) == 11
    assert count_clusters(final_tsv) == 3
    assert get_cluster_sizes(final_tsv) == [3, 3, 5]

def test_multi_component():
    test_dir = 'multi_component_test'
    out_dict = run_cm(test_dir)
    final_tsv = get_final_tsv_ikc(out_dict, 10)

    assert count_nodes(final_tsv) == 12
    assert count_clusters(final_tsv) == 4
    assert get_cluster_sizes(final_tsv) == [3, 3, 3, 3]