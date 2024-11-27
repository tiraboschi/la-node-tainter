import pytest
from la_taint_nodes import get_max_hard_taints, get_max_soft_taints


@pytest.mark.parametrize(
    "wnode_num,expected",
    [
        (1, 0),
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 2),
        (6, 3)
    ]
)
def test_get_max_hard_taints(wnode_num, expected):
    assert get_max_hard_taints(wnode_num) == expected


@pytest.mark.parametrize(
    "wnode_num,hard_taints,expected",
    [
        (1, 0, 0),
        (2, 0, 1),
        (2, 1, 0),
        (3, 0, 1),
        (3, 1, 0),
        (4, 0, 2),
        (4, 1, 1),
        (4, 2, 0),
        (5, 0, 2),
        (5, 1, 1),
        (5, 2, 0),
        (6, 0, 3),
        (6, 1, 2),
        (6, 2, 1),
        (6, 3, 0),
    ]
)
def test_get_max_soft_taints(wnode_num, hard_taints, expected):
    assert hard_taints <= get_max_hard_taints(wnode_num)
    assert get_max_soft_taints(wnode_num, hard_taints) == expected
